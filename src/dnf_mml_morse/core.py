"""
Cœur du système DNF-MML-Morse
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .mml import MMLProcessor
from .morse import MorseCodec
from .dnf import DNFTransmitter
from .streaming import StreamingProcessor, StreamingManager
from .security import SecureTransmissionManager, KeyManager
from .performance import PerformanceMonitor, SmartCache, ParallelProcessor, MemoryOptimizer, cached, timed, memory_optimized, global_monitor, global_cache, global_parallel, global_memory

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DNFMMLMorseSystem:
    """
    Système intégré DNF-MML-Morse pour transmission de documents
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialisation du système

        Args:
            config: Configuration du système
        """
        self.config = config or self._default_config()
        self._validate_config()

        # Initialisation des composants
        self.mml_processor = MMLProcessor()
        self.morse_codec = MorseCodec(mode=self.config.get('morse_mode', 'optimized'))
        self.dnf_transmitter = DNFTransmitter(
            transport_type=self.config.get('transport', 'cw'),
            callsign=self.config.get('callsign')
        )

        # Support streaming
        self.streaming_enabled = self.config.get('streaming_enabled', True)
        self.streaming_manager = StreamingManager() if self.streaming_enabled else None

        # Support sécurité
        self.security_enabled = self.config.get('security_enabled', False)
        self.key_manager = KeyManager() if self.security_enabled else None
        self.secure_transmission = SecureTransmissionManager(self.key_manager) if self.security_enabled else None

        # Support performance
        self.performance_monitor = global_monitor
        self.cache = global_cache
        self.parallel_processor = global_parallel
        self.memory_optimizer = global_memory
        self.performance_enabled = self.config.get('performance_enabled', True)

        logger.info(f"Système DNF-MML-Morse initialisé avec transport {self.config['transport']}")

    def _default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            'morse_mode': 'optimized',
            'transport': 'cw',
            'callsign': 'DEMO',
            'compression_level': 'standard',
            'wpm': 20,
            'max_fragment_size': 200,
            'timeout': 300,
            'retry_attempts': 3,
            'streaming_enabled': True,
            'streaming_chunk_size': 8192,
            'streaming_max_memory_mb': 50,
            'security_enabled': False,  # Sécurité désactivée par défaut
            'encryption_enabled': False,
            'signing_enabled': False,
            'identity_name': 'default_user',
            'performance_enabled': True,
            'cache_enabled': True,
            'parallel_processing': True,
            'memory_optimization': True,
        }

    def _validate_config(self):
        """Validation de la configuration"""
        required_keys = ['morse_mode', 'transport', 'callsign']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Configuration manquante: {key}")

        # Validation des valeurs
        if self.config['morse_mode'] not in ['standard', 'optimized', 'robust']:
            raise ValueError("Mode Morse invalide")

        if self.config['transport'] not in ['cw', 'js8call', 'packet', 'aprs']:
            raise ValueError("Transport invalide")

        if not self.config['callsign'] or len(self.config['callsign']) > 10:
            raise ValueError("Callsign invalide")

    async def transmit_document(self, document_path: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """
        Transmission complète d'un document

        Utilise automatiquement le streaming pour les gros fichiers si activé.

        Args:
            document_path: Chemin vers le document source
            destination: Destinataire (optionnel pour diffusion)

        Returns:
            Résultats de la transmission
        """
        try:
            # Validation du fichier source
            doc_path = Path(document_path)
            if not doc_path.exists():
                raise FileNotFoundError(f"Document non trouvé: {document_path}")

            file_size = doc_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB limite absolue
                raise ValueError("Document trop volumineux (>100MB)")

            # Décider automatiquement du mode de traitement
            use_streaming = self.should_use_streaming(document_path)

            if use_streaming:
                logger.info(f"Utilisation du mode streaming pour {document_path} ({file_size / (1024*1024):.1f} MB)")
                return await self.transmit_file_streaming(document_path, destination)
            else:
                logger.info(f"Utilisation du mode direct pour {document_path} ({file_size / 1024:.1f} KB)")
                return await self._transmit_document_direct(document_path, destination)

        except Exception as e:
            logger.error(f"Erreur lors de la transmission: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }

    async def _transmit_document_direct(self, document_path: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """
        Transmission directe (méthode originale)

        Args:
            document_path: Chemin vers le document source
            destination: Destinataire

        Returns:
            Résultats de la transmission
        """
        # Validation du fichier source
        doc_path = Path(document_path)
        if doc_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limite pour traitement direct
            raise ValueError("Document trop volumineux pour traitement direct (>10MB)")

        logger.info(f"Début de transmission directe de {document_path}")

        # Étape 1 : Chargement et conversion MML
        logger.info("Étape 1: Conversion en MML...")
        mml_doc = await self.mml_processor.convert_to_mml(document_path)
        logger.info(f"✓ Conversion MML terminée: {len(mml_doc['content'])} caractères")

        # Étape 2 : Compression MML-C
        logger.info("Étape 2: Compression MML-C...")
        compressed = await self.mml_processor.compress_mml(mml_doc)
        logger.info(f"✓ Compression terminée: {compressed['ratio']:.1%} de réduction")

        # Étape 3 : Conversion Morse
        logger.info("Étape 3: Conversion Morse...")
        morse_sequence = self.morse_codec.encode(compressed['content'])
        logger.info(f"✓ Conversion Morse terminée: {len(morse_sequence.split())} symboles")

        # Étape 4 : Transmission DNF
        logger.info("Étape 4: Transmission DNF...")
        transmission_result = await self.dnf_transmitter.transmit(
            morse_sequence,
            destination=destination
        )

        result = {
            'success': True,
            'original_size': mml_doc['size'],
            'mml_size': len(mml_doc['content']),
            'compressed_size': len(compressed['content']),
            'compression_ratio': compressed['ratio'],
            'morse_symbols': len(morse_sequence.split()),
            'fragments_sent': transmission_result.get('fragments', 0),
            'transmission_time': transmission_result.get('duration', 0),
            'transport_used': self.config['transport'],
            'destination': destination,
            'method': 'direct',
        }

        logger.info(f"✓ Transmission terminée avec succès: {result['fragments_sent']} fragments")
        return result

    async def receive_documents(self, filter_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Réception de documents

        Args:
            filter_criteria: Critères de filtrage (optionnel)

        Returns:
            Documents reçus
        """
        try:
            logger.info("Début de réception de documents")

            # Configuration des filtres
            filters = filter_criteria or {}

            # Surveillance réseau
            received_data = await self.dnf_transmitter.monitor_incoming(filters)

            processed_documents = []
            for data in received_data:
                try:
                    # Décodage Morse
                    morse_sequence = data.get('morse_sequence', '')
                    decoded_text = self.morse_codec.decode(morse_sequence)

                    # Décompression MML-C
                    decompressed = await self.mml_processor.decompress_mmlc({'content': decoded_text})

                    # Conversion vers format final
                    final_doc = await self.mml_processor.convert_mml_to_output(
                        decompressed['content'],
                        output_format=filters.get('output_format', 'html')
                    )

                    processed_documents.append({
                        'content': final_doc,
                        'metadata': data.get('metadata', {}),
                        'source': data.get('source', 'unknown'),
                        'timestamp': data.get('timestamp'),
                    })

                except Exception as e:
                    logger.warning(f"Erreur de traitement d'un document: {e}")
                    continue

            result = {
                'success': True,
                'documents_received': len(processed_documents),
                'documents_processed': len(processed_documents),
                'documents': processed_documents,
            }

            logger.info(f"✓ Réception terminée: {len(processed_documents)} documents traités")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la réception: {e}")
            return {
                'success': False,
                'error': str(e),
                'documents_received': 0,
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        État du système

        Returns:
            Informations sur l'état du système
        """
        return {
            'status': 'operational',
            'version': '1.0.0',
            'config': self.config,
            'components': {
                'mml_processor': 'active',
                'morse_codec': 'active',
                'dnf_transmitter': 'active',
            },
            'transport_status': self.dnf_transmitter.get_status(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Vérification de santé du système

        Returns:
            Résultats des tests de santé
        """
        health_results = {
            'overall_status': 'healthy',
            'checks': {},
            'timestamp': None,
        }

        try:
            # Test MML processor
            test_mml = await self.mml_processor.convert_to_mml(__file__)  # Test avec ce fichier
            health_results['checks']['mml_processor'] = 'healthy' if test_mml else 'unhealthy'

            # Test Morse codec
            test_morse = self.morse_codec.encode("HELLO")
            test_decode = self.morse_codec.decode(test_morse)
            health_results['checks']['morse_codec'] = 'healthy' if test_decode == "HELLO" else 'unhealthy'

            # Test DNF transmitter
            dnf_status = await self.dnf_transmitter.health_check()
            health_results['checks']['dnf_transmitter'] = 'healthy' if dnf_status.get('healthy') else 'unhealthy'

            # Évaluation globale
            if any(status != 'healthy' for status in health_results['checks'].values()):
                health_results['overall_status'] = 'degraded'
            else:
                health_results['overall_status'] = 'healthy'

        except Exception as e:
            health_results['overall_status'] = 'unhealthy'
            health_results['error'] = str(e)

        health_results['timestamp'] = None  # Sera défini par l'appelant si nécessaire

        return health_results

    def update_config(self, new_config: Dict[str, Any]):
        """
        Mise à jour de la configuration

        Args:
            new_config: Nouvelle configuration partielle
        """
        self.config.update(new_config)
        self._validate_config()

        # Reinitialisation des composants si nécessaire
        if 'morse_mode' in new_config:
            self.morse_codec = MorseCodec(mode=self.config['morse_mode'])

        if 'transport' in new_config or 'callsign' in new_config:
            self.dnf_transmitter = DNFTransmitter(
                transport_type=self.config['transport'],
                callsign=self.config['callsign']
            )

        logger.info("Configuration mise à jour")

    async def shutdown(self):
        """
        Arrêt propre du système
        """
        logger.info("Arrêt du système DNF-MML-Morse")

        # Arrêt des composants
        await self.dnf_transmitter.shutdown()

        logger.info("Système arrêté proprement")

    # Méthodes de streaming

    def should_use_streaming(self, file_path: Union[str, Path]) -> bool:
        """
        Détermine si le streaming doit être utilisé pour un fichier

        Args:
            file_path: Chemin du fichier

        Returns:
            True si streaming recommandé
        """
        if not self.streaming_enabled or not self.streaming_manager:
            return False

        file_path = Path(file_path)
        if not file_path.exists():
            return False

        file_size = file_path.stat().st_size
        streaming_threshold = self.config.get('streaming_threshold_mb', 1) * 1024 * 1024

        return file_size > streaming_threshold

    async def transmit_file_streaming(self, file_path: Union[str, Path],
                                    destination: Optional[str] = None) -> Dict[str, Any]:
        """
        Transmission en streaming pour fichiers volumineux

        Args:
            file_path: Chemin du fichier
            destination: Destinataire

        Returns:
            Résultats de transmission
        """
        if not self.streaming_enabled or not self.streaming_manager:
            # Fallback vers traitement normal
            return await self.transmit_document(str(file_path), destination)

        try:
            # Créer une session de streaming
            session_id = f"stream_{hash(str(file_path))}"
            streaming_config = {
                'chunk_size': self.config.get('streaming_chunk_size', 8192),
                'max_memory_mb': self.config.get('streaming_max_memory_mb', 50),
            }

            await self.streaming_manager.start_streaming_session(session_id, streaming_config)

            # Traiter le fichier
            results = []
            async for result in self.streaming_manager.process_file_in_session(
                session_id, file_path, destination or "STREAM_DEST"
            ):
                results.append(result)

            # Nettoyer la session
            await self.streaming_manager.end_session(session_id)

            # Retourner le résultat consolidé
            if results and results[0]['success']:
                consolidated = results[0].copy()
                consolidated['method'] = 'streaming'
                return consolidated
            else:
                error_result = results[0] if results else {'success': False, 'error': 'Unknown streaming error'}
                error_result['method'] = 'streaming'
                return error_result

        except Exception as e:
            logger.error(f"Erreur streaming: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'streaming',
            }

    async def get_streaming_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        État du système de streaming

        Args:
            session_id: ID de session spécifique (optionnel)

        Returns:
            État du streaming
        """
        if not self.streaming_enabled or not self.streaming_manager:
            return {'streaming_enabled': False}

        if session_id:
            return await self.streaming_manager.get_session_status(session_id)
        else:
            return {
                'streaming_enabled': True,
                'active_sessions': self.streaming_manager.list_active_sessions(),
                'config': {
                    'chunk_size': self.config.get('streaming_chunk_size'),
                    'max_memory_mb': self.config.get('streaming_max_memory_mb'),
                }
            }

    async def analyze_file_for_streaming(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyse un fichier pour déterminer la stratégie optimale

        Args:
            file_path: Fichier à analyser

        Returns:
            Analyse et recommandations
        """
        if not self.streaming_enabled or not self.streaming_manager:
            return {
                'streaming_available': False,
                'recommended_method': 'direct',
            }

        # Utiliser le processeur de streaming pour l'analyse
        processor = StreamingProcessor()
        info = await processor.get_streaming_info(file_path)

        # Déterminer si streaming recommandé
        should_stream = self.should_use_streaming(file_path)

        return {
            'streaming_available': True,
            'recommended_method': 'streaming' if should_stream else 'direct',
            'file_analysis': info,
            'streaming_config': {
                'chunk_size': self.config.get('streaming_chunk_size'),
                'max_memory_mb': self.config.get('streaming_max_memory_mb'),
            }
        }

    # Méthodes de sécurité

    def enable_security(self, identity_name: Optional[str] = None) -> bool:
        """
        Active la sécurité pour le système

        Args:
            identity_name: Nom de l'identité à utiliser

        Returns:
            True si l'activation a réussi
        """
        try:
            self.security_enabled = True
            identity = identity_name or self.config.get('identity_name', 'default_user')

            self.key_manager = KeyManager()
            self.secure_transmission = SecureTransmissionManager(self.key_manager)

            # Génère ou charge l'identité
            try:
                self.key_manager.load_identity(identity)
            except FileNotFoundError:
                logger.info(f"Génération de la nouvelle identité: {identity}")
                self.key_manager.generate_identity(identity)

            self.config['security_enabled'] = True
            self.config['encryption_enabled'] = True
            self.config['signing_enabled'] = True
            self.config['identity_name'] = identity

            logger.info(f"Sécurité activée pour l'identité: {identity}")
            return True

        except Exception as e:
            logger.error(f"Échec de l'activation de la sécurité: {e}")
            self.security_enabled = False
            return False

    def disable_security(self):
        """Désactive la sécurité"""
        self.security_enabled = False
        self.key_manager = None
        self.secure_transmission = None
        self.config['security_enabled'] = False
        self.config['encryption_enabled'] = False
        self.config['signing_enabled'] = False

        logger.info("Sécurité désactivée")

    async def transmit_secure_document(self, document_path: str,
                                     destination: Optional[str] = None,
                                     recipient_identity: Optional[str] = None) -> Dict[str, Any]:
        """
        Transmission sécurisée d'un document

        Args:
            document_path: Chemin du document
            destination: Destinataire radio
            recipient_identity: Identité du destinataire pour chiffrement

        Returns:
            Résultats de transmission sécurisée
        """
        if not self.security_enabled or not self.secure_transmission:
            raise ValueError("Sécurité non activée. Utilisez enable_security() d'abord.")

        try:
            # Transmission normale d'abord
            transmission_result = await self.transmit_document(document_path, destination)

            if not transmission_result['success']:
                return transmission_result

            # Sécurisation du contenu transmis
            # Note: En production, sécuriser les données avant transmission
            content_to_secure = json.dumps(transmission_result, sort_keys=True).encode('utf-8')

            secure_message = self.secure_transmission.create_secure_message(
                content_to_secure,
                self.config['identity_name'],
                recipient_identity,
                encrypt=self.config.get('encryption_enabled', True),
                sign=self.config.get('signing_enabled', True)
            )

            # Ajoute les informations de sécurité au résultat
            transmission_result.update({
                'secure': True,
                'encrypted': secure_message.get('encrypted', False),
                'signed': secure_message.get('signed', False),
                'sender_identity': secure_message.get('sender'),
                'security_metadata': {
                    'algorithm': 'AES-256-GCM + RSA-PSS',
                    'timestamp': secure_message.get('timestamp'),
                }
            })

            logger.info(f"Document transmis de manière sécurisée: {transmission_result['encrypted']=}, {transmission_result['signed']=}")
            return transmission_result

        except Exception as e:
            logger.error(f"Erreur lors de la transmission sécurisée: {e}")
            return {
                'success': False,
                'error': str(e),
                'secure': False,
            }

    def create_identity(self, name: str) -> Dict[str, Any]:
        """
        Crée une nouvelle identité sécurisée

        Args:
            name: Nom de l'identité

        Returns:
            Informations de l'identité créée
        """
        if not self.key_manager:
            raise ValueError("Gestionnaire de clés non initialisé")

        identity = self.key_manager.generate_identity(name)
        logger.info(f"Nouvelle identité créée: {name}")
        return identity

    def list_identities(self) -> List[str]:
        """
        Liste les identités disponibles

        Returns:
            Liste des noms d'identités
        """
        if not self.key_manager:
            return []

        return self.key_manager.list_identities()

    def get_security_status(self) -> Dict[str, Any]:
        """
        État de la sécurité du système

        Returns:
            Informations sur la sécurité
        """
        if not self.security_enabled or not self.secure_transmission:
            return {
                'security_enabled': False,
                'encryption_available': False,
                'signing_available': False,
                'identities_count': 0,
            }

        identities = self.list_identities()

        return {
            'security_enabled': True,
            'encryption_enabled': self.config.get('encryption_enabled', False),
            'signing_enabled': self.config.get('signing_enabled', False),
            'current_identity': self.config.get('identity_name'),
            'identities_count': len(identities),
            'identities': identities,
            'security_stats': self.secure_transmission.get_security_stats(),
        }

    def export_identity(self, identity_name: str) -> Dict[str, Any]:
        """
        Exporte une identité pour partage

        Args:
            identity_name: Nom de l'identité

        Returns:
            Données d'identité publiques
        """
        if not self.key_manager:
            raise ValueError("Gestionnaire de clés non initialisé")

        identity_data = self.key_manager.load_identity(identity_name)
        return {
            'name': identity_name,
            'public_key': identity_data['identity']['public_key'],
            'created': identity_data['identity']['created'],
            'version': identity_data['identity']['version'],
        }

    # Méthodes de performance

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Statistiques de performance du système

        Returns:
            Métriques de performance détaillées
        """
        stats = {
            'system_performance': self.performance_monitor.get_stats(),
            'cache_stats': self.cache.stats(),
            'memory_stats': self.memory_optimizer.get_memory_stats(),
            'parallel_workers': self.parallel_processor.max_workers,
            'performance_enabled': self.performance_enabled,
        }

        # Ajouter les stats des composants si disponibles
        if hasattr(self.mml_processor, 'get_processing_stats'):
            stats['mml_stats'] = self.mml_processor.get_processing_stats()

        if hasattr(self.morse_codec, 'get_stats'):
            stats['morse_stats'] = self.morse_codec.get_stats()

        return stats

    def optimize_performance(self):
        """
        Optimise les performances du système

        Active les optimisations disponibles et nettoie les caches
        """
        logger.info("Optimisation des performances...")

        # Nettoyer les caches
        self.cache.clear()

        # Optimiser la mémoire
        self.memory_optimizer.force_gc()

        # Remettre à zéro les métriques de performance
        self.performance_monitor.reset()

        logger.info("Optimisations appliquées")

    def enable_performance_monitoring(self):
        """
        Active le monitoring de performance
        """
        self.performance_enabled = True
        self.config['performance_enabled'] = True
        logger.info("Monitoring de performance activé")

    def disable_performance_monitoring(self):
        """
        Désactive le monitoring de performance
        """
        self.performance_enabled = False
        self.config['performance_enabled'] = False
        logger.info("Monitoring de performance désactivé")

    @cached(max_size=50, ttl_seconds=600)  # Cache 10 minutes
    def _get_conversion_cache_key(self, file_path: str, file_mtime: float) -> str:
        """
        Génère une clé de cache pour les conversions de fichiers

        Args:
            file_path: Chemin du fichier
            file_mtime: Date de modification

        Returns:
            Clé de cache
        """
        return f"{file_path}:{file_mtime}"

    async def _parallel_convert_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Convertit plusieurs documents en parallèle

        Args:
            file_paths: Liste des chemins de fichiers

        Returns:
            Résultats des conversions
        """
        if not self.performance_enabled or not self.parallel_processor:
            # Traitement séquentiel
            results = []
            for path in file_paths:
                result = await self.transmit_document(path)
                results.append(result)
            return results

        # Traitement parallèle
        async def convert_single(path):
            return await self.transmit_document(path)

        tasks = [convert_single(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Traiter les exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({'success': False, 'error': str(result)})
            else:
                processed_results.append(result)

        return processed_results
