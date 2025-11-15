#!/usr/bin/env python3
"""
Démonstration des optimisations de performance DNF-MML-Morse

Montre le cache intelligent, la parallélisation,
et les optimisations mémoire.
"""

import sys
import time
import tempfile
import os
from pathlib import Path

# Ajout du répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def create_test_files(count: int = 5, size_kb: int = 50) -> List[str]:
    """Crée plusieurs fichiers de test"""
    files = []

    base_content = """
    <html>
    <head><title>Document de test</title></head>
    <body>
        <h1>Titre du document</h1>
        <p>Ceci est un paragraphe de test avec du contenu répétitif pour simuler un document réel avec suffisamment de texte pour les tests de performance et compression.</p>
        <ul>
            <li>Premier élément de liste</li>
            <li>Deuxième élément de liste</li>
            <li>Troisième élément de liste</li>
        </ul>
        <p>Plus de contenu ici pour atteindre la taille souhaitée du fichier de test. Ce texte est répété plusieurs fois.</p>
    </body>
    </html>
    """

    # Répéter pour atteindre la taille souhaitée
    repetitions = max(1, (size_kb * 1024) // len(base_content))
    content = base_content * repetitions

    for i in range(count):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(content)
            files.append(f.name)

    return files

async def demo_caching():
    """Démonstration du cache intelligent"""
    print("[CACHE] Démonstration du cache intelligent")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    system = DNFMMLMorseSystem({'cache_enabled': True})

    # Créer un fichier de test
    test_files = create_test_files(1, 20)
    test_file = test_files[0]

    try:
        print(f"Fichier de test: {test_file}")

        # Première transmission (sans cache)
        print("Première transmission (cache vide)...")
        start_time = time.time()
        result1 = await system.transmit_document(test_file)
        time1 = time.time() - start_time

        # Deuxième transmission (avec cache)
        print("Deuxième transmission (avec cache)...")
        start_time = time.time()
        result2 = await system.transmit_document(test_file)
        time2 = time.time() - start_time

        print("
Resultats:")
        print(f"  Première transmission: {time1:.3f}s")
        print(f"  Deuxième transmission: {time2:.3f}s")
        print(f"  Accélération: {time1/time2:.1f}x plus rapide")
        print(f"  Cache utilisé: {'Oui' if time2 < time1 * 0.8 else 'Non perceptible'}")

        # Statistiques du cache
        cache_stats = system.cache.stats()
        print(f"\nStatistiques cache:")
        print(f"  Taille: {cache_stats['size']}/{cache_stats['max_size']}")
        print(f"  TTL: {cache_stats['ttl_seconds']}s")

    finally:
        os.unlink(test_file)

async def demo_parallel_processing():
    """Démonstration du traitement parallèle"""
    print("\n[PARALLEL] Démonstration du traitement parallèle")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    # Système avec parallélisation
    system_parallel = DNFMMLMorseSystem({
        'parallel_processing': True,
        'performance_enabled': True
    })

    # Système sans parallélisation
    system_sequential = DNFMMLMorseSystem({
        'parallel_processing': False,
        'performance_enabled': False
    })

    # Créer plusieurs fichiers de test
    test_files = create_test_files(3, 30)

    try:
        print(f"Traitement de {len(test_files)} fichiers...")

        # Traitement parallèle
        print("Traitement parallèle...")
        start_time = time.time()
        parallel_results = await system_parallel._parallel_convert_documents(test_files)
        parallel_time = time.time() - start_time

        # Traitement séquentiel
        print("Traitement séquentiel...")
        start_time = time.time()
        sequential_results = []
        for file_path in test_files:
            result = await system_sequential.transmit_document(file_path)
            sequential_results.append(result)
        sequential_time = time.time() - start_time

        print("
Resultats:")
        print(f"  Séquentiel: {sequential_time:.3f}s")
        print(f"  Parallèle: {parallel_time:.3f}s")
        print(f"  Accélération: {sequential_time/parallel_time:.1f}x plus rapide")

        success_count = sum(1 for r in parallel_results if r.get('success'))
        print(f"  Succès parallèles: {success_count}/{len(parallel_results)}")

    finally:
        for file_path in test_files:
            os.unlink(file_path)

def demo_memory_optimization():
    """Démonstration de l'optimisation mémoire"""
    print("\n[MEMORY] Démonstration de l'optimisation mémoire")
    print("=" * 60)

    from dnf_mml_morse.performance import MemoryOptimizer

    optimizer = MemoryOptimizer(memory_threshold_mb=50)

    print("Création d'objets pour simuler utilisation mémoire...")

    # Simuler utilisation mémoire
    big_objects = []
    for i in range(10):
        big_objects.append("x" * 1024 * 1024)  # 1MB chacun
        print(f"  Créé objet {i+1} (mémoire cumulée: {len(big_objects)} MB)")

        # Vérifier si optimisation nécessaire
        if optimizer.should_optimize():
            print(f"  Seuil mémoire dépassé, optimisation déclenchée...")
            optimizer.optimize_memory()

    print("
Nettoyage mémoire...")
    del big_objects
    optimizer.force_gc()

    # Statistiques finales
    stats = optimizer.get_memory_stats()
    print("
Statistiques mémoire:")
    print(f"  RSS: {stats.get('rss_mb', 'N/A'):.1f} MB")
    print(f"  Pic RSS: {stats.get('peak_rss', 0) / (1024*1024):.1f} MB")
    print(f"  Cycles GC: {optimizer.gc_cycles}")

async def demo_performance_monitoring():
    """Démonstration du monitoring de performance"""
    print("\n[MONITORING] Démonstration du monitoring de performance")
    print("=" * 60)

    from dnf_mml_morse.core import DNFMMLMorseSystem

    system = DNFMMLMorseSystem({'performance_enabled': True})

    # Activer le monitoring
    system.enable_performance_monitoring()

    # Créer et traiter un fichier
    test_files = create_test_files(1, 25)
    test_file = test_files[0]

    try:
        print("Traitement avec monitoring activé...")

        # Effectuer plusieurs transmissions
        for i in range(3):
            await system.transmit_document(test_file)
            print(f"  Transmission {i+1} terminée")

        # Récupérer les statistiques
        stats = system.get_performance_stats()

        print("
Statistiques de performance:")
        perf_stats = stats['system_performance']
        print(f"  Opérations: {perf_stats['operation_count']}")
        print(f"  Temps total: {perf_stats['total_time']:.3f}s")
        print(f"  Temps moyen/opération: {perf_stats['avg_operation_time']:.3f}s")

        # Statistiques par opération
        if 'operations' in perf_stats:
            print("
Détail par opération:")
            for op_name, op_stats in perf_stats['operations'].items():
                print(f"  {op_name}: {op_stats['count']} ops, {op_stats['avg_time']:.3f}s/op")

        # Statistiques cache
        cache_stats = stats['cache_stats']
        print(f"\nCache: {cache_stats['size']}/{cache_stats['max_size']} entrées")

        # Statistiques mémoire
        mem_stats = stats['memory_stats']
        if 'rss_mb' in mem_stats:
            print(f"Mémoire: {mem_stats['rss_mb']:.1f} MB RSS")

    finally:
        os.unlink(test_file)

def demo_system_performance():
    """Démonstration des performances système"""
    print("\n[SYSTEM] Informations de performance système")
    print("=" * 60)

    from dnf_mml_morse.performance import get_system_performance_info

    info = get_system_performance_info()

    if 'error' in info:
        print(f"Erreur récupération infos système: {info['error']}")
        return

    print("CPU:")
    print(f"  Cœurs: {info['cpu']['count']}")
    print(f"  Utilisation: {info['cpu']['usage_percent']:.1f}%")

    print("
Mémoire:")
    print(f"  Total: {info['memory']['total_gb']:.1f} GB")
    print(f"  Disponible: {info['memory']['available_gb']:.1f} GB")
    print(f"  Utilisation: {info['memory']['usage_percent']:.1f}%")

    print("
Disque:")
    print(f"  Total: {info['disk']['total_gb']:.1f} GB")
    print(f"  Libre: {info['disk']['free_gb']:.1f} GB")
    print(f"  Utilisation: {info['disk']['usage_percent']:.1f}%")

async def main():
    """Fonction principale de démonstration"""
    print(">>> Démonstration des optimisations de performance - DNF-MML-Morse")
    print("=" * 80)
    print()

    try:
        await demo_caching()
        await demo_parallel_processing()
        demo_memory_optimization()
        await demo_performance_monitoring()
        demo_system_performance()

        print("
[SUCCESS] Démonstration performance terminée!")
        print()
        print("💡 Fonctionnalités de performance implémentées:")
        print("   • Cache intelligent avec TTL et LRU eviction")
        print("   • Traitement parallèle avec pools de workers")
        print("   • Optimisation mémoire avec GC automatique")
        print("   • Monitoring de performance temps réel")
        print("   • Gestion adaptative des ressources système")

    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
