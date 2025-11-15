#!/usr/bin/env python3
"""
Démonstration de l'API REST/WebSocket DNF-MML-Morse

Montre comment utiliser l'API pour transmettre des documents
via des requêtes HTTP.
"""

import sys
import json
import time
from pathlib import Path

# Ajout du répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def demo_api_client():
    """Démonstration d'un client API simple"""
    print("🌐 Démonstration du client API DNF-MML-Morse")
    print("=" * 60)

    try:
        import requests
    except ImportError:
        print("❌ requests requis: pip install requests")
        return

    # Configuration
    base_url = "http://localhost:8000"
    test_file = "examples/sample.html"

    if not Path(test_file).exists():
        print(f"❌ Fichier de test manquant: {test_file}")
        return

    print(f"📡 Serveur API: {base_url}")
    print(f"📄 Fichier de test: {test_file}")
    print()

    # Test 1: Vérification de santé
    print("1️⃣ Test de santé du système...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("   ✅ Serveur opérationnel"            print(f"   📊 Requêtes API: {health['api_stats']['requests_total']}")
            print(f"   🔄 Status système: {health['system']['status']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Impossible de se connecter au serveur")
        print("   💡 Lancez d'abord: dnf-mml-morse server")
        return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    print()

    # Test 2: Analyse de fichier
    print("2️⃣ Analyse du fichier de test...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (Path(test_file).name, f, 'text/html')}
            response = requests.post(f"{base_url}/api/analyze", files=files, timeout=10)

        if response.status_code == 200:
            analysis = response.json()
            print("   ✅ Analyse réussie"            print(f"   📏 Taille: {analysis['file_info']['size_mb']:.2f} MB")
            print(f"   🎯 Méthode recommandée: {analysis['analysis']['recommended_method']}")
            print(f"   📊 Streaming: {analysis['analysis']['file_analysis']['streaming_recommended']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print()

    # Test 3: Transmission
    print("3️⃣ Transmission du document...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (Path(test_file).name, f, 'text/html')}
            data = {'destination': 'API_CLIENT', 'use_streaming': False}
            response = requests.post(f"{base_url}/api/transmit", files=files, data=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("   ✅ Transmission réussie!"                trans = result['transmission']
                print(f"   📏 Taille originale: {trans['original_size']} octets")
                print(f"   🗜️ Ratio compression: {trans['compression_ratio']:.2%}")
                print(f"   📡 Fragments: {trans['fragments_sent']}")
                print(f"   🎯 Destination: {trans['destination']}")
                print(f"   ⏱️ Durée: {trans.get('transmission_time', 'N/A')}s")
            else:
                print(f"   ❌ Échec: {result['transmission'].get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   📄 Réponse: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print()

    # Test 4: Status du système
    print("4️⃣ État du système après transmission...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("   ✅ Status récupéré"            print(f"   🔄 État: {status['system']['status']}")
            print(f"   📊 Requêtes totales: {status['api']['requests_total']}")
            print(f"   📤 Transmissions: {status['api']['transmissions_total']}")
            if status.get('streaming'):
                print(f"   🌊 Sessions actives: {len(status['streaming'].get('active_sessions', []))}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print()

    # Test 5: Données de démonstration
    print("5️⃣ Récupération des données de démo...")
    try:
        response = requests.get(f"{base_url}/api/demo", timeout=5)
        if response.status_code == 200:
            demo = response.json()
            print("   ✅ Données de démo récupérées")

            # Afficher quelques exemples
            if 'sample_transmission' in demo:
                sample = demo['sample_transmission']
                print(f"   📝 Texte: {sample['text']}")
                print(f"   📡 Morse: {sample['morse_standard'][:30]}...")

            if 'unicode_examples' in demo:
                unicode_ex = demo['unicode_examples']
                print(f"   🌍 Unicode: {unicode_ex['mixed']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    print()
    print("🎉 Démonstration API terminée!")

def demo_api_server_quick():
    """Démonstration rapide du lancement du serveur"""
    print("\n🚀 Pour lancer le serveur API:")
    print("   dnf-mml-morse server --host 0.0.0.0 --port 8000")
    print()
    print("📖 Puis accéder à:")
    print("   🌐 Interface web: http://localhost:8000")
    print("   📚 Documentation: http://localhost:8000/docs")
    print("   🔄 Alternative: http://localhost:8000/redoc")

def create_test_client_script():
    """Créer un script client de test"""
    client_script = '''#!/usr/bin/env python3
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

    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
        data = {'destination': 'TEST_CLIENT'}

        response = requests.post(f"{server_url}/api/transmit", files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print("✅ Transmission réussie!")
            print(f"   Ratio compression: {result['transmission']['compression_ratio']:.2%}")
        else:
            print(f"❌ Échec: {result['transmission'].get('error')}")
    else:
        print(f"❌ Erreur HTTP: {response.status_code}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python api_client.py <file_path>")
        sys.exit(1)

    transmit_file(sys.argv[1])
'''

    with open('examples/api_client.py', 'w') as f:
        f.write(client_script)

    print("\n📄 Script client créé: examples/api_client.py")
    print("   Usage: python examples/api_client.py <votre_fichier>")

def main():
    """Fonction principale"""
    print("🌐 Démonstration de l'API DNF-MML-Morse")
    print("=" * 80)
    print()

    # Vérifier si le serveur est accessible
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        server_running = response.status_code == 200
    except:
        server_running = False

    if not server_running:
        print("⚠️ Le serveur API n'est pas accessible sur localhost:8000")
        print()
        demo_api_server_quick()
        create_test_client_script()
        return

    # Lancer la démonstration client
    demo_api_client()
    create_test_client_script()

if __name__ == '__main__':
    main()
