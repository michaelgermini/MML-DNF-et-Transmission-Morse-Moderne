#!/usr/bin/env python3
"""
Interface en ligne de commande pour DNF-MML-Morse
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import DNFMMLMorseSystem
from .mml import convert_to_mml
from .morse import encode_morse, decode_morse
from .api import run_api_server
from .security import generate_secure_identity

# Console Rich pour une belle sortie
console = Console()


def async_command(f):
    """Décorateur pour les commandes async"""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@click.group()
@click.version_option(version="1.0.0")
@click.option('--config', type=click.Path(exists=True),
              help='Fichier de configuration JSON')
@click.option('--verbose', '-v', is_flag=True, help='Mode verbeux')
@click.pass_context
def cli(ctx, config, verbose):
    """DNF-MML-Morse: Transmission de documents via radio amateur

    Un système innovant pour transmettre des documents structurés
    dans des environnements à bande passante limitée.
    """
    ctx.ensure_object(dict)

    # Chargement de la configuration
    ctx.obj['config'] = {}
    if config:
        try:
            with open(config, 'r') as f:
                ctx.obj['config'] = json.load(f)
        except Exception as e:
            console.print(f"[red]Erreur de chargement de config: {e}[/red]")
            sys.exit(1)

    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('document', type=click.Path(exists=True))
@click.option('--destination', '-d', help='Callsign destinataire')
@click.option('--transport', '-t',
              type=click.Choice(['cw', 'js8call', 'packet', 'aprs']),
              default='cw', help='Mode de transmission')
@click.option('--morse-mode', '-m',
              type=click.Choice(['standard', 'optimized', 'robust']),
              default='optimized', help='Mode Morse')
@click.option('--callsign', '-c', help='Votre callsign')
@click.option('--output', '-o', type=click.Path(),
              help='Fichier de sortie pour les résultats')
@click.pass_context
@async_command
async def transmit(ctx, document, destination, transport, morse_mode, callsign, output):
    """Transmettre un document via DNF-MML-Morse"""

    # Configuration
    config = ctx.obj['config'].copy()
    config.update({
        'transport': transport,
        'morse_mode': morse_mode,
        'callsign': callsign or config.get('callsign', 'DEMO'),
    })

    # Validation
    if not destination:
        console.print("[red]Erreur: Destination requise (--destination)[/red]")
        sys.exit(1)

    try:
        # Initialisation du système
        with console.status("[bold green]Initialisation du système...", spinner="dots"):
            system = DNFMMLMorseSystem(config)

        # Transmission avec barre de progression
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Transmission en cours...", total=None)

            result = await system.transmit_document(document, destination)

            progress.update(task, completed=True)

        # Affichage des résultats
        if result['success']:
            # Tableau des résultats
            table = Table(title="Résultats de transmission")
            table.add_column("Métrique", style="cyan")
            table.add_column("Valeur", style="magenta")

            table.add_row("Statut", "[green]✓ Succès[/green]")
            table.add_row("Taille originale", f"{result['original_size']} octets")
            table.add_row("Taille MML", f"{result['mml_size']} caractères")
            table.add_row("Taille compressée", f"{result['compressed_size']} caractères")
            table.add_row("Ratio compression", f"{result['compression_ratio']:.1%}")
            table.add_row("Symboles Morse", f"{result['morse_symbols']}")
            table.add_row("Fragments envoyés", f"{result['fragments_sent']}")
            table.add_row("Temps transmission", f"{result['transmission_time']:.1f}s")
            table.add_row("Transport utilisé", result['transport_used'])
            table.add_row("Destination", result['destination'])

            console.print(table)

            # Sauvegarde si demandée
            if output:
                with open(output, 'w') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                console.print(f"[green]Résultats sauvegardés dans {output}[/green]")

        else:
            console.print(f"[red]❌ Échec de transmission: {result['error']}[/red]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("[yellow]Transmission interrompue par l'utilisateur[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erreur inattendue: {e}[/red]")
        if ctx.obj['verbose']:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--filter', '-f', multiple=True,
              help='Filtres de réception (clé=valeur)')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./received', help='Répertoire de sortie')
@click.option('--format', 'output_format',
              type=click.Choice(['html', 'markdown', 'text', 'json']),
              default='html', help='Format de sortie')
@click.option('--timeout', '-t', type=int, default=300,
              help='Timeout en secondes')
@click.pass_context
@async_command
async def receive(ctx, filter, output_dir, output_format, timeout):
    """Recevoir des documents"""

    # Configuration
    config = ctx.obj['config'].copy()
    filters = {}

    # Parsing des filtres
    for f in filter:
        if '=' in f:
            key, value = f.split('=', 1)
            filters[key] = value

    filters['output_format'] = output_format

    try:
        # Initialisation
        with console.status("[bold green]Initialisation de la réception...", spinner="dots"):
            system = DNFMMLMorseSystem(config)

        # Création du répertoire de sortie
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Réception avec timeout
        console.print(f"[cyan]Réception en cours... (timeout: {timeout}s)[/cyan]")
        console.print(f"[dim]Filtres: {filters}[/dim]")

        try:
            result = await asyncio.wait_for(
                system.receive_documents(filters),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            console.print("[yellow]Timeout atteint, aucun document reçu[/yellow]")
            return

        # Affichage des résultats
        if result['success']:
            documents = result['documents']

            if not documents:
                console.print("[yellow]Aucun document reçu[/yellow]")
                return

            console.print(f"[green]✓ {len(documents)} document(s) reçu(s)[/green]")

            # Sauvegarde des documents
            for i, doc in enumerate(documents, 1):
                filename = f"document_{i}.{output_format}"
                filepath = output_path / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(doc['content'])

                # Affichage des métadonnées
                metadata = doc.get('metadata', {})
                source = doc.get('source', 'unknown')

                console.print(f"[cyan]Document {i}:[/cyan] {filepath}")
                console.print(f"  [dim]Source: {source}[/dim]")
                if 'timestamp' in doc:
                    console.print(f"  [dim]Reçu: {doc['timestamp']}[/dim]")

        else:
            console.print(f"[red]❌ Échec de réception: {result['error']}[/red]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("[yellow]Réception interrompue par l'utilisateur[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erreur inattendue: {e}[/red]")
        if ctx.obj['verbose']:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument('document', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Fichier de sortie (défaut: stdout)')
@click.pass_context
def convert(ctx, document, output):
    """Convertir un document en MML"""

    try:
        result = convert_to_mml(document)

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            console.print(f"[green]✓ Conversion sauvegardée dans {output}[/green]")
        else:
            # Affichage avec syntax highlighting simulé
            content = result['content']
            console.print(Panel(content, title=f"MML: {document}", border_style="blue"))

        # Statistiques
        console.print(f"[dim]Taille originale: {result['size']} octets[/dim]")
        console.print(f"[dim]Taille MML: {len(result['content'])} caractères[/dim]")

    except Exception as e:
        console.print(f"[red]Erreur de conversion: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('text')
@click.option('--mode', '-m',
              type=click.Choice(['standard', 'optimized', 'robust']),
              default='optimized', help='Mode Morse')
@click.option('--decode', '-d', is_flag=True,
              help='Décoder au lieu d\'encoder')
@click.pass_context
def morse(ctx, text, mode, decode):
    """Encoder/décoder du texte en Morse"""

    try:
        if decode:
            result = decode_morse(text, mode=mode)
            operation = "décodage"
        else:
            result = encode_morse(text, mode=mode)
            operation = "encodage"

        console.print(Panel(result, title=f"Morse {operation} ({mode})", border_style="green"))

    except Exception as e:
        console.print(f"[red]Erreur Morse: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--detailed', '-d', is_flag=True,
              help='Informations détaillées')
@click.pass_context
@async_command
async def status(ctx, detailed):
    """Afficher l'état du système"""

    config = ctx.obj['config']

    try:
        system = DNFMMLMorseSystem(config)

        # État de base
        status_info = system.get_system_status()

        table = Table(title="État du système DNF-MML-Morse")
        table.add_column("Composant", style="cyan")
        table.add_column("Statut", style="green")
        table.add_column("Détails", style="dim")

        for component, status in status_info['components'].items():
            details = ""
            if component == 'dnf_transmitter' and detailed:
                transport_status = status_info.get('transport_status', {})
                details = f"Transport: {transport_status.get('type', 'N/A')}"

            table.add_row(component, status, details)

        console.print(table)

        if detailed:
            # Test de santé
            with console.status("[bold green]Tests de santé en cours...", spinner="dots"):
                health = await system.health_check()

            console.print(f"\nSanté globale: [green]{health['overall_status']}[/green]")

            if health['overall_status'] != 'healthy':
                health_table = Table(title="Résultats des tests")
                health_table.add_column("Test", style="cyan")
                health_table.add_column("Résultat", style="yellow")

                for test, result in health['checks'].items():
                    status_color = "green" if result == "healthy" else "red"
                    health_table.add_row(test, f"[{status_color}]{result}[/{status_color}]")

                console.print(health_table)

    except Exception as e:
        console.print(f"[red]Erreur d'état: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('config_file', type=click.Path())
@click.option('--validate', '-v', is_flag=True,
              help='Valider la configuration sans l\'appliquer')
@click.pass_context
def config(ctx, config_file, validate):
    """Gérer la configuration"""

    try:
        # Chargement et validation
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Validation basique
        required_keys = ['morse_mode', 'transport', 'callsign']
        missing_keys = [key for key in required_keys if key not in config_data]

        if missing_keys:
            console.print(f"[red]Clés manquantes: {missing_keys}[/red]")
            sys.exit(1)

        if validate:
            console.print("[green]✓ Configuration valide[/green]")

            # Affichage formaté
            config_text = json.dumps(config_data, indent=2, ensure_ascii=False)
            console.print(Panel(config_text, title="Configuration", border_style="blue"))
        else:
            console.print(f"[yellow]Configuration chargée depuis {config_file}[/yellow]")
            console.print("[dim]Utilisez --validate pour vérifier sans appliquer[/dim]")

    except json.JSONDecodeError as e:
        console.print(f"[red]Erreur JSON: {e}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        console.print(f"[red]Fichier non trouvé: {config_file}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(),
              default='config-template.json',
              help='Fichier de sortie pour le template')
def init_config(output):
    """Générer un template de configuration"""

    template = {
        "morse_mode": "optimized",
        "transport": "cw",
        "callsign": "YOUR_CALLSIGN",
        "compression_level": "standard",
        "wpm": 20,
        "max_fragment_size": 200,
        "timeout": 300,
        "retry_attempts": 3,
        "logging": {
            "level": "INFO",
            "file": "dnf_mml_morse.log"
        },
        "security": {
            "enable_signatures": true,
            "hash_algorithm": "blake2b",
            "encryption": false
        }
    }

    try:
        with open(output, 'w') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Template de configuration créé: {output}[/green]")

        # Affichage du contenu
        template_text = json.dumps(template, indent=2, ensure_ascii=False)
        console.print(Panel(template_text, title="Template généré", border_style="blue"))

    except Exception as e:
        console.print(f"[red]Erreur de création du template: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='Adresse d\'écoute')
@click.option('--port', '-p', type=int, default=8000, help='Port d\'écoute')
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Fichier de configuration JSON')
@click.pass_context
def server(ctx, host, port, config):
    """Lancer le serveur API REST/WebSocket"""
    # Chargement de la configuration
    server_config = ctx.obj.get('config', {}).copy()

    if config:
        try:
            with open(config, 'r') as f:
                server_config.update(json.load(f))
        except Exception as e:
            console.print(f"[red]Erreur de chargement de config: {e}[/red]")
            sys.exit(1)

    # Vérifier que les dépendances sont installées
    try:
        import fastapi
        import uvicorn
    except ImportError:
        console.print("[red]Erreur: FastAPI et Uvicorn sont requis pour le serveur API[/red]")
        console.print("[yellow]Installez avec: pip install fastapi uvicorn[/yellow]")
        sys.exit(1)

    console.print(f"[green]🚀 Démarrage du serveur API sur http://{host}:{port}[/green]")
    console.print(f"[blue]📖 Documentation: http://{host}:{port}/docs[/blue]")
    console.print(f"[blue]🌐 Interface web: http://{host}:{port}[/blue]")
    console.print("[dim]Appuyez sur Ctrl+C pour arrêter[/dim]")
    console.print()

    try:
        run_api_server(host=host, port=port, config=server_config)
    except KeyboardInterrupt:
        console.print("\n[yellow]Serveur arrêté par l'utilisateur[/yellow]")
    except Exception as e:
        console.print(f"[red]Erreur du serveur: {e}[/red]")
        sys.exit(1)


@cli.group()
def security():
    """Commandes de sécurité et chiffrement"""
    pass


@security.command()
@click.argument('name')
@click.pass_context
def create_identity(ctx, name):
    """Créer une nouvelle identité sécurisée"""
    try:
        identity = generate_secure_identity(name)
        console.print(f"[green]✓ Identité '{name}' créée avec succès[/green]")
        console.print(f"  Créée le: {identity['created']}")
        console.print(f"  Clé publique: {identity['public_key'][:50]}...")

    except Exception as e:
        console.print(f"[red]Erreur lors de la création de l'identité: {e}[/red]")
        sys.exit(1)


@security.command()
@click.pass_context
def list_identities(ctx):
    """Lister les identités disponibles"""
    try:
        system = DNFMMLMorseSystem(ctx.obj.get('config', {}))
        identities = system.list_identities()

        if not identities:
            console.print("[yellow]Aucune identité trouvée[/yellow]")
            return

        table = Table(title="Identités disponibles")
        table.add_column("Nom", style="cyan")
        table.add_column("Statut", style="green")

        for identity in identities:
            status = "Disponible"
            table.add_row(identity, status)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        sys.exit(1)


@security.command()
@click.argument('name')
@click.pass_context
def show_identity(ctx, name):
    """Afficher les détails d'une identité"""
    try:
        system = DNFMMLMorseSystem(ctx.obj.get('config', {}))
        identity = system.export_identity(name)

        console.print(f"[green]Identité: {name}[/green]")
        console.print(f"  Créée: {identity['created']}")
        console.print(f"  Version: {identity['version']}")
        console.print(f"  Clé publique (début): {identity['public_key'][:100]}...")

    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        sys.exit(1)


@security.command()
@click.option('--identity', '-i', help='Identité à utiliser')
@click.pass_context
def enable(ctx, identity):
    """Activer la sécurité"""
    try:
        config = ctx.obj.get('config', {}).copy()
        config.update({
            'security_enabled': True,
            'encryption_enabled': True,
            'signing_enabled': True,
            'identity_name': identity or 'default_user',
        })

        system = DNFMMLMorseSystem(config)
        success = system.enable_security(identity)

        if success:
            console.print(f"[green]✓ Sécurité activée pour l'identité '{identity or 'default_user'}'[/green]")
            console.print("[dim]Le système utilisera maintenant le chiffrement et les signatures[/dim]")
        else:
            console.print("[red]❌ Échec de l'activation de la sécurité[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        sys.exit(1)


@security.command()
@click.pass_context
def status(ctx):
    """Afficher l'état de la sécurité"""
    try:
        config = ctx.obj.get('config', {})
        system = DNFMMLMorseSystem(config)

        security_info = system.get_security_status()

        console.print("[green]État de la sécurité[/green]")

        if not security_info['security_enabled']:
            console.print("[yellow]Sécurité désactivée[/yellow]")
            return

        console.print(f"  Activée: [green]Oui[/green]")
        console.print(f"  Chiffrement: [green]{'Oui' if security_info['encryption_enabled'] else 'Non'}[/green]")
        console.print(f"  Signatures: [green]{'Oui' if security_info['signing_enabled'] else 'Non'}[/green]")
        console.print(f"  Identité actuelle: {security_info['current_identity']}")
        console.print(f"  Identités disponibles: {security_info['identities_count']}")

        if 'security_stats' in security_info:
            stats = security_info['security_stats']
            console.print(f"  Messages chiffrés: {stats['stats']['messages_encrypted']}")
            console.print(f"  Messages signés: {stats['stats']['messages_signed']}")
            console.print(f"  Messages vérifiés: {stats['stats']['messages_verified']}")
            console.print(f"  Échecs de sécurité: {stats['stats']['security_failures']}")

    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('document', type=click.Path(exists=True))
@click.option('--destination', '-d', help='Callsign destinataire')
@click.option('--secure', '-s', is_flag=True, help='Utiliser transmission sécurisée')
@click.option('--identity', '-i', help='Identité pour sécurisation')
@click.option('--recipient', '-r', help='Identité du destinataire')
@click.pass_context
@async_command
async def transmit_secure(ctx, document, destination, secure, identity, recipient):
    """Transmettre un document de manière sécurisée"""
    if not secure and not identity and not recipient:
        console.print("[red]Utilisez --secure, --identity ou --recipient pour la transmission sécurisée[/red]")
        sys.exit(1)

    try:
        config = ctx.obj.get('config', {}).copy()

        if secure or identity or recipient:
            config.update({
                'security_enabled': True,
                'encryption_enabled': True,
                'signing_enabled': True,
                'identity_name': identity or 'default_user',
            })

        system = DNFMMLMorseSystem(config)

        if secure and not system.security_enabled:
            success = system.enable_security(identity)
            if not success:
                console.print("[red]Impossible d'activer la sécurité[/red]")
                sys.exit(1)

        console.print(f"Transmission sécurisée de {document}...")

        if secure:
            result = await system.transmit_secure_document(document, destination, recipient)
        else:
            result = await system.transmit_document(document, destination)

        if result['success']:
            console.print("[green]✓ Transmission réussie![/green]")

            if result.get('secure'):
                console.print(f"  Sécurisé: [green]Oui[/green]")
                console.print(f"  Chiffré: {'Oui' if result.get('encrypted') else 'Non'}")
                console.print(f"  Signé: {'Oui' if result.get('signed') else 'Non'}")
                console.print(f"  Identité: {result.get('sender_identity', 'N/A')}")

            console.print(f"  Fragments: {result['fragments_sent']}")
            console.print(f"  Ratio compression: {result['compression_ratio']:.2%}")
            console.print(f"  Durée: {result.get('transmission_time', 'N/A')}s")

        else:
            console.print(f"[red]❌ Échec: {result['error']}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        sys.exit(1)


def main():
    """Point d'entrée principal"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompu par l'utilisateur[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Erreur fatale: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
