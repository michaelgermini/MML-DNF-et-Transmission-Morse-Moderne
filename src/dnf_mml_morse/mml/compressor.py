"""
Compresseur MML - Compression avancée avec tokens lexicaux
"""

import re
import zlib
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter, defaultdict
import heapq
import logging

logger = logging.getLogger(__name__)


class MMLCompressor:
    """
    Compresseur pour le langage MML avec compression adaptative

    Implémente plusieurs niveaux de compression :
    1. Codes courts pour les balises fréquentes
    2. Tokens lexicaux (#M, #T, etc.)
    3. Compression par dictionnaire adaptatif
    4. Compression finale (zlib)
    """

    def __init__(self, compression_level: str = 'standard'):
        """
        Initialisation du compresseur

        Args:
            compression_level: Niveau de compression ('light', 'standard', 'aggressive')
        """
        self.compression_level = compression_level

        # Codes courts pour les balises MML fréquentes
        self.tag_codes = {
            'P': 'p', 'H1': '1', 'H2': '2', 'H3': '3', 'H4': '4', 'H5': '5', 'H6': '6',
            'D': 'd', 'S': 's', 'B': 'b', 'E': 'e', 'C': 'c', 'Q': 'q', 'U': 'u', 'O': 'o', 'L': 'l',
            'A': 'a', 'R': 'r', 'F': 'f', 'N': 'n', 'I': 'i', 'T': 't', 'K': 'k', 'M': 'm',
            'J': 'j', 'X': 'x',  # Balises spéciales
        }

        # Tokens lexicaux prédéfinis (MML-C)
        self.lexical_tokens = {
            # Mots très fréquents
            'le': '#L', 'la': '#A', 'les': '#S', 'de': '#D', 'du': '#U', 'des': '#E',
            'et': '#T', 'à': '#Z', 'un': '#N', 'une': '#E', 'dans': '#I', 'sur': '#R',
            'pour': '#P', 'avec': '#V', 'par': '#Q', 'sans': '#W', 'son': '#O', 'sa': '#H',

            # Mots courants
            'qui': '#Q', 'que': '#K', 'dont': '#F', 'où': '#G', 'quand': '#C',
            'comment': '#M', 'pourquoi': '#Y', 'mais': '#B', 'ou': '#J', 'donc': '#X',

            # Termes techniques fréquents
            'transmission': '#1', 'communication': '#2', 'urgence': '#3', 'sécurité': '#4',
            'système': '#5', 'message': '#6', 'protocole': '#7', 'réseau': '#8',
            'données': '#9', 'information': '#0', 'fréquence': '#A', 'signal': '#B',
        }

        # Dictionnaire adaptatif (apprentissage)
        self.adaptive_dict = {}
        self.dict_counter = Counter()

        # Statistiques de compression
        self.stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0.0,
            'tokens_used': 0,
            'adaptive_entries': 0,
        }

    def compress(self, mml_content: str) -> Dict[str, Any]:
        """
        Compression complète du contenu MML

        Args:
            mml_content: Contenu MML à compresser

        Returns:
            Résultat de compression avec métadonnées
        """
        self.stats = {'original_size': len(mml_content)}

        # Phase 1: Codes courts pour les balises
        logger.debug("Phase 1: Codes courts pour les balises")
        compressed = self._apply_tag_codes(mml_content)

        # Phase 2: Tokens lexicaux prédéfinis
        logger.debug("Phase 2: Tokens lexicaux prédéfinis")
        compressed = self._apply_lexical_tokens(compressed)

        # Phase 3: Dictionnaire adaptatif (si niveau élevé)
        if self.compression_level in ['standard', 'aggressive']:
            logger.debug("Phase 3: Dictionnaire adaptatif")
            compressed = self._apply_adaptive_compression(compressed, mml_content)

        # Phase 4: Compression finale
        if self.compression_level == 'aggressive':
            logger.debug("Phase 4: Compression finale zlib")
            compressed = self._apply_final_compression(compressed)

        self.stats['compressed_size'] = len(compressed)
        self.stats['compression_ratio'] = len(compressed) / max(len(mml_content), 1)
        self.stats['tokens_used'] = compressed.count('#')

        return {
            'content': compressed,
            'original_size': len(mml_content),
            'compressed_size': len(compressed),
            'compression_ratio': self.stats['compression_ratio'],
            'compression_level': self.compression_level,
            'stats': self.stats.copy(),
            'format': 'mml-c',
        }

    def _apply_tag_codes(self, content: str) -> str:
        """
        Application des codes courts aux balises MML

        Args:
            content: Contenu MML

        Returns:
            Contenu avec codes courts
        """
        # Remplacement des balises ouvrantes
        for tag, code in self.tag_codes.items():
            content = re.sub(rf'<{tag}>', f'<{code}>', content)
            content = re.sub(rf'<{tag}(\s[^>]*)>', f'<{code}\\1>', content)

        # Remplacement des balises fermantes
        for tag, code in self.tag_codes.items():
            content = re.sub(rf'</{tag}>', f'</{code}>', content)

        return content

    def _apply_lexical_tokens(self, content: str) -> str:
        """
        Application des tokens lexicaux prédéfinis

        Args:
            content: Contenu MML

        Returns:
            Contenu avec tokens lexicaux
        """
        # Tri par longueur décroissante pour éviter les conflits
        sorted_tokens = sorted(self.lexical_tokens.items(),
                             key=lambda x: len(x[0]), reverse=True)

        for word, token in sorted_tokens:
            # Échapper les caractères spéciaux pour regex
            escaped_word = re.escape(word)
            # Remplacer seulement les mots complets (avec word boundaries)
            pattern = rf'\b{escaped_word}\b'
            content = re.sub(pattern, token, content, flags=re.IGNORECASE)

        return content

    def _apply_adaptive_compression(self, compressed: str, original: str) -> str:
        """
        Compression adaptative basée sur l'analyse du contenu

        Args:
            compressed: Contenu déjà compressé
            original: Contenu original pour analyse

        Returns:
            Contenu avec compression adaptative
        """
        # Analyse des séquences fréquentes dans l'original
        words = re.findall(r'\b\w+\b', original.lower())

        # Comptage des mots fréquents (mais pas déjà dans les tokens)
        existing_tokens = set(self.lexical_tokens.keys())
        word_freq = Counter(word for word in words
                          if word not in existing_tokens and len(word) > 3)

        # Sélection des mots les plus fréquents
        top_words = [word for word, _ in word_freq.most_common(20)]

        # Attribution de nouveaux tokens (#a, #b, #c, etc.)
        token_start = ord('a')
        for i, word in enumerate(top_words):
            if i >= 26:  # Limite à 26 tokens adaptatifs
                break
            token = f'#{chr(token_start + i)}'
            if token not in self.lexical_tokens.values():
                self.adaptive_dict[word] = token
                # Application du token
                escaped_word = re.escape(word)
                compressed = re.sub(rf'\b{escaped_word}\b', token, compressed, flags=re.IGNORECASE)

        self.stats['adaptive_entries'] = len(self.adaptive_dict)

        return compressed

    def _apply_final_compression(self, content: str) -> str:
        """
        Compression finale avec zlib

        Args:
            content: Contenu à compresser

        Returns:
            Contenu compressé (bytes encodés en base64-like)
        """
        # Compression zlib
        compressed_bytes = zlib.compress(content.encode('utf-8'), level=9)

        # Encodage en base64-like pour transmission texte
        import base64
        encoded = base64.b64encode(compressed_bytes).decode('ascii')

        # Ajout d'un marqueur de compression finale
        return f"@@ZLIB@@{encoded}"

    def decompress(self, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Décompression du contenu MML-C

        Args:
            compressed_data: Données compressées

        Returns:
            Contenu décompressé
        """
        content = compressed_data['content']

        # Phase 1: Décompression finale si présente
        if content.startswith('@@ZLIB@@'):
            content = self._decompress_final(content)

        # Phase 2: Restauration des tokens adaptatifs
        if self.adaptive_dict:
            for word, token in self.adaptive_dict.items():
                content = content.replace(token, word)

        # Phase 3: Restauration des tokens lexicaux
        # Inversion du dictionnaire
        token_to_word = {v: k for k, v in self.lexical_tokens.items()}
        for token, word in token_to_word.items():
            content = content.replace(token, word)

        # Phase 4: Restauration des codes de balises
        # Inversion du dictionnaire des codes
        code_to_tag = {v: k for k, v in self.tag_codes.items()}
        for code, tag in code_to_tag.items():
            content = re.sub(rf'<{code}>', f'<{tag}>', content)
            content = re.sub(rf'<{code}(\s[^>]*)>', f'<{tag}\\1>', content)
            content = re.sub(rf'</{code}>', f'</{tag}>', content)

        return {
            'content': content,
            'original_compressed_size': compressed_data.get('compressed_size', 0),
            'decompressed_size': len(content),
            'format': 'mml',
        }

    def _decompress_final(self, content: str) -> str:
        """
        Décompression finale zlib

        Args:
            content: Contenu compressé

        Returns:
            Contenu décompressé
        """
        import base64

        # Extraction de la partie compressée
        zlib_marker = '@@ZLIB@@'
        if not content.startswith(zlib_marker):
            return content

        encoded_data = content[len(zlib_marker):]

        try:
            # Décodage base64
            compressed_bytes = base64.b64decode(encoded_data)

            # Décompression zlib
            decompressed_bytes = zlib.decompress(compressed_bytes)

            # Décodage UTF-8
            return decompressed_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"Erreur de décompression finale: {e}")
            return content  # Retour du contenu original en cas d'erreur

    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyse du contenu pour optimiser la compression

        Args:
            content: Contenu à analyser

        Returns:
            Analyse détaillée
        """
        analysis = {
            'total_chars': len(content),
            'tags_count': len(re.findall(r'</?\w+', content)),
            'text_ratio': 0.0,
            'word_freq': {},
            'tag_freq': {},
            'compression_potential': 0.0,
        }

        # Ratio texte/balises
        text_parts = re.findall(r'[^<>]+', content)
        total_text = sum(len(part) for part in text_parts)
        analysis['text_ratio'] = total_text / max(len(content), 1)

        # Fréquence des mots
        words = re.findall(r'\b\w+\b', content)
        analysis['word_freq'] = dict(Counter(words).most_common(20))

        # Fréquence des balises
        tags = re.findall(r'</?(\w+)', content)
        analysis['tag_freq'] = dict(Counter(tags).most_common(10))

        # Estimation du potentiel de compression
        # Basé sur la redondance des mots et balises
        unique_words = len(set(words))
        total_words = len(words)
        redundancy = 1 - (unique_words / max(total_words, 1))

        unique_tags = len(set(tags))
        total_tags = len(tags)
        tag_redundancy = 1 - (unique_tags / max(total_tags, 1))

        analysis['compression_potential'] = (redundancy * 0.6 + tag_redundancy * 0.4)

        return analysis

    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Statistiques détaillées de compression

        Returns:
            Statistiques de compression
        """
        return {
            'compression_level': self.compression_level,
            'lexical_tokens_count': len(self.lexical_tokens),
            'tag_codes_count': len(self.tag_codes),
            'adaptive_dict_size': len(self.adaptive_dict),
            'stats': self.stats.copy(),
        }


# Fonctions utilitaires
def compress_mml(content: str, level: str = 'standard') -> Dict[str, Any]:
    """
    Fonction utilitaire pour compression directe

    Args:
        content: Contenu MML à compresser
        level: Niveau de compression

    Returns:
        Résultat de compression
    """
    compressor = MMLCompressor(level)
    return compressor.compress(content)


def decompress_mmlc(compressed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fonction utilitaire pour décompression directe

    Args:
        compressed_data: Données compressées

    Returns:
        Données décompressées
    """
    compressor = MMLCompressor()
    return compressor.decompress(compressed_data)
