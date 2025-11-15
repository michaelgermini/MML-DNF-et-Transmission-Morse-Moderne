#!/usr/bin/env python3
"""
Client de test pour l'API DNF-MML-Morse
"""

import requests
import sys
from pathlib import Path

def transmit_file(file_path, server_url="http://localhost:8000"):
    """Transmettre un fichier via l'API"""

    if not Path(file_path).exists():
        print(f"Erreur: Fichier {file_path} introuvable")
        return

    print(f"Transmission de {file_path} vers {server_url}...")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
            data = {'destination': 'TEST_CLIENT'}

            response = requests.post(f"{server_url}/api/transmit", files=files, data=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Transmission réussie!")
                print(f"   Ratio compression: {result['transmission']['compression_ratio']:.2%}")
                print(f"   Fragments envoyés: {result['transmission']['fragments_sent']}")
                print(f"   Durée: {result['transmission'].get('transmission_time', 'N/A')}s")
            else:
                print(f"❌ Échec: {result['transmission'].get('error', 'Unknown error')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"   Détails: {response.text[:200]}...")

    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("💡 Lancez d'abord: dnf-mml-morse server")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python examples/api_client.py <file_path>")
        sys.exit(1)

    transmit_file(sys.argv[1])
