"""
Parser MML - Conversion de documents vers le langage MML
"""

import re
import html
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from bs4 import BeautifulSoup
import markdown
import logging

logger = logging.getLogger(__name__)


class MMLParser:
    """
    Parser pour convertir HTML/Markdown vers MML (Minimal Markup Language)

    Le MML est un langage de balisage minimal optimisé pour :
    - La transmission à faible bande passante
    - La compression efficace
    - La robustesse aux erreurs de transmission
    """

    def __init__(self):
        """Initialisation du parser"""
        self.supported_formats = ['html', 'markdown', 'md', 'txt']

        # Mappings des balises HTML vers MML
        self.html_to_mml = {
            # Structure
            'h1': 'H1', 'h2': 'H2', 'h3': 'H3', 'h4': 'H4', 'h5': 'H5', 'h6': 'H6',
            'p': 'P', 'div': 'D', 'span': 'S', 'section': 'C', 'article': 'A',
            'header': 'R', 'footer': 'F', 'nav': 'N', 'aside': 'I',

            # Listes
            'ul': 'U', 'ol': 'O', 'li': 'L',

            # Tableaux
            'table': 'T', 'tr': 'R', 'td': 'D', 'th': 'H',

            # Liens et médias
            'a': 'K', 'img': 'M', 'audio': 'U', 'video': 'V',

            # Mise en forme
            'strong': 'B', 'b': 'B', 'em': 'E', 'i': 'E',
            'code': 'C', 'pre': 'E', 'blockquote': 'Q',

            # Sémantique
            'title': 'J', 'meta': 'M', 'link': 'K',
        }

        # Attributs importants à conserver
        self.important_attrs = {
            'a': ['href'],
            'img': ['src', 'alt'],
            'meta': ['name', 'content', 'property'],
            'link': ['rel', 'href'],
        }

        # Expressions régulières pour Markdown
        self.md_patterns = {
            'header': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            'bold': re.compile(r'\*\*(.+?)\*\*'),
            'italic': re.compile(r'\*(.+?)\*'),
            'code_inline': re.compile(r'`(.+?)`'),
            'code_block': re.compile(r'```(.+?)```', re.DOTALL),
            'link': re.compile(r'\[(.+?)\]\((.+?)\)'),
            'list_item': re.compile(r'^[\s]*[-\*\+]\s+(.+)$', re.MULTILINE),
            'ordered_list': re.compile(r'^\s*\d+\.\s+(.+)$', re.MULTILINE),
        }

    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyse un fichier et le convertit en MML

        Args:
            file_path: Chemin vers le fichier source

        Returns:
            Document MML avec métadonnées
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

        # Détection du format
        file_ext = file_path.suffix.lower().lstrip('.')
        if file_ext not in self.supported_formats:
            raise ValueError(f"Format non supporté: {file_ext}")

        # Lecture du contenu
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Essai avec d'autres encodages
            for encoding in ['latin-1', 'cp1252']:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Impossible de décoder le fichier: {file_path}")

        # Conversion selon le format
        if file_ext in ['html']:
            return self._parse_html(content, file_path)
        elif file_ext in ['markdown', 'md']:
            return self._parse_markdown(content, file_path)
        elif file_ext == 'txt':
            return self._parse_text(content, file_path)
        else:
            raise ValueError(f"Format non supporté: {file_ext}")

    def _parse_html(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Conversion HTML vers MML

        Args:
            content: Contenu HTML
            file_path: Chemin du fichier source

        Returns:
            Document MML
        """
        soup = BeautifulSoup(content, 'html.parser')

        # Extraction des métadonnées
        metadata = self._extract_html_metadata(soup)

        # Conversion récursive du contenu
        mml_content = self._html_to_mml(soup.body or soup)

        return {
            'format': 'html',
            'source_path': str(file_path),
            'size': len(content),
            'metadata': metadata,
            'content': mml_content,
            'encoding': 'utf-8',
        }

    def _extract_html_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extraction des métadonnées HTML"""
        metadata = {}

        # Titre
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content

        # Description depuis meta ou premier paragraphe
        if 'description' not in metadata:
            first_p = soup.find('p')
            if first_p:
                desc = first_p.get_text().strip()[:200]
                if desc:
                    metadata['description'] = desc

        # Auteur
        author_meta = soup.find('meta', {'name': 'author'})
        if author_meta:
            metadata['author'] = author_meta.get('content')

        return metadata

    def _html_to_mml(self, element) -> str:
        """
        Conversion récursive d'un élément HTML vers MML

        Args:
            element: Élément BeautifulSoup

        Returns:
            Contenu MML
        """
        if isinstance(element, str):
            # Texte brut - échapper les caractères spéciaux MML
            return self._escape_mml_text(element)

        # Ignorer les éléments de script et style
        if element.name in ['script', 'style', 'noscript']:
            return ''

        # Balise d'ouverture
        mml_tag = self.html_to_mml.get(element.name, 'X')  # X pour balise inconnue

        # Attributs importants
        attrs_mml = self._format_html_attrs(element)

        # Contenu
        content_parts = []
        for child in element.children:
            content_parts.append(self._html_to_mml(child))

        content = ''.join(content_parts)

        # Construction de la balise MML
        if content:
            if attrs_mml:
                return f'<{mml_tag}{attrs_mml}>{content}</{mml_tag}>'
            else:
                return f'<{mml_tag}>{content}</{mml_tag}>'
        else:
            # Balise auto-fermante
            if attrs_mml:
                return f'<{mml_tag}{attrs_mml}/>'
            else:
                return f'<{mml_tag}/>'

    def _format_html_attrs(self, element) -> str:
        """Formatage des attributs HTML pour MML"""
        if element.name not in self.important_attrs:
            return ''

        attrs = []
        for attr in self.important_attrs[element.name]:
            value = element.get(attr)
            if value:
                # Échapper les guillemets et caractères spéciaux
                value = value.replace('"', '\\"').replace('<', '\\<').replace('>', '\\>')
                attrs.append(f'{attr}="{value}"')

        return ' ' + ' '.join(attrs) if attrs else ''

    def _parse_markdown(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Conversion Markdown vers MML

        Args:
            content: Contenu Markdown
            file_path: Chemin du fichier source

        Returns:
            Document MML
        """
        # Conversion Markdown vers HTML puis vers MML
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])

        # Création d'un faux soup pour réutiliser la logique HTML
        soup = BeautifulSoup(f'<div>{html_content}</div>', 'html.parser')

        # Extraction des métadonnées basiques
        metadata = self._extract_markdown_metadata(content)

        # Conversion vers MML
        mml_content = self._html_to_mml(soup.div)

        return {
            'format': 'markdown',
            'source_path': str(file_path),
            'size': len(content),
            'metadata': metadata,
            'content': mml_content,
            'encoding': 'utf-8',
        }

    def _extract_markdown_metadata(self, content: str) -> Dict[str, Any]:
        """Extraction des métadonnées Markdown (front matter YAML)"""
        metadata = {}

        lines = content.split('\n')
        if len(lines) >= 3 and lines[0].strip() == '---':
            # Front matter YAML détecté
            end_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_idx = i
                    break

            if end_idx > 0:
                # Parsing basique du YAML
                for line in lines[1:end_idx]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip().strip('"').strip("'")

        # Titre depuis premier header si pas de front matter
        if 'title' not in metadata:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1).strip()

        return metadata

    def _parse_text(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Conversion texte brut vers MML

        Args:
            content: Contenu texte
            file_path: Chemin du fichier source

        Returns:
            Document MML
        """
        # Texte brut = paragraphes séparés par des sauts de ligne
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        mml_parts = []
        for para in paragraphs:
            if para:
                escaped = self._escape_mml_text(para)
                mml_parts.append(f'<P>{escaped}</P>')

        mml_content = ''.join(mml_parts)

        return {
            'format': 'text',
            'source_path': str(file_path),
            'size': len(content),
            'metadata': {
                'title': file_path.stem,
                'paragraphs': len(paragraphs),
            },
            'content': mml_content,
            'encoding': 'utf-8',
        }

    def _escape_mml_text(self, text: str) -> str:
        """
        Échappement du texte pour MML

        Args:
            text: Texte à échapper

        Returns:
            Texte échappé
        """
        # Échapper les caractères spéciaux MML
        text = text.replace('<', '\\<')
        text = text.replace('>', '\\>')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('[', '\\[')
        text = text.replace(']', '\\]')

        # Normaliser les espaces
        text = ' '.join(text.split())

        return text

    def validate_mml(self, mml_content: str) -> Dict[str, Any]:
        """
        Validation basique du contenu MML

        Args:
            mml_content: Contenu MML à valider

        Returns:
            Résultats de validation
        """
        errors = []
        warnings = []

        # Vérification des balises équilibrées
        stack = []
        i = 0
        while i < len(mml_content):
            if mml_content[i] == '<':
                # Balise ouvrante
                if i + 1 < len(mml_content) and mml_content[i + 1] != '/':
                    # Recherche de la fin de la balise
                    end_pos = mml_content.find('>', i)
                    if end_pos == -1:
                        errors.append(f"Balise non fermée à position {i}")
                        break

                    tag_content = mml_content[i+1:end_pos]
                    tag_name = tag_content.split()[0].split('{')[0]  # Gestion des attributs

                    if tag_content.endswith('/'):
                        # Balise auto-fermante
                        pass
                    else:
                        # Balise ouvrante normale
                        stack.append((tag_name, i))

                    i = end_pos + 1

                elif i + 1 < len(mml_content) and mml_content[i + 1] == '/':
                    # Balise fermante
                    end_pos = mml_content.find('>', i)
                    if end_pos == -1:
                        errors.append(f"Balise fermante non fermée à position {i}")
                        break

                    tag_name = mml_content[i+2:end_pos]
                    if stack and stack[-1][0] == tag_name:
                        stack.pop()
                    else:
                        errors.append(f"Balise fermante {tag_name} sans ouvrante correspondante à position {i}")

                    i = end_pos + 1
                else:
                    i += 1
            else:
                i += 1

        if stack:
            for tag_name, pos in stack:
                errors.append(f"Balise {tag_name} ouverte à position {pos} non fermée")

        # Vérifications de contenu
        if not mml_content.strip():
            warnings.append("Document MML vide")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'stats': {
                'length': len(mml_content),
                'tags': len(re.findall(r'</?\w+', mml_content)),
                'text_ratio': len(re.findall(r'[^<>]+', mml_content)) / max(len(mml_content), 1),
            }
        }


# Fonction utilitaire pour usage direct
def parse_document(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Fonction utilitaire pour parser un document directement

    Args:
        file_path: Chemin du document

    Returns:
        Document MML
    """
    parser = MMLParser()
    return parser.parse_file(file_path)
