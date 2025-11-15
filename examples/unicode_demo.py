#!/usr/bin/env python3
"""
Démonstration du support Unicode dans DNF-MML-Morse

Montre comment le système gère les caractères Unicode :
- Émojis
- Caractères accentués
- Scripts non-latins (cyrillique, grec, arabe, etc.)
"""

import sys
from pathlib import Path

# Ajout du répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dnf_mml_morse.morse.codec import MorseCodec, encode_morse, decode_morse
from dnf_mml_morse.unicode_handler import normalize_unicode_text, get_unicode_info


def demo_unicode_text():
    """Démonstration avec différents types de texte Unicode"""
    print("🌍 Démonstration du support Unicode")
    print("=" * 60)

    # Textes de test avec différents types de caractères Unicode
    test_texts = [
        ("Français accentué", "Café, naïve, résumé, coéquipier"),
        ("Émojis courants", "J'adore ❤️ le café ☕ et la musique 🎵! 👍"),
        ("Cyrillique", "Привет мир! Как дела?"),
        ("Grec", "Γεια σου κόσμε! Τι κάνεις;"),
        ("Arabe simple", "مرحبا بالعالم! كيف حالك؟"),
        ("Maths/Tech", "α + β = ∑ ∫ π ≈ 3.14"),
        ("Mix complexe", "Hello 世界 🌍 Café café Привет! 🎉 α + β"),
    ]

    codec = MorseCodec(mode='optimized', unicode_support=True)

    for name, text in test_texts:
        print(f"\n📝 {name}:")
        print(f"   Original: {text}")

        # Analyse Unicode
        unicode_info = codec.get_unicode_info(text)
        if unicode_info.get('total_unicode_chars', 0) > 0:
            print(f"   Caractères Unicode: {unicode_info['total_unicode_chars']}")
            print(f"   Scripts: {list(unicode_info['scripts'].keys())}")

        # Normalisation
        normalized = normalize_unicode_text(text)
        if normalized != text:
            print(f"   Normalisé: {normalized}")

        # Encodage Morse
        morse = codec.encode(text, add_prosigns=False)
        print(f"   Morse: {morse[:60]}{'...' if len(morse) > 60 else ''}")

        # Décodage (pour vérifier)
        decoded = codec.decode(morse)
        status = "✓" if decoded == normalized.upper() else "✗"
        print(f"   Décodé: {decoded} {status}")

        print()


def demo_custom_mappings():
    """Démonstration des mappings personnalisés"""
    print("🔧 Mappings personnalisés")
    print("=" * 60)

    codec = MorseCodec(unicode_support=True)

    # Ajouter des mappings personnalisés
    custom_mappings = [
        ("🚀", "ROCKET"),
        ("🛰️", "SAT"),
        ("📡", "ANTENNA"),
        ("⚡", "POWER"),
        ("🔋", "BATTERY"),
    ]

    print("Mappings personnalisés ajoutés:")
    for char, replacement in custom_mappings:
        codec.add_unicode_mapping(char, replacement)
        print(f"   {char} -> {replacement}")

    # Texte avec ces émojis
    text = "Satellite 🚀 avec antenne 📡 et batterie 🔋 pleine ⚡"
    print(f"\nTexte original: {text}")

    normalized = normalize_unicode_text(text)
    print(f"Texte normalisé: {normalized}")

    morse = codec.encode(text, add_prosigns=False)
    print(f"Morse: {morse}")

    print()


def demo_unicode_stats():
    """Démonstration des statistiques Unicode"""
    print("📊 Statistiques Unicode")
    print("=" * 60)

    # Texte riche en Unicode
    rich_text = """
    Bonjour! ☕ Café & thé 🍵

    Mathématiques: α + β = γ, π ≈ 3.14
    Émojis: ❤️ 👍 😂 😊 🌟

    Cyrillique: Привет! Здравствуйте!
    Grec: Γεια σου! Χαίρετε!

    Mix: Hello 世界 🌍 + αβγ + Привет! 🎉
    """

    codec = MorseCodec(unicode_support=True)

    # Encoder plusieurs fois pour accumuler des stats
    for _ in range(3):
        codec.encode(rich_text)

    stats = codec.get_stats()

    print("Statistiques générales:")
    print(f"   Caractères encodés: {stats['stats']['encoded_chars']}")
    print(f"   Erreurs: {stats['stats']['errors']}")

    if 'unicode_stats' in stats:
        unicode_stats = stats['unicode_stats']
        print("\nStatistiques Unicode:")
        print(f"   Caractères traités: {unicode_stats['characters_processed']}")
        print(f"   Caractères Unicode: {unicode_stats['unicode_characters']}")
        print(f"   Ratio Unicode: {unicode_stats['unicode_ratio_percent']}%")
        print(f"   Translittérations: {unicode_stats['transliterations']}")
        print(f"   Fallbacks: {unicode_stats['fallbacks']}")

        print(f"\nScripts supportés: {', '.join(unicode_stats['supported_scripts'])}")

    print()


def demo_error_handling():
    """Démonstration de la gestion d'erreurs"""
    print("⚠️ Gestion d'erreurs Unicode")
    print("=" * 60)

    # Texte avec caractères problématiques
    problematic_text = "Hello 世界 🌍 𝄞 🎼"  # Caractères musicaux rares

    print(f"Texte problématique: {problematic_text}")

    # Analyse
    info = get_unicode_info(problematic_text)
    print(f"Analyse: {info['total_unicode_chars']} caractères Unicode")
    print(f"Scripts: {list(info['scripts'].keys())}")

    # Normalisation avec différents modes
    modes = ['transliterate', 'decompose', 'remove']

    for mode in modes:
        normalized = normalize_unicode_text(problematic_text, mode=mode)
        print(f"Mode '{mode}': {normalized}")

    print()


def main():
    """Fonction principale de démonstration"""
    print("🎯 Démonstration du support Unicode - DNF-MML-Morse")
    print("=" * 80)
    print()

    try:
        demo_unicode_text()
        demo_custom_mappings()
        demo_unicode_stats()
        demo_error_handling()

        print("🎉 Démonstration Unicode terminée avec succès!")
        print()
        print("💡 Le système supporte maintenant:")
        print("   • Émojis courants avec mappings dédiés")
        print("   • Caractères accentués européens")
        print("   • Translittération cyrillique, grecque, arabe")
        print("   • Mappings personnalisables")
        print("   • Fallbacks pour caractères inconnus")
        print("   • Statistiques détaillées d'utilisation")

    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
