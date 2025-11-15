#!/usr/bin/env python3
"""
Démonstration complète du système DNF-MML-Morse
"""

import asyncio
import sys
from pathlib import Path

# Ajout du répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dnf_mml_morse.core import DNFMMLMorseSystem
from dnf_mml_morse.mml import convert_to_mml_sync
from dnf_mml_morse.morse import encode_morse, decode_morse
from dnf_mml_morse.mml.compressor import compress_mml


def demo_conversion():
    """Démonstration de la conversion HTML vers MML"""
    print("[CONVERSION] Conversion HTML vers MML")
    print("=" * 50)

    # Conversion du fichier exemple
    try:
        mml_doc = convert_to_mml_sync('examples/sample.html')
        print("✓ Conversion réussie")
        print(f"  Format source: {mml_doc['format']}")
        print(f"  Taille originale: {mml_doc['size']} octets")
        print(f"  Taille MML: {len(mml_doc['content'])} caractères")
        print(f"  Métadonnées: {mml_doc['metadata']['title']}")
        print()
        print("Aperçu MML:")
        print(mml_doc['content'][:200] + "...")
        print()

    except Exception as e:
        print(f"❌ Erreur de conversion: {e}")
        return False

    return True


def demo_compression():
    """Démonstration de la compression MML"""
    print("🗜️ Compression MML-C")
    print("=" * 50)

    # Contenu de test
    test_content = """
<H1>Guide de survie en forêt</H1>
<H2>Préparation</H2>
<P>Avant de partir en forêt, il est essentiel de bien se préparer. Emportez une carte, une boussole, et informez quelqu'un de votre itinéraire.</P>
<H2>Signes de détresse</H2>
<P>En cas de problème, restez calme et signalez votre position. Utilisez un sifflet ou un feu pour attirer l'attention des secours.</P>
<H2>Premier secours</H2>
<P>Si vous êtes blessé, immobilisez la zone touchée et conservez votre chaleur corporelle. Attendez les secours sans bouger.</P>
""".strip()

    try:
        # Compression
        compressed = compress_mml(test_content, level='standard')

        print("✓ Compression réussie")
        print(f"  Taille originale: {compressed['original_size']} caractères")
        print(f"  Taille compressée: {len(compressed['content'])} caractères")
        print(f"  Ratio de compression: {compressed['compression_ratio']:.2%}")
        print(f"  Niveau: {compressed['compression_level']}")
        print()
        print("Contenu compressé:")
        print(compressed['content'][:100] + "..." if len(compressed['content']) > 100 else compressed['content'])
        print()

    except Exception as e:
        print(f"❌ Erreur de compression: {e}")
        return False

    return True


def demo_morse():
    """Démonstration du codec Morse"""
    print("📡 Codec Morse")
    print("=" * 50)

    test_texts = [
        "SOS",
        "HELLO WORLD",
        "DNF MML MORSE",
        "73 DE F6ABC"
    ]

    try:
        for text in test_texts:
            print(f"Texte: {text}")

            # Encodage standard
            morse_std = encode_morse(text, mode='standard')
            print(f"  Morse standard: {morse_std}")

            # Encodage optimisé
            morse_opt = encode_morse(text, mode='optimized')
            print(f"  Morse optimisé: {morse_opt}")

            # Décodage
            decoded = decode_morse(morse_opt, mode='optimized')
            print(f"  Décodé: {decoded}")
            print(f"  ✓ Intégrité: {'OK' if decoded == text else 'ERREUR'}")
            print()

    except Exception as e:
        print(f"❌ Erreur Morse: {e}")
        return False

    return True


async def demo_transmission():
    """Démonstration de transmission complète"""
    print("📤 Transmission complète DNF-MML-Morse")
    print("=" * 50)

    try:
        # Configuration du système
        config = {
            'morse_mode': 'optimized',
            'transport': 'cw',
            'callsign': 'DEMO',
            'compression_level': 'standard'
        }

        print("Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()

        # Initialisation
        system = DNFMMLMorseSystem(config)
        print("✓ Système initialisé")

        # Transmission
        print("Transmission en cours...")
        result = await system.transmit_document('examples/sample.html', destination='F6XYZ')

        if result['success']:
            print("✓ Transmission réussie!")
            print(f"  Fragments envoyés: {result['fragments_sent']}")
            print(f"  Octets transmis: {result['mml_size']}")
            print(f"  Ratio compression: {result['compression_ratio']:.2%}")
            print(f"  Durée: {result['transmission_time']:.1f}s")
            print(f"  Transport: {result['transport_used']}")
            print(f"  Destination: {result['destination']}")
        else:
            print(f"❌ Échec: {result['error']}")

        print()

    except Exception as e:
        print(f"❌ Erreur de transmission: {e}")
        return False

    return True


async def demo_reception():
    """Démonstration de réception"""
    print("📥 Réception de documents")
    print("=" * 50)

    try:
        config = {
            'morse_mode': 'optimized',
            'transport': 'cw',
            'callsign': 'DEMO'
        }

        system = DNFMMLMorseSystem(config)
        print("✓ Système de réception initialisé")

        # Simulation de réception
        print("Surveillance du réseau...")
        documents = await system.receive_documents()

        if documents['success'] and documents['documents']:
            print(f"✓ {len(documents['documents'])} document(s) reçu(s)")

            for i, doc in enumerate(documents['documents'], 1):
                print(f"  Document {i}:")
                print(f"    Source: {doc.get('source', 'unknown')}")
                print(f"    Taille: {len(doc.get('content', ''))} caractères")
                print(f"    Aperçu: {doc.get('content', '')[:50]}...")
        else:
            print("ℹ️ Aucun document reçu (normal en mode simulation)")

        print()

    except Exception as e:
        print(f"❌ Erreur de réception: {e}")
        return False

    return True


async def main():
    """Fonction principale de démonstration"""
    print(">>> Demonstration du systeme DNF-MML-Morse")
    print("=" * 60)
    print()

    # Vérification des fichiers requis
    if not Path('examples/sample.html').exists():
        print("❌ Fichier examples/sample.html manquant")
        print("   Lancez d'abord: python setup.py develop")
        return

    demos = [
        ("Conversion HTML→MML", demo_conversion, False),  # sync
        ("Compression MML-C", demo_compression, False),   # sync
        ("Codec Morse", demo_morse, False),               # sync
        ("Transmission complète", demo_transmission, True), # async
        ("Réception", demo_reception, True),               # async
    ]

    results = []
    for name, demo_func, is_async in demos:
        print(f"🚀 {name}")
        print("-" * 30)

        if is_async:
            success = await demo_func()
        else:
            success = demo_func()

        results.append((name, success))

        if not success:
            print("⚠️ Démonstration interrompue à cause d'erreurs")
            break

        print()

    # Résumé
    print("📊 Résumé de la démonstration")
    print("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for name, success in results:
        status = "✓" if success else "❌"
        print(f"{status} {name}")

    print()
    print(f"Score: {success_count}/{total_count} démonstrations réussies")

    if success_count == total_count:
        print("🎉 Toutes les démonstrations ont réussi!")
        print("   Le système DNF-MML-Morse est opérationnel.")
    else:
        print("⚠️ Certaines démonstrations ont échoué.")
        print("   Vérifiez les logs ci-dessus pour le dépannage.")

    print()
    print("💡 Pour plus d'informations:")
    print("   - Guide de démarrage: QUICKSTART.md")
    print("   - Documentation: docs/")
    print("   - Exemples: examples/")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Démonstration interrompue")
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
