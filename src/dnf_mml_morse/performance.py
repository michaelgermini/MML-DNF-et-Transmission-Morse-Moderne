"""
Module d'optimisation des performances pour DNF-MML-Morse

Implémente la parallélisation, le cache intelligent,
et les optimisations mémoire pour améliorer les performances.
"""

import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache, wraps
from typing import Dict, Any, List, Optional, Callable, TypeVar, Union
import threading
import psutil
import gc
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Types génériques
T = TypeVar('T')
F = TypeVar('F', bound=Callable)


class PerformanceMonitor:
    """
    Moniteur de performances avec métriques détaillées
    """

    def __init__(self):
        self.metrics = {
            'operation_count': 0,
            'total_time': 0.0,
            'peak_memory': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'parallel_tasks': 0,
            'errors': 0,
        }
        self.operations: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def start_operation(self, name: str) -> 'OperationTimer':
        """Démarre le chronométrage d'une opération"""
        return OperationTimer(self, name)

    def record_metric(self, name: str, value: Union[int, float]):
        """Enregistre une métrique"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = 0
            if isinstance(value, (int, float)):
                self.metrics[name] += value

    def record_operation_time(self, name: str, duration: float):
        """Enregistre le temps d'une opération"""
        with self._lock:
            if name not in self.operations:
                self.operations[name] = []
            self.operations[name].append(duration)
            self.metrics['operation_count'] += 1
            self.metrics['total_time'] += duration

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        with self._lock:
            stats = self.metrics.copy()

            # Statistiques par opération
            operation_stats = {}
            for op_name, times in self.operations.items():
                if times:
                    operation_stats[op_name] = {
                        'count': len(times),
                        'total_time': sum(times),
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times),
                    }

            stats['operations'] = operation_stats

            # Taux de succès du cache
            total_cache = stats['cache_hits'] + stats['cache_misses']
            if total_cache > 0:
                stats['cache_hit_rate'] = stats['cache_hits'] / total_cache
            else:
                stats['cache_hit_rate'] = 0.0

            # Performance globale
            if stats['operation_count'] > 0:
                stats['avg_operation_time'] = stats['total_time'] / stats['operation_count']
            else:
                stats['avg_operation_time'] = 0.0

            return stats

    def reset(self):
        """Remet à zéro les métriques"""
        with self._lock:
            self.metrics.clear()
            self.operations.clear()
            self.metrics.update({
                'operation_count': 0,
                'total_time': 0.0,
                'peak_memory': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'parallel_tasks': 0,
                'errors': 0,
            })


class OperationTimer:
    """Chronomètreur d'opération avec contexte"""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.monitor.record_operation_time(self.operation_name, duration)


class SmartCache:
    """
    Cache intelligent avec gestion automatique de la mémoire
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialisation du cache intelligent

        Args:
            max_size: Taille maximale du cache
            ttl_seconds: Durée de vie des entrées (Time To Live)
        """
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []
        self._lock = threading.Lock()

    def _get_key(self, *args, **kwargs) -> str:
        """Génère une clé de cache unique"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]

                # Vérifier TTL
                if time.time() - entry['timestamp'] > self.ttl:
                    self._remove(key)
                    return None

                # Mettre à jour l'ordre d'accès (LRU)
                self.access_order.remove(key)
                self.access_order.append(key)

                return entry['value']
            return None

    def put(self, key: str, value: Any):
        """Stocke une valeur dans le cache"""
        with self._lock:
            # Éviction si nécessaire
            if key not in self.cache and len(self.cache) >= self.max_size:
                self._evict_lru()

            # Stocker la valeur
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
            }

            # Mettre à jour l'ordre d'accès
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

    def _evict_lru(self):
        """Évite l'entrée la moins récemment utilisée"""
        if self.access_order:
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]

    def _remove(self, key: str):
        """Supprime une entrée du cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)

    def clear(self):
        """Vide le cache"""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()

    def stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        with self._lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': 0.0,  # À calculer avec un compteur d'accès
                'ttl_seconds': self.ttl,
            }


class ParallelProcessor:
    """
    Processeur parallèle pour tâches CPU-intensives
    """

    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        Initialisation du processeur parallèle

        Args:
            max_workers: Nombre maximum de workers (défaut: CPU count)
            use_processes: Utiliser des processus au lieu de threads
        """
        self.max_workers = max_workers or min(32, (psutil.cpu_count() or 4) * 2)
        self.use_processes = use_processes

        # Executor pool
        self._executor = None
        self._lock = threading.Lock()

    def _get_executor(self):
        """Obtient ou crée l'executor"""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    if self.use_processes:
                        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
                    else:
                        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._executor

    async def run_parallel(self, tasks: List[Callable], *args) -> List[Any]:
        """
        Exécute des tâches en parallèle

        Args:
            tasks: Liste des fonctions à exécuter
            *args: Arguments passés à chaque fonction

        Returns:
            Résultats des tâches
        """
        if not tasks:
            return []

        loop = asyncio.get_event_loop()
        executor = self._get_executor()

        # Créer les tâches
        futures = [
            loop.run_in_executor(executor, task, *args)
            for task in tasks
        ]

        # Attendre tous les résultats
        results = await asyncio.gather(*futures, return_exceptions=True)

        # Traiter les exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erreur dans tâche parallèle {i}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)

        return processed_results

    async def run_batch(self, func: Callable, items: List[Any],
                       batch_size: int = 10) -> List[Any]:
        """
        Traite une liste d'éléments par batches

        Args:
            func: Fonction à appliquer
            items: Liste d'éléments
            batch_size: Taille des batches

        Returns:
            Résultats traités
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # Traiter le batch en parallèle
            batch_results = await self.run_parallel([func] * len(batch), batch)
            results.extend(batch_results)

        return results

    def shutdown(self):
        """Arrête l'executor"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None


class MemoryOptimizer:
    """
    Optimiseur de mémoire avec gestion automatique du GC
    """

    def __init__(self, memory_threshold_mb: int = 500, gc_threshold: int = 1000):
        """
        Initialisation de l'optimiseur mémoire

        Args:
            memory_threshold_mb: Seuil de mémoire pour déclencher l'optimisation
            gc_threshold: Seuil pour le garbage collector
        """
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  # Convertir en bytes
        self.gc_threshold = gc_threshold

        # Statistiques
        self.memory_peaks = []
        self.gc_cycles = 0

    def should_optimize(self) -> bool:
        """Vérifie si une optimisation mémoire est nécessaire"""
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss

            self.memory_peaks.append(memory_usage)

            return memory_usage > self.memory_threshold
        except:
            return False

    def optimize_memory(self):
        """Optimise l'utilisation mémoire"""
        # Forcer le garbage collection
        collected = gc.collect()
        self.gc_cycles += 1

        # Collecter les objets non référencés
        gc.collect(1)  # Générations plus jeunes
        gc.collect(2)  # Toutes les générations

        logger.debug(f"Optimisation mémoire: {collected} objets collectés")

    def force_gc(self):
        """Force un cycle complet de garbage collection"""
        # Ajuster les seuils du GC
        gc.set_threshold(self.gc_threshold, 10, 10)

        # Forcer la collection
        collected = gc.collect()

        # Restaurer les seuils par défaut
        gc.set_threshold(gc.get_threshold()[0], gc.get_threshold()[1], gc.get_threshold()[2])

        logger.debug(f"GC forcé: {collected} objets collectés")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Statistiques d'utilisation mémoire"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss': memory_info.rss,
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms': memory_info.vms,
                'vms_mb': memory_info.vms / (1024 * 1024),
                'peak_rss': max(self.memory_peaks) if self.memory_peaks else 0,
                'gc_cycles': self.gc_cycles,
                'gc_objects': len(gc.get_objects()),
            }
        except:
            return {'error': 'Impossible de récupérer les stats mémoire'}


# Décorateurs pour l'optimisation

def cached(max_size: int = 128, ttl_seconds: int = 300):
    """
    Décorateur de cache avec TTL

    Args:
        max_size: Taille maximale du cache
        ttl_seconds: Durée de vie des entrées
    """
    cache = SmartCache(max_size=max_size, ttl_seconds=ttl_seconds)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            key = cache._get_key(*args, **kwargs)

            # Vérifier le cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Exécuter la fonction
            result = func(*args, **kwargs)

            # Mettre en cache
            cache.put(key, result)

            return result

        return wrapper
    return decorator


def timed(monitor: Optional[PerformanceMonitor] = None):
    """
    Décorateur pour mesurer le temps d'exécution

    Args:
        monitor: Moniteur de performance (optionnel)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal monitor
            if monitor is None:
                monitor = PerformanceMonitor()

            operation_name = f"{func.__module__}.{func.__qualname__}"

            with monitor.start_operation(operation_name):
                result = func(*args, **kwargs)

            return result

        return wrapper
    return decorator


def memory_optimized(optimizer: Optional[MemoryOptimizer] = None):
    """
    Décorateur pour optimisation mémoire

    Args:
        optimizer: Optimiseur mémoire (optionnel)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal optimizer
            if optimizer is None:
                optimizer = MemoryOptimizer()

            # Vérifier si optimisation nécessaire avant
            if optimizer.should_optimize():
                optimizer.optimize_memory()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Vérifier si optimisation nécessaire après
                if optimizer.should_optimize():
                    optimizer.force_gc()

        return wrapper
    return decorator


# Gestionnaire global de performance
global_monitor = PerformanceMonitor()
global_cache = SmartCache(max_size=500, ttl_seconds=1800)  # 30 minutes TTL
global_parallel = ParallelProcessor()
global_memory = MemoryOptimizer()


@asynccontextmanager
async def performance_context():
    """
    Contexte de performance avec monitoring automatique

    Usage:
        async with performance_context():
            # Code à mesurer
            pass
    """
    monitor = PerformanceMonitor()
    start_stats = monitor.get_stats()

    try:
        yield monitor
    finally:
        end_stats = monitor.get_stats()

        # Log des métriques
        if end_stats['operation_count'] > 0:
            logger.info(f"Performance: {end_stats['operation_count']} opérations, "
                       f"{end_stats['total_time']:.3f}s total, "
                       f"{end_stats['avg_operation_time']:.3f}s/opération")


def optimize_for_large_files(file_size: int) -> Dict[str, Any]:
    """
    Recommande des optimisations pour un fichier donné

    Args:
        file_size: Taille du fichier en bytes

    Returns:
        Configuration optimisée
    """
    size_mb = file_size / (1024 * 1024)

    config = {
        'use_streaming': False,
        'chunk_size': 8192,
        'max_memory_mb': 100,
        'parallel_processing': False,
        'cache_enabled': True,
    }

    if size_mb > 10:  # > 10MB
        config.update({
            'use_streaming': True,
            'chunk_size': 65536,  # 64KB chunks
            'max_memory_mb': 200,
            'parallel_processing': True,
        })
    elif size_mb > 1:  # > 1MB
        config.update({
            'use_streaming': True,
            'chunk_size': 32768,  # 32KB chunks
            'max_memory_mb': 150,
        })

    return config


# Fonctions utilitaires de performance

async def run_with_timeout(coro, timeout_seconds: float = 30.0):
    """
    Exécute une coroutine avec timeout

    Args:
        coro: Coroutine à exécuter
        timeout_seconds: Timeout en secondes

    Returns:
        Résultat ou None si timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout après {timeout_seconds}s")
        return None


def get_system_performance_info() -> Dict[str, Any]:
    """
    Informations de performance du système

    Returns:
        Métriques système
    """
    try:
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu': {
                'count': cpu_count,
                'usage_percent': cpu_percent,
            },
            'memory': {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'usage_percent': memory.percent,
            },
            'disk': {
                'total_gb': disk.total / (1024**3),
                'free_gb': disk.free / (1024**3),
                'usage_percent': disk.percent,
            },
        }
    except:
        return {'error': 'Impossible de récupérer les infos système'}
