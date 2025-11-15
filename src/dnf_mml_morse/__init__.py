"""
DNF-MML-Morse: Système de transmission de documents structurés via radio amateur

Ce package fournit une implémentation complète du système DNF-MML-Morse,
permettant la transmission fiable de documents structurés dans des environnements
contraints utilisant le langage MML, le framework DNF et le code Morse.

Fonctionnalités principales:
- Conversion HTML/Markdown vers MML
- Compression MML-C avec tokens lexicaux
- Mapping Morse optimisé pour MML-C
- Transmission via divers protocoles radio
- Sécurité et authentification intégrées
- Interface CLI et API Python

Exemple d'usage rapide:
    >>> from dnf_mml_morse import transmit_document
    >>> result = await transmit_document('document.html', destination='F6XYZ')
    >>> print(f"Transmission réussie: {result['fragments_sent']} fragments")
"""

__version__ = "1.0.0"
__author__ = "Système DNF-MML-Morse"
__email__ = "contact@dnf-mml-morse.org"
__license__ = "MIT"

# Import des modules principaux
from .core import DNFMMLMorseSystem
from .mml import MMLProcessor, MMLParser, MMLCompressor, MMLValidator
from .morse import MorseCodec
from .dnf import DNFTransmitter, DNFNetworkManager

# Fonctions utilitaires pour usage rapide
async def transmit_document(document_path, destination=None, **config):
    """
    Fonction utilitaire pour transmission rapide de documents

    Args:
        document_path (str): Chemin vers le document source
        destination (str, optional): Destinataire radio
        **config: Configuration supplémentaire

    Returns:
        dict: Résultats de la transmission
    """
    system = DNFMMLMorseSystem(config)
    return await system.transmit_document(document_path, destination)


def convert_to_mml(document_path):
    """
    Convertit un document en MML

    Args:
        document_path (str): Chemin vers le document source

    Returns:
        dict: Document MML avec métadonnées
    """
    processor = MMLProcessor()
    return processor.convert_to_mml(document_path)


def encode_morse(text, mode='optimized'):
    """
    Encode du texte en Morse

    Args:
        text (str): Texte à encoder
        mode (str): Mode d'encodage ('optimized', 'standard')

    Returns:
        str: Séquence Morse
    """
    codec = MorseCodec(mode=mode)
    return codec.encode(text)


def decode_morse(morse_sequence, mode='optimized'):
    """
    Décode une séquence Morse en texte

    Args:
        morse_sequence (str): Séquence Morse
        mode (str): Mode de décodage

    Returns:
        str: Texte décodé
    """
    codec = MorseCodec(mode=mode)
    return codec.decode(morse_sequence)


# Exports publics
__all__ = [
    # Classes principales
    'DNFMMLMorseSystem',
    'MMLProcessor',
    'MMLParser',
    'MMLCompressor',
    'MMLValidator',
    'MorseCodec',
    'DNFTransmitter',
    'DNFNetworkManager',

    # Fonctions utilitaires
    'transmit_document',
    'convert_to_mml',
    'encode_morse',
    'decode_morse',

    # Métadonnées
    '__version__',
    '__author__',
    '__email__',
    '__license__',
]

# Validation de l'environnement au chargement
def _validate_environment():
    """Validation de l'environnement d'exécution"""
    import sys

    if sys.version_info < (3, 8):
        raise RuntimeError("DNF-MML-Morse nécessite Python 3.8 ou supérieur")

    # Vérifications supplémentaires peuvent être ajoutées ici
    # (dépendances, permissions, etc.)

_validate_environment()
