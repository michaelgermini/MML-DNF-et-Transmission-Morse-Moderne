"""
Streaming pour DNF-MML-Morse

Permet le traitement de documents volumineux en mode streaming,
sans charger tout le contenu en mémoire.
"""

import asyncio
import aiofiles
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional, Union, BinaryIO
from contextlib import asynccontextmanager
import logging

from .mml import MMLProcessor
from .morse import MorseCodec
from .dnf import DNFTransmitter

logger = logging.getLogger(__name__)


class StreamingProcessor:
    """
    Processeur en streaming pour documents volumineux

    Traite les fichiers par chunks pour éviter la surcharge mémoire,
    tout en maintenant la cohérence du traitement MML.
    """

    def __init__(self, chunk_size: int = 8192, max_memory_mb: int = 50):
        """
        Initialisation du processeur streaming

        Args:
            chunk_size: Taille des chunks en octets
            max_memory_mb: Mémoire maximale autorisée en MB
        """
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

        # Processeurs pour chaque étape
        self.mml_processor = MMLProcessor()
        self.morse_codec = MorseCodec()
        self.dnf_transmitter = DNFTransmitter()

        # Statistiques
        self.stats = {
            'chunks_processed': 0,
            'bytes_processed': 0,
            'mml_chunks': 0,
            'morse_chunks': 0,
            'transmission_packets': 0,
            'processing_time': 0,
            'memory_peak': 0,
        }

    @asynccontextmanager
    async def process_file_streaming(self, file_path: Union[str, Path],
                                   destination: str,
                                   buffer_size: int = 3):
        """
        Traite un fichier en streaming de bout en bout

        Args:
            file_path: Chemin du fichier source
            destination: Destinataire
            buffer_size: Nombre de chunks en buffer
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

        # Vérification de la taille du fichier
        file_size = file_path.stat().st_size
        if file_size > self.max_memory_bytes:
            logger.warning(f"Fichier volumineux: {file_size / (1024*1024):.1f} MB")

        start_time = asyncio.get_event_loop().time()

        try:
            # Pipeline de streaming
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                # Étape 1: Lecture et conversion MML en streaming
                mml_stream = self._stream_html_to_mml(f)

                # Étape 2: Compression MML-C en streaming
                compressed_stream = self._stream_compress_mml(mml_stream, buffer_size)

                # Étape 3: Conversion Morse en streaming
                morse_stream = self._stream_to_morse(compressed_stream)

                # Étape 4: Transmission en streaming
                transmission_results = []
                async for morse_chunk in morse_stream:
                    result = await self.dnf_transmitter.transmit(morse_chunk, destination)
                    transmission_results.append(result)
                    self.stats['transmission_packets'] += 1

            # Mise à jour des statistiques
            end_time = asyncio.get_event_loop().time()
            self.stats['processing_time'] = end_time - start_time

            yield {
                'success': True,
                'file_size': file_size,
                'chunks_processed': self.stats['chunks_processed'],
                'transmission_results': transmission_results,
                'stats': self.stats.copy(),
            }

        except Exception as e:
            logger.error(f"Erreur streaming: {e}")
            yield {
                'success': False,
                'error': str(e),
                'file_path': str(file_path),
                'stats': self.stats.copy(),
            }

    async def _stream_html_to_mml(self, file_handle) -> AsyncGenerator[str, None]:
        """
        Convertit HTML vers MML en streaming

        Args:
            file_handle: Handle de fichier ouvert

        Yields:
            Chunks MML
        """
        buffer = ""
        in_tag = False
        tag_depth = 0

        async for line in file_handle:
            buffer += line
            self.stats['bytes_processed'] += len(line)

            # Traitement par lignes pour éviter la surcharge
            while len(buffer) > self.chunk_size:
                # Trouver un point de coupure sûr (fin de balise)
                cutoff = self._find_safe_cutoff(buffer, self.chunk_size)

                chunk = buffer[:cutoff]
                buffer = buffer[cutoff:]

                # Convertir le chunk en MML
                if chunk.strip():
                    mml_chunk = self._convert_html_chunk_to_mml(chunk)
                    if mml_chunk:
                        yield mml_chunk
                        self.stats['mml_chunks'] += 1

        # Traiter le reste du buffer
        if buffer.strip():
            mml_chunk = self._convert_html_chunk_to_mml(buffer)
            if mml_chunk:
                yield mml_chunk
                self.stats['mml_chunks'] += 1

    def _find_safe_cutoff(self, text: str, max_length: int) -> int:
        """
        Trouve un point de coupure sûr dans le texte

        Args:
            text: Texte à couper
            max_length: Longueur maximale

        Returns:
            Position de coupure
        """
        if len(text) <= max_length:
            return len(text)

        # Chercher la dernière fin de balise avant max_length
        cutoff = max_length

        # Chercher en arrière pour trouver une fin de balise
        for i in range(min(max_length, len(text) - 1), 0, -1):
            if text[i] == '>' and (i == 0 or text[i-1] != '\\'):  # > non échappé
                cutoff = i + 1
                break
            elif text[i] in '\n\r':  # Fin de ligne
                cutoff = i
                break

        return cutoff

    def _convert_html_chunk_to_mml(self, html_chunk: str) -> str:
        """
        Convertit un chunk HTML en MML

        Args:
            html_chunk: Chunk HTML

        Returns:
            Chunk MML
        """
        # Utiliser le parser MML existant pour les chunks
        try:
            # Créer un faux document HTML pour le chunk
            fake_html = f"<div>{html_chunk}</div>"

            # Parser et extraire le contenu MML
            result = self.mml_processor.convert_to_mml(fake_html)

            # Nettoyer les balises wrapper ajoutées
            mml_content = result['content']
            if mml_content.startswith('<D>'):
                mml_content = mml_content[3:]  # Enlever <D>
            if mml_content.endswith('</D>'):
                mml_content = mml_content[:-4]  # Enlever </D>

            return mml_content

        except Exception as e:
            logger.warning(f"Erreur conversion chunk HTML->MML: {e}")
            return html_chunk  # Fallback: retourner tel quel

    async def _stream_compress_mml(self, mml_stream: AsyncGenerator[str, None],
                                 buffer_size: int) -> AsyncGenerator[str, None]:
        """
        Compresse MML en streaming

        Args:
            mml_stream: Stream MML
            buffer_size: Taille du buffer

        Yields:
            Chunks MML-C compressés
        """
        buffer = []

        async for mml_chunk in mml_stream:
            buffer.append(mml_chunk)

            # Traiter quand le buffer est plein
            if len(buffer) >= buffer_size:
                combined_chunk = ''.join(buffer)
                compressed = self.mml_processor.compress_mml({'content': combined_chunk})

                if compressed['content']:
                    yield compressed['content']

                buffer = []

        # Traiter le reste du buffer
        if buffer:
            combined_chunk = ''.join(buffer)
            compressed = self.mml_processor.compress_mml({'content': combined_chunk})

            if compressed['content']:
                yield compressed['content']

    async def _stream_to_morse(self, compressed_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        Convertit en Morse en streaming

        Args:
            compressed_stream: Stream MML-C

        Yields:
            Chunks Morse
        """
        async for compressed_chunk in compressed_stream:
            morse_chunk = self.morse_codec.encode(compressed_chunk, add_prosigns=False)

            if morse_chunk:
                yield morse_chunk
                self.stats['morse_chunks'] += 1

    async def get_streaming_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyse un fichier pour déterminer la stratégie de streaming optimale

        Args:
            file_path: Chemin du fichier

        Returns:
            Informations de streaming
        """
        file_path = Path(file_path)
        file_size = file_path.stat().st_size

        # Estimation du nombre de chunks
        estimated_chunks = max(1, file_size // self.chunk_size)

        # Estimation de la mémoire nécessaire
        memory_estimate = min(file_size, self.max_memory_bytes)

        return {
            'file_size': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'estimated_chunks': estimated_chunks,
            'chunk_size': self.chunk_size,
            'memory_estimate_mb': memory_estimate / (1024 * 1024),
            'streaming_recommended': file_size > self.max_memory_bytes * 0.1,  # > 10% de la limite
            'processing_strategy': 'streaming' if estimated_chunks > 1 else 'direct',
        }

    def set_chunk_size(self, size: int):
        """
        Modifie la taille des chunks

        Args:
            size: Nouvelle taille en octets
        """
        if size < 1024:
            raise ValueError("Taille de chunk minimale: 1024 octets")
        if size > self.max_memory_bytes // 4:
            raise ValueError("Taille de chunk trop grande")

        self.chunk_size = size
        logger.info(f"Taille de chunk modifiée: {size} octets")

    def get_stats(self) -> Dict[str, Any]:
        """
        Statistiques de streaming

        Returns:
            Statistiques détaillées
        """
        return {
            'streaming_enabled': True,
            'chunk_size': self.chunk_size,
            'max_memory_mb': self.max_memory_mb,
            'stats': self.stats.copy(),
            'performance': {
                'bytes_per_second': self.stats['bytes_processed'] / max(self.stats['processing_time'], 0.001),
                'chunks_per_second': self.stats['chunks_processed'] / max(self.stats['processing_time'], 0.001),
            } if self.stats['processing_time'] > 0 else {},
        }


class StreamingManager:
    """
    Gestionnaire de streaming pour l'ensemble du système

    Coordonne le streaming entre tous les composants.
    """

    def __init__(self):
        self.streaming_processor = StreamingProcessor()
        self.active_streams = {}

    async def start_streaming_session(self, session_id: str, config: Dict[str, Any]) -> str:
        """
        Démarre une session de streaming

        Args:
            session_id: Identifiant de session
            config: Configuration de streaming

        Returns:
            ID de session
        """
        # Créer un nouveau processeur avec la config
        processor = StreamingProcessor(
            chunk_size=config.get('chunk_size', 8192),
            max_memory_mb=config.get('max_memory_mb', 50)
        )

        self.active_streams[session_id] = {
            'processor': processor,
            'config': config,
            'start_time': asyncio.get_event_loop().time(),
            'status': 'active',
        }

        logger.info(f"Session streaming démarrée: {session_id}")
        return session_id

    async def process_file_in_session(self, session_id: str,
                                    file_path: Union[str, Path],
                                    destination: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Traite un fichier dans une session de streaming

        Args:
            session_id: ID de session
            file_path: Fichier à traiter
            destination: Destinataire

        Yields:
            Résultats de traitement par chunks
        """
        if session_id not in self.active_streams:
            raise ValueError(f"Session inconnue: {session_id}")

        session = self.active_streams[session_id]
        processor = session['processor']

        async with processor.process_file_streaming(file_path, destination) as result:
            yield result

        # Marquer la session comme terminée
        session['status'] = 'completed'
        session['end_time'] = asyncio.get_event_loop().time()

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        État d'une session de streaming

        Args:
            session_id: ID de session

        Returns:
            État de la session
        """
        if session_id not in self.active_streams:
            return {'status': 'not_found'}

        session = self.active_streams[session_id]
        processor = session['processor']

        return {
            'session_id': session_id,
            'status': session['status'],
            'start_time': session['start_time'],
            'config': session['config'],
            'stats': processor.get_stats(),
            'duration': (session.get('end_time', asyncio.get_event_loop().time()) - session['start_time']),
        }

    async def end_session(self, session_id: str):
        """
        Termine une session de streaming

        Args:
            session_id: ID de session
        """
        if session_id in self.active_streams:
            self.active_streams[session_id]['status'] = 'terminated'
            logger.info(f"Session streaming terminée: {session_id}")

    def list_active_sessions(self) -> List[str]:
        """
        Liste des sessions actives

        Returns:
            Liste des IDs de sessions actives
        """
        return [sid for sid, session in self.active_streams.items()
                if session['status'] == 'active']


# Fonctions utilitaires
async def stream_file_processing(file_path: Union[str, Path],
                               destination: str,
                               chunk_size: int = 8192) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Fonction utilitaire pour traitement de fichier en streaming

    Args:
        file_path: Fichier à traiter
        destination: Destinataire
        chunk_size: Taille des chunks

    Yields:
        Résultats de traitement
    """
    processor = StreamingProcessor(chunk_size=chunk_size)

    async with processor.process_file_streaming(file_path, destination) as result:
        yield result
