"""
Validateur MML - Validation syntaxique et sémantique
"""

import re
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MMLValidator:
    """
    Validateur pour le langage MML (Minimal Markup Language)

    Vérifie :
    - La syntaxe des balises
    - La structure hiérarchique
    - La sémantique des éléments
    - La conformité aux spécifications MML
    """

    def __init__(self):
        """Initialisation du validateur"""
        # Balises MML autorisées
        self.allowed_tags = {
            # Structure
            'H1', 'H2', 'H3', 'H4', 'H5', 'H6',  # Titres
            'P',   # Paragraphe
            'D',   # Division
            'S',   # Span
            'C',   # Section
            'A',   # Article
            'R',   # Header
            'F',   # Footer
            'N',   # Navigation
            'I',   # Aside

            # Listes
            'U',   # Unordered list
            'O',   # Ordered list
            'L',   # List item

            # Tableaux
            'T',   # Table
            'R',   # Table row (attention conflit avec Header)
            'D',   # Table cell (attention conflit avec Division)
            'H',   # Table header

            # Liens et médias
            'K',   # Link
            'M',   # Media (image, audio, video)

            # Mise en forme
            'B',   # Bold
            'E',   # Emphasis
            'C',   # Code (attention conflit avec Section)
            'Q',   # Quote

            # Métadonnées
            'J',   # Title
            'X',   # Extension/custom

            # Codes courts (compression)
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        }

        # Règles de hiérarchie
        self.hierarchy_rules = {
            'U': {'L'},        # UL ne peut contenir que LI
            'O': {'L'},        # OL ne peut contenir que LI
            'T': {'R'},        # TABLE ne peut contenir que TR
            'R': {'D', 'H'},   # TR ne peut contenir que TD ou TH
            'L': set(),        # LI peut contenir n'importe quoi
        }

        # Règles d'attributs
        self.attribute_rules = {
            'K': {'href'},     # Liens doivent avoir href
            'M': {'src', 'alt'}, # Médias doivent avoir src
            'J': {'level'},    # Titres peuvent avoir level
        }

        # Expressions régulières pour validation
        self.tag_pattern = re.compile(r'</?([a-zA-Z0-9]+)(?:\s+([^>]*))?(/?)>')
        self.attr_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]*)"')

    def validate(self, mml_content: str, strict: bool = False) -> Dict[str, Any]:
        """
        Validation complète du contenu MML

        Args:
            mml_content: Contenu MML à valider
            strict: Mode de validation strict (True) ou permissif (False)

        Returns:
            Résultats de validation
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {},
            'recommendations': [],
        }

        try:
            # Validation syntaxique
            syntax_result = self._validate_syntax(mml_content)
            result['errors'].extend(syntax_result['errors'])
            result['warnings'].extend(syntax_result['warnings'])

            # Validation structurelle (si syntaxe OK)
            if syntax_result['valid']:
                structure_result = self._validate_structure(mml_content)
                result['errors'].extend(structure_result['errors'])
                result['warnings'].extend(structure_result['warnings'])

                # Validation sémantique
                semantic_result = self._validate_semantics(mml_content)
                result['errors'].extend(semantic_result['errors'])
                result['warnings'].extend(semantic_result['warnings'])

            # Statistiques
            result['stats'] = self._analyze_stats(mml_content)

            # Recommandations
            result['recommendations'] = self._generate_recommendations(result)

            # Validation globale
            result['valid'] = len(result['errors']) == 0

            # En mode strict, les warnings deviennent des erreurs
            if strict and result['warnings']:
                result['errors'].extend([f"Strict: {w}" for w in result['warnings']])
                result['warnings'] = []
                result['valid'] = len(result['errors']) == 0

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Erreur de validation: {e}")

        return result

    def _validate_syntax(self, content: str) -> Dict[str, Any]:
        """
        Validation de la syntaxe MML

        Args:
            content: Contenu MML

        Returns:
            Résultats de validation syntaxique
        """
        result = {'valid': True, 'errors': [], 'warnings': []}

        # Vérification des balises équilibrées
        stack = []
        i = 0

        while i < len(content):
            if content[i] == '<':
                # Recherche de la fin de la balise
                end_pos = content.find('>', i)
                if end_pos == -1:
                    result['errors'].append(f"Balise non fermée à position {i}")
                    result['valid'] = False
                    break

                tag_content = content[i+1:end_pos]

                if tag_content.startswith('/'):
                    # Balise fermante
                    tag_name = tag_content[1:].split()[0]
                    if not stack:
                        result['errors'].append(f"Balise fermante '{tag_name}' sans balise ouvrante à position {i}")
                        result['valid'] = False
                    elif stack[-1] != tag_name:
                        result['errors'].append(f"Balise fermante '{tag_name}' ne correspond pas à l'ouvrante '{stack[-1]}' à position {i}")
                        result['valid'] = False
                    else:
                        stack.pop()
                else:
                    # Balise ouvrante
                    tag_parts = tag_content.split()
                    tag_name = tag_parts[0]

                    # Vérification balise autorisée
                    if tag_name not in self.allowed_tags:
                        result['warnings'].append(f"Balise inconnue '{tag_name}' à position {i}")

                    # Balise auto-fermante
                    if tag_content.endswith('/'):
                        pass  # Rien à faire
                    else:
                        stack.append(tag_name)

                    # Validation des attributs
                    if len(tag_parts) > 1:
                        attr_string = ' '.join(tag_parts[1:])
                        attr_errors = self._validate_attributes(tag_name, attr_string, i)
                        result['errors'].extend(attr_errors['errors'])
                        result['warnings'].extend(attr_errors['warnings'])
                        if attr_errors['errors']:
                            result['valid'] = False

                i = end_pos + 1
            else:
                i += 1

        # Vérification des balises non fermées
        if stack:
            for tag in stack:
                result['errors'].append(f"Balise '{tag}' non fermée")
            result['valid'] = False

        return result

    def _validate_attributes(self, tag_name: str, attr_string: str, position: int) -> Dict[str, Any]:
        """
        Validation des attributs d'une balise

        Args:
            tag_name: Nom de la balise
            attr_string: Chaîne des attributs
            position: Position dans le document

        Returns:
            Résultats de validation
        """
        result = {'errors': [], 'warnings': []}

        # Parsing des attributs
        attrs = {}
        for match in self.attr_pattern.finditer(attr_string):
            attr_name, attr_value = match.groups()
            attrs[attr_name] = attr_value

        # Validation selon les règles de la balise
        if tag_name in self.attribute_rules:
            required_attrs = self.attribute_rules[tag_name]
            for req_attr in required_attrs:
                if req_attr not in attrs:
                    result['warnings'].append(f"Attribut requis '{req_attr}' manquant pour balise '{tag_name}' à position {position}")

        # Validation générale des attributs
        for attr_name, attr_value in attrs.items():
            # Vérification des caractères spéciaux dans la valeur
            if '"' in attr_value or '<' in attr_value or '>' in attr_value:
                result['warnings'].append(f"Caractères spéciaux dans la valeur de l'attribut '{attr_name}' à position {position}")

        return result

    def _validate_structure(self, content: str) -> Dict[str, Any]:
        """
        Validation de la structure hiérarchique

        Args:
            content: Contenu MML

        Returns:
            Résultats de validation structurelle
        """
        result = {'errors': [], 'warnings': []}

        # Parsing simplifié pour analyse de structure
        stack = []
        for match in self.tag_pattern.finditer(content):
            tag_name = match.group(1)
            is_closing = match.group(0).startswith('</')
            is_self_closing = match.group(0).endswith('/>')

            if is_self_closing:
                continue
            elif is_closing:
                if stack and stack[-1] == tag_name:
                    stack.pop()
                else:
                    result['errors'].append(f"Structure invalide: balise fermante '{tag_name}' inattendue")
            else:
                # Vérification des règles hiérarchiques
                if stack and stack[-1] in self.hierarchy_rules:
                    allowed_children = self.hierarchy_rules[stack[-1]]
                    if allowed_children and tag_name not in allowed_children:
                        result['warnings'].append(f"Élément '{tag_name}' inattendu dans '{stack[-1]}'")

                stack.append(tag_name)

        return result

    def _validate_semantics(self, content: str) -> Dict[str, Any]:
        """
        Validation sémantique

        Args:
            content: Contenu MML

        Returns:
            Résultats de validation sémantique
        """
        result = {'errors': [], 'warnings': []}

        # Recherche de patterns sémantiques problématiques

        # Titres vides
        empty_headers = re.findall(r'<H[1-6]>\s*</H[1-6]>', content)
        if empty_headers:
            result['warnings'].append(f"{len(empty_headers)} titre(s) vide(s) trouvé(s)")

        # Liens sans href
        links_without_href = re.findall(r'<K[^>]*>(?!.*href\s*=)[^<]*</K>', content, re.DOTALL)
        if links_without_href:
            result['warnings'].append(f"{len(links_without_href)} lien(s) sans attribut href")

        # Listes vides
        empty_lists = re.findall(r'<[UO]>\s*</[UO]>', content)
        if empty_lists:
            result['warnings'].append(f"{len(empty_lists)} liste(s) vide(s) trouvée(s)")

        # Paragraphes vides
        empty_paragraphs = re.findall(r'<P>\s*</P>', content)
        if empty_paragraphs:
            result['warnings'].append(f"{len(empty_paragraphs)} paragraphe(s) vide(s) trouvé(s)")

        # Vérification de la structure générale
        if not re.search(r'<H1[^>]*>.*</H1>', content):
            result['warnings'].append("Aucun titre de niveau 1 (H1) trouvé")

        return result

    def _analyze_stats(self, content: str) -> Dict[str, Any]:
        """
        Analyse statistique du document MML

        Args:
            content: Contenu MML

        Returns:
            Statistiques du document
        """
        stats = {
            'total_length': len(content),
            'tag_count': 0,
            'text_length': 0,
            'tag_frequency': defaultdict(int),
            'depth_max': 0,
            'compression_ratio_estimate': 0.0,
        }

        # Comptage des balises
        tags = re.findall(r'</?([a-zA-Z0-9]+)', content)
        stats['tag_count'] = len(tags)

        for tag in tags:
            stats['tag_frequency'][tag] += 1

        # Longueur du texte
        text_parts = re.findall(r'[^<>]+', content)
        stats['text_length'] = sum(len(part.strip()) for part in text_parts)

        # Profondeur maximale
        current_depth = 0
        max_depth = 0
        for match in self.tag_pattern.finditer(content):
            if not match.group(0).startswith('</') and not match.group(0).endswith('/>'):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif match.group(0).startswith('</'):
                current_depth = max(0, current_depth - 1)

        stats['depth_max'] = max_depth

        # Ratio de compression estimé
        if stats['total_length'] > 0:
            text_ratio = stats['text_length'] / stats['total_length']
            tag_ratio = stats['tag_count'] * 10 / stats['total_length']  # Estimation taille moyenne balise
            stats['compression_ratio_estimate'] = text_ratio + tag_ratio

        return dict(stats)

    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """
        Génération de recommandations d'amélioration

        Args:
            validation_result: Résultats de validation

        Returns:
            Liste de recommandations
        """
        recommendations = []
        stats = validation_result.get('stats', {})

        # Recommandations basées sur les stats
        if stats.get('depth_max', 0) > 10:
            recommendations.append("Considérez aplatir la hiérarchie (profondeur > 10 niveaux)")

        if stats.get('compression_ratio_estimate', 0) > 0.8:
            recommendations.append("Le document contient beaucoup de texte - envisagez la compression MML-C")

        # Recommandations basées sur les erreurs/warnings
        error_count = len(validation_result.get('errors', []))
        warning_count = len(validation_result.get('warnings', []))

        if error_count > 0:
            recommendations.append(f"Corrigez les {error_count} erreur(s) de validation pour améliorer la compatibilité")

        if warning_count > 0:
            recommendations.append(f"Considérez corriger les {warning_count} avertissement(s) pour une meilleure qualité")

        # Recommandations générales
        if stats.get('tag_count', 0) < 5:
            recommendations.append("Ajoutez plus de structure (titres, paragraphes) pour améliorer la lisibilité")

        return recommendations

    def repair(self, mml_content: str) -> Dict[str, Any]:
        """
        Tentative de réparation automatique du MML invalide

        Args:
            mml_content: Contenu MML à réparer

        Returns:
            Résultats de réparation
        """
        result = {
            'original': mml_content,
            'repaired': mml_content,
            'changes': [],
            'success': True,
        }

        # Fermeture automatique des balises non fermées
        # (Implémentation simplifiée)
        stack = []
        repaired = []
        i = 0

        while i < len(mml_content):
            if mml_content[i] == '<':
                end_pos = mml_content.find('>', i)
                if end_pos == -1:
                    break

                tag_content = mml_content[i+1:end_pos]
                repaired.append(mml_content[i:end_pos+1])

                if tag_content.startswith('/'):
                    # Balise fermante
                    tag_name = tag_content[1:].split()[0]
                    if stack and stack[-1] == tag_name:
                        stack.pop()
                    # Sinon, on ignore (balise orpheline)
                elif not tag_content.endswith('/'):
                    # Balise ouvrante
                    tag_name = tag_content.split()[0]
                    stack.append(tag_name)

                i = end_pos + 1
            else:
                repaired.append(mml_content[i])
                i += 1

        # Fermeture des balises restantes
        while stack:
            tag = stack.pop()
            repaired.append(f'</{tag}>')
            result['changes'].append(f"Fermeture automatique de la balise '{tag}'")

        result['repaired'] = ''.join(repaired)

        return result


# Fonctions utilitaires
def validate_mml(content: str, strict: bool = False) -> Dict[str, Any]:
    """
    Fonction utilitaire pour validation directe

    Args:
        content: Contenu MML à valider
        strict: Mode strict

    Returns:
        Résultats de validation
    """
    validator = MMLValidator()
    return validator.validate(content, strict)


def repair_mml(content: str) -> str:
    """
    Fonction utilitaire pour réparation automatique

    Args:
        content: Contenu MML à réparer

    Returns:
        Contenu réparé
    """
    validator = MMLValidator()
    result = validator.repair(content)
    return result['repaired']
