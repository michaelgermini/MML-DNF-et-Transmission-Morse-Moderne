#!/usr/bin/env python3
"""
Démonstration du mode streaming DNF-MML-Morse

Montre comment traiter des documents volumineux en mode streaming
sans charger tout le contenu en mémoire.
"""

import sys
import tempfile
import os
from pathlib import Path

# Ajout du répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def create_large_test_file(size_mb: int = 5) -> str:
    """Crée un fichier de test volumineux"""
    # Créer du contenu répétitif pour simuler un gros document
    base_content = """
    <html>
    <head><title>Document volumineux de test</title></head>
    <body>
        <h1>Document volumineux pour test streaming</h1>
        <p>Ceci est un paragraphe de test qui sera répété de nombreuses fois pour créer un document volumineux.</p>
        <ul>
            <li>Item de liste 1</li>
            <li>Item de liste 2</li>
            <li>Item de liste 3</li>
        </ul>
        <p>Plus de contenu ici pour augmenter la taille du document de test.</p>
        <div>
            <h2>Sous-section</h2>
            <p>Contenu de la sous-section avec du texte supplémentaire pour atteindre la taille désirée.</p>
        </div>
    </body>
    </html>
    """

    # Répéter pour atteindre la taille désirée
    repetitions = max(1, (size_mb * 1024 * 1024) // len(base_content))
    large_content = base_content * repetitions

    # Créer fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(large_content)
        return f.name

async def demo_streaming_analysis():
    """Démonstration de l'analyse de fichiers pour streaming"""
    print("[ANALYSE] Analyse de fichiers pour streaming")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    system = DNFMMLMorseSystem()

    # Créer des fichiers de test de différentes tailles
    test_files = []

    for size_mb in [0.1, 1, 5, 10]:
        file_path = create_large_test_file(size_mb)
        test_files.append((file_path, size_mb))

        analysis = await system.analyze_file_for_streaming(file_path)

        print(f"Fichier {size_mb}MB:")
        print(f"  Taille: {analysis['file_analysis']['file_size_mb']:.1f} MB")
        print(f"  Chunks estimés: {analysis['file_analysis']['estimated_chunks']}")
        print(f"  Streaming recommandé: {analysis['recommended_method']}")
        print()

    # Nettoyer
    for file_path, _ in test_files:
        os.unlink(file_path)

async def demo_streaming_transmission():
    """Démonstration de transmission en streaming"""
    print("[STREAMING] Transmission en mode streaming")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    # Configuration avec streaming activé
    config = {
        'streaming_enabled': True,
        'streaming_chunk_size': 4096,  # Petits chunks pour la démo
        'streaming_max_memory_mb': 10,
        'streaming_threshold_mb': 0.5,  # Seuil bas pour la démo
    }

    system = DNFMMLMorseSystem(config)

    # Créer un fichier de test
    test_file = create_large_test_file(2)  # 2MB

    try:
        print(f"Traitement du fichier: {test_file}")
        print(f"Taille: {os.path.getsize(test_file) / (1024*1024):.1f} MB")

        # Transmission en streaming
        result = await system.transmit_file_streaming(test_file, "STREAM_DEMO")

        print("
Resultats de transmission:")
        print(f"  Succès: {result['success']}")
        print(f"  Méthode: {result['method']}")
        print(f"  Fragments: {result.get('chunks_processed', 'N/A')}")
        print(f"  Stats: {result.get('stats', {})}")

    finally:
        os.unlink(test_file)

def demo_streaming_status():
    """Démonstration de l'état du système de streaming"""
    print("[STATUS] État du système de streaming")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    # Système avec streaming
    system_streaming = DNFMMLMorseSystem({'streaming_enabled': True})
    status_streaming = await system_streaming.get_streaming_status()

    print("Système avec streaming activé:")
    print(f"  Streaming activé: {status_streaming['streaming_enabled']}")
    print(f"  Sessions actives: {len(status_streaming.get('active_sessions', []))}")
    print(f"  Chunk size: {status_streaming['config']['chunk_size']}")
    print(f"  Mémoire max: {status_streaming['config']['max_memory_mb']} MB")
    print()

    # Système sans streaming
    system_no_streaming = DNFMMLMorseSystem({'streaming_enabled': False})
    status_no_streaming = await system_no_streaming.get_streaming_status()

    print("Système avec streaming désactivé:")
    print(f"  Streaming activé: {status_no_streaming['streaming_enabled']}")

async def demo_auto_mode_selection():
    """Démonstration de la sélection automatique du mode"""
    print("[AUTO] Sélection automatique du mode de traitement")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    system = DNFMMLMorseSystem({
        'streaming_enabled': True,
        'streaming_threshold_mb': 1,  # 1MB seuil
    })

    # Tester différents fichiers
    test_cases = [
        (0.1, "Petit fichier"),
        (2, "Fichier moyen"),
        (5, "Gros fichier"),
    ]

    for size_mb, description in test_cases:
        test_file = create_large_test_file(size_mb)

        try:
            should_stream = system.should_use_streaming(test_file)
            file_size_mb = os.path.getsize(test_file) / (1024 * 1024)

            print(f"{description} ({file_size_mb:.1f} MB): {'STREAMING' if should_stream else 'DIRECT'}")

        finally:
            os.unlink(test_file)

def demo_memory_efficiency():
    """Démonstration de l'efficacité mémoire"""
    print("[MEMORY] Efficacité mémoire du streaming")
    print("=" * 60)

    print("Avantages du mode streaming:")
    print("• Traitement par chunks sans charger tout le fichier")
    print("• Mémoire constante indépendamment de la taille du fichier")
    print("• Traitement possible de fichiers très volumineux")
    print("• Reprise possible en cas d'interruption")
    print()

    print("Configuration recommandée:")
    print("• Chunk size: 4-8 KB pour l'équilibre performance/mémoire")
    print("• Buffer size: 2-4 chunks pour lisser les variations")
    print("• Seuil streaming: 1-5 MB selon la mémoire disponible")
    print("• Mémoire max: 10-50% de la RAM disponible")

async def main():
    """Fonction principale de démonstration"""
    print(">>> Démonstration du mode streaming - DNF-MML-Morse")
    print("=" * 80)
    print()

    try:
        await demo_streaming_analysis()
        await demo_streaming_transmission()
        await demo_streaming_status()
        await demo_auto_mode_selection()
        demo_memory_efficiency()

        print("\n[SUCCESS] Démonstration streaming terminée!")
        print()
        print("💡 Le mode streaming permet de traiter des documents volumineux:")
        print("   • Sans limitation de taille mémoire")
        print("   • Avec performance constante")
        print("   • En préservant la réactivité")
        print("   • Avec reprise automatique possible")

    except Exception as e:
        print(f"[ERROR] Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
