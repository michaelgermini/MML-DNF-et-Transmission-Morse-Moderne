"""
Processeur MML - Interface unifiée pour le traitement MML
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Union, Optional
from bs4 import BeautifulSoup
from .parser import MMLParser
from .compressor import MMLCompressor
from .validator import MMLValidator


class MMLProcessor:
    """
    Processeur unifié pour le langage MML

    Combine parsing, compression, validation et conversion
    """

    def __init__(self, compression_level: str = 'standard'):
        """
        Initialisation du processeur

        Args:
            compression_level: Niveau de compression ('light', 'standard', 'aggressive')
        """
        self.parser = MMLParser()
        self.compressor = MMLCompressor(compression_level)
        self.validator = MMLValidator()

    async def convert_to_mml(self, input_source: Union[str, Path]) -> Dict[str, Any]:
        """
        Conversion d'une source vers MML

        Args:
            input_source: Fichier source ou contenu HTML/Markdown

        Returns:
            Document MML avec métadonnées
        """
        # Si c'est un fichier, le parser
        if isinstance(input_source, (str, Path)) and Path(input_source).exists():
            return self.parser.parse_file(str(input_source))
        else:
            # Contenu direct - traiter comme HTML
            return self.parser._parse_html(str(input_source), "direct_input")

    async def compress_mml(self, mml_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compression d'un document MML

        Args:
            mml_document: Document MML

        Returns:
            Document compressé
        """
        content = mml_document.get('content', '')
        return self.compressor.compress(content)

    async def decompress_mmlc(self, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Décompression de données MML-C

        Args:
            compressed_data: Données compressées

        Returns:
            Données décompressées
        """
        return self.compressor.decompress(compressed_data)

    def validate_mml(self, mml_content: str, strict: bool = False) -> Dict[str, Any]:
        """
        Validation de contenu MML

        Args:
            mml_content: Contenu MML à valider
            strict: Mode strict

        Returns:
            Résultats de validation
        """
        return self.validator.validate(mml_content, strict)

    def repair_mml(self, mml_content: str) -> str:
        """
        Réparation automatique de MML invalide

        Args:
            mml_content: Contenu MML à réparer

        Returns:
            Contenu réparé
        """
        result = self.validator.repair(mml_content)
        return result['repaired']

    async def convert_mml_to_output(self, mml_content: str, output_format: str = 'html') -> str:
        """
        Conversion de MML vers un format de sortie

        Args:
            mml_content: Contenu MML
            output_format: Format de sortie ('html', 'markdown', 'text')

        Returns:
            Contenu converti
        """
        # Mapping inverse MML vers HTML
        mml_to_html = {
            'H1': 'h1', 'H2': 'h2', 'H3': 'h3', 'H4': 'h4', 'H5': 'h5', 'H6': 'h6',
            'P': 'p', 'D': 'div', 'S': 'span', 'C': 'section', 'A': 'article',
            'R': 'header', 'F': 'footer', 'N': 'nav', 'I': 'aside',
            'U': 'ul', 'O': 'ol', 'L': 'li',
            'T': 'table', 'R': 'tr', 'D': 'td', 'H': 'th',
            'K': 'a', 'M': 'img',
            'B': 'strong', 'E': 'em', 'C': 'code', 'Q': 'blockquote',
        }

        # Remplacement des balises
        for mml_tag, html_tag in mml_to_html.items():
            mml_content = re.sub(rf'<{mml_tag}>', f'<{html_tag}>', mml_content)
            mml_content = re.sub(rf'<{mml_tag}(\s[^>]*)>', f'<{html_tag}\\1>', mml_content)
            mml_content = re.sub(rf'</{mml_tag}>', f'</{html_tag}>', mml_content)

        # Remplacement des codes courts
        code_to_tag = {'p': 'p', '1': 'h1', '2': 'h2', '3': 'h3', '4': 'h4', '5': 'h5', '6': 'h6'}
        for code, tag in code_to_tag.items():
            mml_content = re.sub(rf'<{code}>', f'<{tag}>', mml_content)
            mml_content = re.sub(rf'</{code}>', f'</{tag}>', mml_content)

        if output_format == 'markdown':
            # Conversion HTML vers Markdown (basique)
            return self._html_to_markdown(mml_content)
        elif output_format == 'text':
            # Extraction du texte brut
            soup = BeautifulSoup(mml_content, 'html.parser')
            return soup.get_text()
        else:
            return mml_content

    def _html_to_markdown(self, html_content: str) -> str:
        """Conversion basique HTML vers Markdown"""
        # Remplacements simples
        replacements = [
            (r'<h1>(.*?)</h1>', r'# \1'),
            (r'<h2>(.*?)</h2>', r'## \1'),
            (r'<h3>(.*?)</h3>', r'### \1'),
            (r'<p>(.*?)</p>', r'\1\n'),
            (r'<strong>(.*?)</strong>', r'**\1**'),
            (r'<em>(.*?)</em>', r'*\1*'),
            (r'<code>(.*?)</code>', r'`\1`'),
            (r'<li>(.*?)</li>', r'- \1'),
            (r'<br/?>', r'\n'),
        ]

        markdown = html_content
        for pattern, replacement in replacements:
            markdown = re.sub(pattern, replacement, markdown, flags=re.IGNORECASE | re.DOTALL)

        # Nettoyage des balises restantes
        markdown = re.sub(r'<[^>]+>', '', markdown)

        return markdown.strip()

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Statistiques de traitement

        Returns:
            Statistiques détaillées
        """
        return {
            'compression_stats': self.compressor.get_compression_stats(),
            'validation_capabilities': 'full',
            'supported_formats': ['html', 'markdown', 'text', 'mml'],
            'compression_levels': ['light', 'standard', 'aggressive'],
        }


# Fonction utilitaire
async def convert_to_mml(input_source: Union[str, Path]) -> Dict[str, Any]:
    """
    Fonction utilitaire de conversion vers MML

    Args:
        input_source: Source à convertir

    Returns:
        Document MML
    """
    processor = MMLProcessor()
    return await processor.convert_to_mml(input_source)


# Fonction synchrone pour compatibilité
def convert_to_mml_sync(input_source: Union[str, Path]) -> Dict[str, Any]:
    """
    Fonction utilitaire synchrone de conversion vers MML

    Args:
        input_source: Source à convertir

    Returns:
        Document MML
    """
    import asyncio
    return asyncio.run(convert_to_mml(input_source))
