"""
Gestionnaire Unicode pour DNF-MML-Morse

Gère la conversion des caractères Unicode en séquences Morse,
avec support pour les caractères accentués, émojis, et autres scripts.
"""

import unicodedata
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class UnicodeHandler:
    """
    Gestionnaire Unicode pour la transmission Morse

    Convertit les caractères Unicode en séquences Morse via :
    1. Normalisation Unicode (NFD/NFC)
    2. Translittération pour les scripts non-latins
    3. Décomposition des caractères combinés
    4. Fallback pour les caractères non supportés
    """

    def __init__(self):
        """Initialisation du gestionnaire Unicode"""
        self._load_transliteration_tables()
        self._load_emoji_mappings()
        self._load_extended_latin_mappings()

        # Statistiques
        self.stats = {
            'characters_processed': 0,
            'unicode_characters': 0,
            'transliterations': 0,
            'fallbacks': 0,
        }

    def _load_transliteration_tables(self):
        """Charge les tables de translittération"""
        # Translittération cyrillique vers latin
        self.cyrillic_to_latin = {
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
            'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'J', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'KH', 'Ц': 'TS', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SHCH',
            'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA',
            # Minuscules
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }

        # Translittération grecque
        self.greek_to_latin = {
            'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H',
            'Θ': 'TH', 'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X',
            'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Φ': 'F',
            'Χ': 'CH', 'Ψ': 'PS', 'Ω': 'O',
            # Minuscules
            'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h',
            'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x',
            'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'y', 'φ': 'f',
            'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
        }

        # Translittération hébraïque basique
        self.hebrew_to_latin = {
            'א': "'", 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'v', 'ז': 'z',
            'ח': 'kh', 'ט': 't', 'י': 'y', 'כ': 'k', 'ל': 'l', 'מ': 'm', 'נ': 'n',
            'ס': 's', 'ע': "'", 'פ': 'p', 'צ': 'ts', 'ק': 'k', 'ר': 'r', 'ש': 'sh',
            'ת': 't',
        }

        # Translittération arabe basique
        self.arabic_to_latin = {
            'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
            'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
            'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': "'", 'غ': 'gh', 'ف': 'f', 'ق': 'q',
            'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        }

    def _load_extended_latin_mappings(self):
        """Charge les mappings pour caractères latins étendus"""
        # Caractères accentués courants
        self.extended_latin = {
            # Français
            'à': 'a', 'â': 'a', 'ä': 'a', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'ï': 'i', 'î': 'i', 'ô': 'o', 'ö': 'o', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ÿ': 'y', 'ç': 'c',
            # Majuscules accentuées
            'À': 'A', 'Â': 'A', 'Ä': 'A', 'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Ï': 'I', 'Î': 'I', 'Ô': 'O', 'Ö': 'O', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ÿ': 'Y', 'Ç': 'C',
            # Espagnol
            'á': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n',
            'Á': 'A', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N',
            # Portugais
            'ã': 'a', 'õ': 'o', 'â': 'a', 'ê': 'e', 'ô': 'o',
            'Ã': 'A', 'Õ': 'O', 'Â': 'A', 'Ê': 'E', 'Ô': 'O',
            # Allemand
            'ß': 'ss',
            # Autres
            'ø': 'o', 'Ø': 'O', 'å': 'a', 'Å': 'A',
        }

    def _load_emoji_mappings(self):
        """Charge les mappings pour émojis courants"""
        # Émojis de communication couramment utilisés
        self.emoji_mappings = {
            '❤️': '<3', '👍': 'OK', '👎': 'KO', '😂': 'LOL', '😊': ':)', '😢': ':(',
            '😮': ':O', '😍': '<3', '🤔': '?!', '🙄': ':/', '😴': 'ZZZ', '💯': '100',
            '🔥': 'HOT', '💪': 'STR', '🎉': 'YAY', '💔': 'X3', '😎': '8)', '🤗': 'HUG',
            '😇': 'HALO', '😈': 'DEVIL', '👻': 'GHOST', '💩': 'POO', '🐱': 'CAT', '🐶': 'DOG',
            '🌟': 'STAR', '⚡': 'FLASH', '❄️': 'ICE', '🔥': 'FIRE', '💧': 'DROP', '🌈': 'RAINBOW',
            '🌞': 'SUN', '🌙': 'MOON', '⭐': 'STAR', '✨': 'SPARKLE', '🔮': 'BALL',
            '🎵': 'MUSIC', '🎶': 'NOTE', '🎤': 'MIC', '🎧': 'HEAD', '📱': 'PHONE', '💻': 'PC',
            '🚀': 'ROCKET', '✈️': 'PLANE', '🚗': 'CAR', '🏠': 'HOME', '🏃': 'RUN', '⚽': 'BALL',
            '🍕': 'PIZZA', '☕': 'COFFEE', '🍺': 'BEER', '🎂': 'CAKE', '🎁': 'GIFT',
        }

        # Catégories d'émojis pour fallback
        self.emoji_categories = {
            'smileys': ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇'],
            'hearts': ['❤️', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '💕'],
            'gestures': ['👍', '👎', '👌', '✌️', '🤞', '👏', '🙌', '🤝', '🙏', '✊'],
            'nature': ['🌱', '🌿', '🌾', '🌵', '🌲', '🌳', '🌴', '🌸', '🌺', '🌻'],
            'weather': ['☀️', '🌤️', '⛅', '☁️', '🌧️', '⛈️', '🌩️', '❄️', '🌨️', '🌪️'],
        }

    def normalize_unicode(self, text: str, mode: str = 'transliterate') -> str:
        """
        Normalise le texte Unicode pour la transmission Morse

        Args:
            text: Texte Unicode à normaliser
            mode: Mode de normalisation ('transliterate', 'decompose', 'remove')

        Returns:
            Texte normalisé
        """
        if not text:
            return ""

        original_length = len(text)
        processed_chars = 0
        unicode_chars = 0
        transliterations = 0
        fallbacks = 0

        result_parts = []

        for char in text:
            processed_chars += 1

            # Caractère ASCII standard - pas de traitement
            if ord(char) < 128:
                result_parts.append(char)
                continue

            unicode_chars += 1
            replacement = None

            # 1. Essai des mappings directs
            if char in self.emoji_mappings:
                replacement = self.emoji_mappings[char]
                transliterations += 1
            elif char in self.extended_latin:
                replacement = self.extended_latin[char]
                transliterations += 1
            elif char in self.cyrillic_to_latin:
                replacement = self.cyrillic_to_latin[char]
                transliterations += 1
            elif char in self.greek_to_latin:
                replacement = self.greek_to_latin[char]
                transliterations += 1
            elif char in self.hebrew_to_latin:
                replacement = self.hebrew_to_latin[char]
                transliterations += 1
            elif char in self.arabic_to_latin:
                replacement = self.arabic_to_latin[char]
                transliterations += 1

            # 2. Normalisation Unicode (décomposition)
            if replacement is None:
                try:
                    # Décomposition canonique
                    decomposed = unicodedata.normalize('NFD', char)

                    # Garde seulement les caractères de base (pas les diacritiques)
                    base_chars = []
                    for c in decomposed:
                        if unicodedata.category(c) != 'Mn':  # Non-spacing mark
                            base_chars.append(c)

                    if base_chars and base_chars[0].isalpha():
                        replacement = ''.join(base_chars)
                        transliterations += 1
                except:
                    pass

            # 3. Fallback selon le mode
            if replacement is None:
                if mode == 'remove':
                    replacement = ''  # Supprimer
                elif mode == 'decompose':
                    try:
                        # Essai de décomposition complète
                        decomposed = unicodedata.normalize('NFD', char)
                        replacement = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
                        if not replacement:
                            replacement = '?'
                    except:
                        replacement = '?'
                else:  # transliterate
                    # Représentation numérique pour caractères inconnus
                    replacement = f"{{{ord(char):04X}}}"
                fallbacks += 1

            result_parts.append(replacement)

        result = ''.join(result_parts)

        # Mise à jour des statistiques
        self.stats['characters_processed'] += processed_chars
        self.stats['unicode_characters'] += unicode_chars
        self.stats['transliterations'] += transliterations
        self.stats['fallbacks'] += fallbacks

        logger.debug(f"Normalisé {unicode_chars} caractères Unicode sur {processed_chars} total")

        return result

    def get_unicode_info(self, text: str) -> Dict[str, Any]:
        """
        Analyse les caractères Unicode dans un texte

        Args:
            text: Texte à analyser

        Returns:
            Informations sur les caractères Unicode
        """
        unicode_chars = []
        scripts = defaultdict(int)
        categories = defaultdict(int)

        for char in text:
            if ord(char) >= 128:  # Non-ASCII
                unicode_chars.append(char)

                # Script Unicode
                try:
                    script = unicodedata.script(char)
                    scripts[script] += 1
                except:
                    scripts['Unknown'] += 1

                # Catégorie Unicode
                try:
                    category = unicodedata.category(char)
                    categories[category] += 1
                except:
                    categories['Unknown'] += 1

        return {
            'total_unicode_chars': len(unicode_chars),
            'unique_unicode_chars': len(set(unicode_chars)),
            'scripts': dict(scripts),
            'categories': dict(categories),
            'sample_chars': unicode_chars[:10],  # Échantillon
        }

    def add_custom_mapping(self, char: str, replacement: str):
        """
        Ajoute un mapping personnalisé

        Args:
            char: Caractère Unicode
            replacement: Chaîne de remplacement
        """
        if len(replacement) > 10:  # Limite de longueur
            raise ValueError("Le remplacement ne peut pas dépasser 10 caractères")

        self.emoji_mappings[char] = replacement
        logger.info(f"Mapping personnalisé ajouté: {char} -> {replacement}")

    def get_supported_scripts(self) -> List[str]:
        """
        Retourne la liste des scripts supportés

        Returns:
            Liste des scripts Unicode supportés
        """
        return [
            'Latin', 'Cyrillic', 'Greek', 'Hebrew', 'Arabic',
            'Emoji', 'Extended_Latin'
        ]

    def get_stats(self) -> Dict[str, Any]:
        """
        Statistiques d'utilisation

        Returns:
            Statistiques détaillées
        """
        total_processed = self.stats['characters_processed']
        unicode_ratio = (self.stats['unicode_characters'] / max(total_processed, 1)) * 100

        return {
            'characters_processed': total_processed,
            'unicode_characters': self.stats['unicode_characters'],
            'unicode_ratio_percent': round(unicode_ratio, 2),
            'transliterations': self.stats['transliterations'],
            'fallbacks': self.stats['fallbacks'],
            'supported_scripts': self.get_supported_scripts(),
            'custom_mappings_count': len([k for k in self.emoji_mappings.keys() if k not in self._load_emoji_mappings.__defaults__[0]]),
        }


# Fonctions utilitaires
def normalize_unicode_text(text: str, mode: str = 'transliterate') -> str:
    """
    Fonction utilitaire pour normalisation Unicode

    Args:
        text: Texte à normaliser
        mode: Mode de normalisation

    Returns:
        Texte normalisé
    """
    handler = UnicodeHandler()
    return handler.normalize_unicode(text, mode)


def get_unicode_info(text: str) -> Dict[str, Any]:
    """
    Fonction utilitaire pour analyse Unicode

    Args:
        text: Texte à analyser

    Returns:
        Informations Unicode
    """
    handler = UnicodeHandler()
    return handler.get_unicode_info(text)
