# Makefile pour DNF-MML-Morse

.PHONY: help install test lint format clean build docs demo ci

# Couleurs pour les messages
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Afficher cette aide
	@echo "$(BLUE)DNF-MML-Morse - Outil de développement$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Installer les dépendances
	@echo "$(BLUE)Installation des dépendances...$(NC)"
	pip install -r requirements.txt
	pip install -e .
	@echo "$(GREEN)Installation terminée.$(NC)"

install-dev: ## Installer les dépendances de développement
	@echo "$(BLUE)Installation des dépendances de développement...$(NC)"
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio black isort flake8 mypy sphinx sphinx-rtd-theme
	pip install -e .
	@echo "$(GREEN)Installation terminée.$(NC)"

test: ## Exécuter tous les tests
	@echo "$(BLUE)Exécution des tests...$(NC)"
	pytest tests/ -v --tb=short

test-unit: ## Exécuter les tests unitaires uniquement
	@echo "$(BLUE)Exécution des tests unitaires...$(NC)"
	pytest tests/ -v --tb=short -m "not integration"

test-integration: ## Exécuter les tests d'intégration
	@echo "$(BLUE)Exécution des tests d'intégration...$(NC)"
	pytest tests/test_integration.py -v --tb=short

test-coverage: ## Exécuter les tests avec couverture
	@echo "$(BLUE)Exécution des tests avec couverture...$(NC)"
	pytest --cov=src/dnf_mml_morse --cov-report=html --cov-report=term-missing

lint: ## Vérifier le code avec flake8
	@echo "$(BLUE)Vérification du code...$(NC)"
	flake8 src/dnf_mml_morse tests --max-line-length=127 --max-complexity=10
	@echo "$(GREEN)Linting terminé.$(NC)"

type-check: ## Vérifier les types avec mypy
	@echo "$(BLUE)Vérification des types...$(NC)"
	mypy src/dnf_mml_morse --ignore-missing-imports
	@echo "$(GREEN)Vérification des types terminée.$(NC)"

format: ## Formatter le code avec black et isort
	@echo "$(BLUE)Formatage du code...$(NC)"
	black src/dnf_mml_morse tests
	isort src/dnf_mml_morse tests
	@echo "$(GREEN)Formatage terminé.$(NC)"

format-check: ## Vérifier le formatage sans modifier
	@echo "$(BLUE)Vérification du formatage...$(NC)"
	black --check --diff src/dnf_mml_morse tests
	isort --check-only --diff src/dnf_mml_morse tests

quality: lint type-check format-check test ## Vérifier la qualité globale du code

clean: ## Nettoyer les fichiers temporaires
	@echo "$(BLUE)Nettoyage...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	@echo "$(GREEN)Nettoyage terminé.$(NC)"

build: ## Construire le package
	@echo "$(BLUE)Construction du package...$(NC)"
	python -m build
	@echo "$(GREEN)Package construit.$(NC)"

demo: ## Lancer la démonstration
	@echo "$(BLUE)Lancement de la démonstration...$(NC)"
	python demo_simple.py

demo-full: ## Lancer la démonstration complète
	@echo "$(BLUE)Lancement de la démonstration complète...$(NC)"
	python demo.py

docs: ## Générer la documentation (si configuré)
	@echo "$(YELLOW)Documentation non configurée pour le moment.$(NC)"
	@echo "Utilisez: sphinx-build docs/ docs/_build/html"

ci: ## Simuler CI local
	@echo "$(BLUE)Simulation CI locale...$(NC)"
	make clean
	make install-dev
	make quality
	make build
	@echo "$(GREEN)CI locale terminée avec succès.$(NC)"

# Commandes de développement rapide
dev-setup: install-dev format quality ## Configuration complète pour le développement

run-tests: test-coverage ## Exécuter tous les tests avec couverture

# Commandes pour les exemples
example-html: ## Traiter l'exemple HTML
	@echo "$(BLUE)Traitement de l'exemple HTML...$(NC)"
	python -c "
import asyncio
from src.dnf_mml_morse.core import DNFMMLMorseSystem
system = DNFMMLMorseSystem()
result = asyncio.run(system.transmit_document('examples/sample.html', 'TEST'))
print(f'Succès: {result[\"success\"]}')
print(f'Ratio compression: {result[\"compression_ratio\"]:.2%}')
	"

example-md: ## Traiter l'exemple Markdown
	@echo "$(BLUE)Traitement de l'exemple Markdown...$(NC)"
	python -c "
import asyncio
from src.dnf_mml_morse.core import DNFMMLMorseSystem
system = DNFMMLMorseSystem()
result = asyncio.run(system.transmit_document('examples/sample.md', 'TEST'))
print(f'Succès: {result[\"success\"]}')
print(f'Ratio compression: {result[\"compression_ratio\"]:.2%}')
	"

# Aide pour les tâches courantes
setup: ## Configuration initiale du projet
	@echo "$(BLUE)Configuration initiale du projet DNF-MML-Morse$(NC)"
	@echo "1. Assurez-vous que Python 3.8+ est installé"
	@echo "2. Exécutez: make install-dev"
	@echo "3. Exécutez: make quality"
	@echo "4. Exécutez: make demo"
	@echo "$(GREEN)Prêt pour le développement !$(NC)"

# Informations système
info: ## Afficher les informations système
	@echo "$(BLUE)Informations système:$(NC)"
	@python --version
	@pip --version
	@echo ""
	@echo "$(BLUE)Dépendances installées:$(NC)"
	@pip list | grep -E "(pytest|black|flake8|mypy|coverage)" || echo "Aucune dépendance de développement trouvée"

# Raccourcis
check: quality ## Alias pour quality
fmt: format ## Alias pour format
tc: type-check ## Alias pour type-check
