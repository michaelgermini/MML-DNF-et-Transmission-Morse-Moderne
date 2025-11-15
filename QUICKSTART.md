# 🚀 Guide de démarrage rapide - DNF-MML-Morse

Bienvenue dans le système DNF-MML-Morse ! Ce guide vous permet de commencer en quelques minutes.

## Prérequis

- Python 3.8 ou supérieur
- pip pour l'installation

## Installation rapide

```bash
# Cloner ou télécharger le projet
cd dnf-mml-morse

# Installer les dépendances
pip install -r requirements.txt

# Installation en mode développement (optionnel)
pip install -e .
```

## 🧪 Test rapide du système

Lancez le test intégré pour vérifier que tout fonctionne :

```bash
python test_basic.py
```

Vous devriez voir :
```
[OK] Import des modules réussi
[OK] Parser MML: True
[OK] Compresseur: ratio 0.68
[OK] Codec Morse: HELLO
[SUCCESS] Tous les tests de base réussis!
```

## 📝 Premiers pas avec la ligne de commande

### 1. Convertir un document HTML en MML

```bash
# Utiliser le CLI pour convertir
python -m src.dnf_mml_morse.cli convert examples/sample.html --output output.mml
```

### 2. Tester le codec Morse

```bash
# Encoder du texte en Morse
python -c "from src.dnf_mml_morse.morse.codec import encode_morse; print(encode_morse('HELLO WORLD'))"

# Décoder du Morse
python -c "from src.dnf_mml_morse.morse.codec import decode_morse; print(decode_morse('.... . .-.. .-.. --- / .-- --- .-. .-.. -..'))"
```

### 3. Tester la compression MML

```bash
# Compresser du contenu MML
python -c "
from src.dnf_mml_morse.mml.compressor import compress_mml
content = '<H1>Titre</H1><P>Ceci est un paragraphe de test assez long pour démontrer la compression.</P>'
result = compress_mml(content)
print(f'Ratio de compression: {result[\"compression_ratio\"]:.2f}')
print(f'Contenu compressé: {result[\"content\"][:50]}...')
"
```

## 🔄 Pipeline complet : HTML → MML → Compression → Morse

Voici un exemple complet de traitement d'un document :

```python
import asyncio
from src.dnf_mml_morse.core import DNFMMLMorseSystem

async def demo_pipeline():
    # Configuration
    config = {
        'morse_mode': 'optimized',
        'transport': 'cw',
        'callsign': 'F6ABC',
        'compression_level': 'standard'
    }

    # Initialisation du système
    system = DNFMMLMorseSystem(config)

    # Transmission d'un document
    result = await system.transmit_document('examples/sample.html', destination='F6XYZ')

    print("Résultats de transmission :")
    print(f"- Succès: {result['success']}")
    print(f"- Taille originale: {result['original_size']} octets")
    print(f"- Ratio compression: {result['compression_ratio']:.2%}")
    print(f"- Fragments transmis: {result['fragments_sent']}")

# Lancer la démo
asyncio.run(demo_pipeline())
```

## 📊 Tests automatisés

Lancez la suite de tests :

```bash
# Tests unitaires MML
python -m pytest tests/test_mml.py -v

# Tous les tests
python -m pytest tests/ -v
```

## 🎯 Exemples pratiques

### Transmission d'urgence

```python
from src.dnf_mml_morse import transmit_document

# Message d'urgence
message = """
URGENT: Incendie forêt
Localisation: 45.123N 2.456E
3 blessés légers, besoin hélicoptère évacuation
"""

# Transmission simulée
result = await transmit_document(message, destination='F6SOS')
```

### Conversion de page web

```python
from src.dnf_mml_morse.mml import convert_to_mml

# Convertir une page HTML
mml_doc = convert_to_mml('examples/sample.html')
print(f"Document converti: {len(mml_doc['content'])} caractères")
print(f"Métadonnées: {mml_doc['metadata']}")
```

## 🔧 Configuration avancée

Créer un fichier de configuration `config.json` :

```json
{
  "morse_mode": "optimized",
  "transport": "cw",
  "callsign": "YOUR_CALLSIGN",
  "compression_level": "standard",
  "wpm": 20,
  "max_fragment_size": 200,
  "timeout": 300
}
```

Utiliser avec le CLI :
```bash
dnf-mml-morse --config config.json transmit document.html --destination F6XYZ
```

## 🚨 Dépannage

### Erreur d'import
Si vous avez des erreurs d'import, vérifiez :
- Python 3.8+ est installé
- Vous êtes dans le bon répertoire
- Les dépendances sont installées : `pip install -r requirements.txt`

### Erreur de transmission
- Vérifiez que le callsign est valide
- Assurez-vous que le fichier destination existe
- Testez avec un fichier plus petit d'abord

### Problèmes de performance
- Utilisez `compression_level: "light"` pour des documents courts
- Réduisez `wpm` pour des transmissions plus lentes mais plus fiables

## 📚 Prochaines étapes

1. **Lire la documentation complète** dans le dossier `docs/`
2. **Explorer les exemples** dans `examples/`
3. **Personnaliser la configuration** selon vos besoins
4. **Contribuer** au projet sur GitHub

## 🆘 Support

- **Documentation complète** : `docs/` directory
- **Exemples** : `examples/` directory
- **Tests** : `python -m pytest tests/`
- **Issues** : Signaler les problèmes sur GitHub

---

*Ce système représente une innovation majeure dans la transmission de données structurées en environnements contraints. Profitez de l'exploration !* 🌍📡✨
