#!/usr/bin/env python3
"""
Hook de pré-commit pour DNF-MML-Morse

Vérifie automatiquement la qualité du code avant chaque commit.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} réussi")
            return True
        else:
            print(f"❌ {description} échoué:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Erreur lors de {description}: {e}")
        return False


def main():
    """Fonction principale du pré-commit"""
    print("🔒 Pré-commit hook - DNF-MML-Morse")
    print("=" * 50)

    # Vérifier que nous sommes dans un dépôt git
    if not Path('.git').exists():
        print("❌ Pas dans un dépôt git")
        return 1

    success = True

    # 1. Vérifier le formatage avec black
    if not run_command("black --check --quiet src/dnf_mml_morse tests", "Vérification du formatage (black)"):
        print("💡 Exécutez: make format")
        success = False

    # 2. Vérifier les imports avec isort
    if not run_command("isort --check-only --quiet src/dnf_mml_morse tests", "Vérification des imports (isort)"):
        print("💡 Exécutez: make format")
        success = False

    # 3. Vérifier le linting avec flake8
    if not run_command("flake8 src/dnf_mml_morse tests --max-line-length=127 --max-complexity=10", "Vérification du code (flake8)"):
        print("💡 Corrigez les erreurs de linting")
        success = False

    # 4. Vérifier les types avec mypy (optionnel, peut échouer)
    mypy_result = run_command("mypy src/dnf_mml_morse --ignore-missing-imports", "Vérification des types (mypy)")
    if not mypy_result:
        print("⚠️ Erreurs de types détectées (non bloquant)")

    # 5. Exécuter les tests rapides
    if not run_command("pytest tests/ -x --tb=short -q", "Exécution des tests"):
        print("💡 Corrigez les tests qui échouent")
        success = False

    # Résumé
    print("\n" + "=" * 50)
    if success:
        print("🎉 Toutes les vérifications passées ! Commit autorisé.")
        return 0
    else:
        print("❌ Des vérifications ont échoué. Corrigez les erreurs avant de committer.")
        print("\nCommandes utiles:")
        print("  make quality    # Vérifier la qualité")
        print("  make format     # Formatter le code")
        print("  make test       # Exécuter les tests")
        return 1


if __name__ == '__main__':
    sys.exit(main())
