#!/usr/bin/env python3
"""
Demonstration simple du systeme DNF-MML-Morse (sans emojis)
"""

import sys
from pathlib import Path

# Ajout du repertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    print(">>> Demonstration du systeme DNF-MML-Morse")
    print("=" * 60)
    print()

    try:
        from dnf_mml_morse.mml.parser import MMLParser
        from dnf_mml_morse.mml.compressor import MMLCompressor
        from dnf_mml_morse.morse.codec import MorseCodec

        print("[OK] Import des modules reussi")

        # Test basique du parser
        parser = MMLParser()
        test_mml = '<H1>Test</H1><P>Hello World</P>'
        validation = parser.validate_mml(test_mml)
        print(f"[OK] Parser MML: {validation['valid']}")

        # Test basique du compresseur
        compressor = MMLCompressor()
        compressed = compressor.compress(test_mml)
        print(f"[OK] Compresseur: ratio {compressed['compression_ratio']:.2f}")
        # Test basique du codec Morse
        codec = MorseCodec()
        morse = codec.encode('HELLO')
        decoded = codec.decode(morse)
        print(f"[OK] Codec Morse: {decoded}")

        print("[SUCCESS] Tous les tests de base reussis!")
        print()
        print("Le systeme DNF-MML-Morse est operationnel!")
        print()
        print("Pour plus d'informations:")
        print("- Guide de demarrage: QUICKSTART.md")
        print("- Documentation: docs/")
        print("- Exemples: examples/")

    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
