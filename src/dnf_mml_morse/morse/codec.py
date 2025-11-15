"""
Codec Morse - Encodage et décodage Morse optimisé pour MML-C
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
import logging

from ..unicode_handler import UnicodeHandler

logger = logging.getLogger(__name__)


class MorseCodec:
    """
    Codec Morse optimisé pour la transmission de MML-C

    Modes d'encodage :
    - standard: Morse international classique
    - optimized: Mapping optimisé pour MML-C (priorité aux caractères fréquents)
    - robust: Version robuste aux erreurs (répétitions, redondance)
    """

    def __init__(self, mode: str = 'optimized', wpm: int = 20, unicode_support: bool = True):
        """
        Initialisation du codec Morse

        Args:
            mode: Mode d'encodage ('standard', 'optimized', 'robust')
            wpm: Vitesse en mots par minute (pour calculs temporels)
            unicode_support: Activer le support Unicode
        """
        self.mode = mode
        self.wpm = wpm
        self.unicode_support = unicode_support

        # Gestionnaire Unicode
        self.unicode_handler = UnicodeHandler() if unicode_support else None

        # Tables Morse selon le mode
        self.encoding_tables = {
            'standard': self._get_standard_table(),
            'optimized': self._get_optimized_table(),
            'robust': self._get_robust_table(),
        }

        # Tables de décodage (inverses)
        self.decoding_tables = {}
        for mode_name, table in self.encoding_tables.items():
            self.decoding_tables[mode_name] = {v: k for k, v in table.items()}

        # Statistiques d'utilisation
        self.stats = {
            'encoded_chars': 0,
            'decoded_chars': 0,
            'errors': 0,
            'avg_symbol_length': 0.0,
        }

        # Vérification du mode
        if mode not in self.encoding_tables:
            raise ValueError(f"Mode inconnu: {mode}. Modes disponibles: {list(self.encoding_tables.keys())}")

    def _get_standard_table(self) -> Dict[str, str]:
        """Table Morse internationale standard"""
        return {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..',
            '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
            '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
            '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
            '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
            '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
            '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.',
            '$': '...-..-', '@': '.--.-.', ' ': '/',
        }

    def _get_optimized_table(self) -> Dict[str, str]:
        """
        Table optimisée pour MML-C

        Priorité aux caractères fréquents en MML :
        - Balises: < > / =
        - Chiffres: 0-9 (pour compression)
        - Lettres fréquentes: E T A O I N
        - Caractères spéciaux MML: # { } [ ] ( ) " '
        """
        base = self._get_standard_table().copy()

        # Optimisations pour MML-C
        optimized = {
            # Caractères MML prioritaires (plus courts)
            '<': '.-.',     # Plus court que standard
            '>': '-.',      # Plus court que standard
            '/': '-',       # Plus court que standard
            '=': '...',     # Plus court que standard
            '#': '..',      # Très fréquent en MML-C
            '{': '.--',     # Pour tokens
            '}': '--.',     # Pour tokens
            '[': '-.',      # Pour arrays
            ']': '.-',      # Pour arrays
            '"': '..-.',    # Pour attributs
            "'": '.-..',    # Pour attributs

            # Chiffres optimisés (plus fréquents)
            '0': '-----', '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.',

            # Lettres fréquentes optimisées
            'E': '.',       # Déjà optimal
            'T': '-',       # Déjà optimal
            'A': '.-',      # Déjà optimal
            'O': '---',     # Déjà optimal
            'I': '..',      # Déjà optimal
            'N': '-.',      # Déjà optimal
            'S': '...',     # Déjà optimal
            'R': '.-.',     # Déjà optimal
            'H': '....',    # Déjà optimal
            'L': '.-..',    # Plus court
            'D': '-..',     # Déjà optimal
            'C': '-.-.',    # Plus court
            'U': '..-',     # Déjà optimal
            'M': '--',      # Déjà optimal
            'F': '..-.',    # Plus court
            'Y': '-.--',    # Plus court
            'P': '.--.',    # Plus court
            'G': '--.',     # Déjà optimal
            'W': '.--',     # Déjà optimal
            'B': '-...',    # Plus court
            'V': '...-',    # Plus court
            'K': '-.-',     # Déjà optimal
            'X': '-..-',    # Plus court
            'J': '.---',    # Plus court
            'Q': '--.-',    # Plus court
            'Z': '--..',    # Plus court

            ' ': '/',       # Séparateur de mots
        }

        # Fusion avec les caractères standards restants
        for char, code in base.items():
            if char not in optimized:
                optimized[char] = code

        return optimized

    def _get_robust_table(self) -> Dict[str, str]:
        """
        Table robuste avec redondance

        Chaque symbole est répété pour résister aux erreurs de transmission
        """
        base = self._get_optimized_table().copy()

        # Ajout de redondance (répétition des symboles)
        robust = {}
        for char, code in base.items():
            if char == ' ':
                robust[char] = code  # Le séparateur reste simple
            else:
                # Répétition du code avec séparateur
                robust[char] = f"{code}/{code}"

        return robust

    def encode(self, text: str, add_prosigns: bool = True) -> str:
        """
        Encodage du texte en Morse

        Args:
            text: Texte à encoder
            add_prosigns: Ajouter les signes de procédure

        Returns:
            Séquence Morse
        """
        if not text:
            return ""

        # Prétraitement Unicode si activé
        if self.unicode_support and self.unicode_handler:
            original_text = text
            text = self.unicode_handler.normalize_unicode(text)

            if text != original_text:
                logger.debug(f"Texte Unicode normalisé: '{original_text}' -> '{text}'")

        table = self.encoding_tables[self.mode]
        result = []
        char_count = 0

        for char in text.upper():
            if char in table:
                morse = table[char]
                result.append(morse)
                char_count += 1
            else:
                # Caractère inconnu - utilisation d'un code spécial
                logger.warning(f"Caractère inconnu ignoré: {char} (U+{ord(char):04X})")
                self.stats['errors'] += 1

        morse_sequence = ' '.join(result)

        # Ajout des signes de procédure si demandé
        if add_prosigns:
            morse_sequence = f"<BT> {morse_sequence} <AR>"

        # Mise à jour des statistiques
        self.stats['encoded_chars'] += char_count
        if result:
            self.stats['avg_symbol_length'] = sum(len(code) for code in result) / len(result)

        return morse_sequence

    def decode(self, morse_sequence: str, ignore_errors: bool = True) -> str:
        """
        Décodage d'une séquence Morse

        Args:
            morse_sequence: Séquence Morse à décoder
            ignore_errors: Ignorer les erreurs de décodage

        Returns:
            Texte décodé
        """
        if not morse_sequence:
            return ""

        table = self.decoding_tables[self.mode]
        result = []
        char_count = 0

        # Nettoyage de la séquence
        morse_sequence = morse_sequence.strip()

        # Suppression des signes de procédure
        morse_sequence = re.sub(r'<[^>]+>', '', morse_sequence)

        # Découpage en symboles
        symbols = morse_sequence.split()

        for symbol in symbols:
            # Gestion du mode robust (répétitions)
            if self.mode == 'robust' and '/' in symbol:
                # Prendre la première partie de la répétition
                symbol = symbol.split('/')[0]

            if symbol in table:
                char = table[symbol]
                result.append(char)
                char_count += 1
            elif not ignore_errors:
                raise ValueError(f"Symbole Morse inconnu: {symbol}")
            else:
                logger.warning(f"Symbole Morse inconnu ignoré: {symbol}")
                result.append('?')  # Caractère d'erreur
                self.stats['errors'] += 1

        decoded_text = ''.join(result)

        # Mise à jour des statistiques
        self.stats['decoded_chars'] += char_count

        return decoded_text

    def get_timing_info(self, morse_sequence: str) -> Dict[str, Any]:
        """
        Calcul des informations temporelles pour la transmission

        Args:
            morse_sequence: Séquence Morse

        Returns:
            Informations de timing
        """
        # Paramètres PARIS (standard)
        dot_duration = 60.0 / (50 * self.wpm)  # Durée d'un point en secondes

        durations = {
            '.': dot_duration,           # Point
            '-': 3 * dot_duration,       # Trait
            ' ': dot_duration,           # Espace inter-symboles
            '/': 7 * dot_duration,       # Espace inter-mots
        }

        # Analyse de la séquence
        total_duration = 0
        symbol_count = 0

        for char in morse_sequence:
            if char in durations:
                total_duration += durations[char]
                if char in '.-':
                    symbol_count += 1

        return {
            'total_duration_seconds': total_duration,
            'symbol_count': symbol_count,
            'wpm_effective': self.wpm,
            'characters_per_minute': (symbol_count * 60) / max(total_duration, 1),
            'transmission_time_minutes': total_duration / 60,
        }

    def optimize_for_mmlc(self, mmlc_content: str) -> Dict[str, Any]:
        """
        Optimisation du codec pour contenu MML-C spécifique

        Args:
            mmlc_content: Contenu MML-C

        Returns:
            Configuration optimisée
        """
        # Analyse de fréquence des caractères
        char_freq = defaultdict(int)
        for char in mmlc_content.upper():
            char_freq[char] += 1

        # Caractères les plus fréquents
        top_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Création d'une table personnalisée
        custom_table = self.encoding_tables[self.mode].copy()

        # Attribution de codes courts aux caractères fréquents
        short_codes = ['.', '-', '..', '.-', '-.']
        for i, (char, _) in enumerate(top_chars):
            if i < len(short_codes) and char not in ['<', '>', '/', '=']:
                custom_table[char] = short_codes[i]

        return {
            'custom_table': custom_table,
            'top_chars': top_chars,
            'estimated_improvement': len(top_chars) * 0.1,  # Estimation
        }

    def validate_morse(self, morse_sequence: str) -> Dict[str, Any]:
        """
        Validation d'une séquence Morse

        Args:
            morse_sequence: Séquence à valider

        Returns:
            Résultats de validation
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {},
        }

        # Vérifications de base
        if not morse_sequence.strip():
            result['warnings'].append("Séquence Morse vide")
            return result

        # Vérification des caractères autorisés
        allowed_chars = set('.-/ ')
        for char in morse_sequence:
            if char not in allowed_chars:
                result['errors'].append(f"Caractère invalide: {char}")
                result['valid'] = False

        # Vérification de la structure
        symbols = morse_sequence.split()
        valid_symbols = set(self.encoding_tables[self.mode].values())

        invalid_symbols = []
        for symbol in symbols:
            if symbol not in valid_symbols and symbol != '/':
                invalid_symbols.append(symbol)

        if invalid_symbols:
            result['warnings'].append(f"Symboles inconnus: {invalid_symbols[:5]}...")

        # Statistiques
        result['stats'] = {
            'total_symbols': len(symbols),
            'unique_symbols': len(set(symbols)),
            'avg_symbol_length': sum(len(s) for s in symbols if s != '/') / max(len([s for s in symbols if s != '/']), 1),
            'word_count': morse_sequence.count('/') + 1,
        }

        return result

    def add_unicode_mapping(self, char: str, replacement: str):
        """
        Ajoute un mapping Unicode personnalisé

        Args:
            char: Caractère Unicode
            replacement: Chaîne de remplacement ASCII
        """
        if self.unicode_handler:
            self.unicode_handler.add_custom_mapping(char, replacement)
            logger.info(f"Mapping Unicode ajouté: {char} -> {replacement}")
        else:
            raise ValueError("Support Unicode désactivé")

    def get_unicode_info(self, text: str) -> Dict[str, Any]:
        """
        Analyse les caractères Unicode dans un texte

        Args:
            text: Texte à analyser

        Returns:
            Informations Unicode
        """
        if self.unicode_handler:
            return self.unicode_handler.get_unicode_info(text)
        else:
            return {'unicode_support': False}

    def get_stats(self) -> Dict[str, Any]:
        """
        Statistiques d'utilisation du codec

        Returns:
            Statistiques détaillées
        """
        stats = {
            'mode': self.mode,
            'wpm': self.wpm,
            'unicode_support': self.unicode_support,
            'stats': self.stats.copy(),
            'table_size': len(self.encoding_tables[self.mode]),
        }

        # Ajouter les statistiques Unicode si activé
        if self.unicode_support and self.unicode_handler:
            stats['unicode_stats'] = self.unicode_handler.get_stats()

        return stats


# Fonctions utilitaires
def encode_morse(text: str, mode: str = 'optimized') -> str:
    """
    Fonction utilitaire d'encodage

    Args:
        text: Texte à encoder
        mode: Mode d'encodage

    Returns:
        Séquence Morse
    """
    codec = MorseCodec(mode=mode)
    return codec.encode(text)


def decode_morse(morse_sequence: str, mode: str = 'optimized') -> str:
    """
    Fonction utilitaire de décodage

    Args:
        morse_sequence: Séquence Morse
        mode: Mode de décodage

    Returns:
        Texte décodé
    """
    codec = MorseCodec(mode=mode)
    return codec.decode(morse_sequence)


# Alias pour compatibilité
def morse_encode(text: str, mode: str = 'optimized') -> str:
    """Alias pour encode_morse"""
    return encode_morse(text, mode)


def morse_decode(morse_sequence: str, mode: str = 'optimized') -> str:
    """Alias pour decode_morse"""
    return decode_morse(morse_sequence, mode)
