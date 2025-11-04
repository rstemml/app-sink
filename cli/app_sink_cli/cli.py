"""
App-Sink CLI - Main command-line interface
"""

import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from tabulate import tabulate

from .config import config
from .api_client import APIClient
from .analyzer import LocalAnalyzer

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    App-Sink CLI - Deploy apps to Kubernetes with AI

    A simple CLI to deploy and manage applications on your App-Sink cluster.
    """
    pass


# ============================================================================
# Configuration Commands
# ============================================================================

@cli.group()
def config_cmd():
    """Manage CLI configuration"""
    pass


@config_cmd.command("init")
def config_init():
    """Interactive configuration setup"""
    console.print("\n[bold blue]App-Sink Configuration[/bold blue]\n")

    endpoint = click.prompt("API Endpoint (e.g., https://api.example.com)", type=str)
    api_key = click.prompt("API Key", type=str, hide_input=True)
    default_domain = click.prompt("Default Domain (optional)", type=str, default="", show_default=False)

    config.set("endpoint", endpoint)
    config.set("api_key", api_key)
    if default_domain:
        config.set("default_domain", default_domain)

    console.print("\n[green]✓ Configuration saved![/green]")
    console.print(f"Config file: {config.config_file}\n")


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set configuration value"""
    config.set(key, value)
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@config_cmd.command("get")
@click.argument("key")
def config_get(key):
    """Get configuration value"""
    value = config.get(key)
    if value:
        console.print(f"{key}: {value}")
    else:
        console.print(f"[yellow]{key} not set[/yellow]")


@config_cmd.command("show")
def config_show():
    """Show all configuration"""
    console.print("\n[bold]Current Configuration:[/bold]\n")
    console.print(f"Endpoint: {config.endpoint or '[red]Not set[/red]'}")
    console.print(f"API Key: {'[green]Set[/green]' if config.api_key else '[red]Not set[/red]'}")
    console.print(f"Default Domain: {config.default_domain or '[yellow]Not set[/yellow]'}")
    console.print(f"\nConfig file: {config.config_file}\n")


# ============================================================================
# Deployment Commands
# ============================================================================

@cli.command()
@click.option("--name", "-n", help="Application name (auto-detected if not provided)")
@click.option("--image", "-i", help="Docker image (e.g., ghcr.io/user/app:tag)")
@click.option("--port", "-p", type=int, help="Container port")
@click.option("--domain", "-d", help="Custom domain")
@click.option("--replicas", "-r", type=int, default=1, help="Number of replicas")
@click.option("--env", "-e", multiple=True, help="Environment variables (key=value)")
@click.option("--cpu", help="CPU limit (e.g., 500m, 1)")
@click.option("--memory", help="Memory limit (e.g., 512Mi, 1Gi)")
@click.option("--dry-run", is_flag=True, help="Show generated config without deploying")
def deploy(name, image, port, domain, replicas, env, cpu, memory, dry_run):
    """
    Deploy application with AI-powered analysis

    Examples:
      app-sink deploy                           # Auto-detect everything
      app-sink deploy --image user/app:v1.0     # Provide image
      app-sink deploy --domain myapp.com        # Custom domain
    """
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        # Get current directory
        repo_path = os.getcwd()

        # Analyze repository with AI
        console.print("\n[blue]🤖 Analyzing repository with AI...[/blue]\n")

        analyzer = LocalAnalyzer()
        analysis = analyzer.analyze_local_repo(repo_path, name)

        console.print(f"[green]✓ Detected: {analysis['detected_language']}[/green]")
        if analysis.get('detected_framework'):
            console.print(f"  Framework: {analysis['detected_framework']}")
        if analysis.get('detected_port'):
            console.print(f"  Port: {analysis['detected_port']}")

        # Use CLI arguments or AI detection
        app_name = name or analysis['deployment_config']['name']
        app_port = port or analysis['deployment_config']['port']
        app_image = image or analysis['deployment_config']['image']

        if not image:
            console.print("\n[yellow]⚠ No image provided. Please specify with --image[/yellow]")
            suggested_image = f"ghcr.io/your-username/{app_name}:latest"
            console.print(f"  Example: app-sink deploy --image {suggested_image}\n")
            sys.exit(1)

        # Parse environment variables
        env_dict = {}
        for e in env:
            if "=" in e:
                k, v = e.split("=", 1)
                env_dict[k] = v

        # Merge with AI suggested env vars
        for env_var in analysis.get('suggested_env_vars', []):
            if env_var not in env_dict:
                # Ask user for value if not provided
                pass  # Could prompt here

        # Build deployment config
        deployment = {
            "name": app_name,
            "image": app_image,
            "port": app_port,
            "domain": domain,
            "replicas": replicas,
            "env": env_dict,
            "resources": {
                "cpu": cpu or analysis['deployment_config']['resources']['cpu'],
                "memory": memory or analysis['deployment_config']['resources']['memory']
            }
        }

        if dry_run:
            console.print("\n[bold]Generated Deployment Configuration:[/bold]\n")
            import json
            console.print(json.dumps(deployment, indent=2))
            console.print("\n[yellow]Dry run - no deployment created[/yellow]\n")
            return

        # Deploy via API
        console.print("\n[blue]🚀 Deploying to App-Sink...[/blue]\n")

        client = APIClient()
        result = client.create_app(deployment)

        console.print(f"[green]✓ Deployed successfully![/green]")
        console.print(f"\nName: {result['name']}")
        console.print(f"Status: {result['status']}")
        if result.get('url'):
            console.print(f"URL: [link]{result['url']}[/link]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--image", "-i", help="Update Docker image")
@click.option("--replicas", "-r", type=int, help="Update replicas")
@click.option("--domain", "-d", help="Update domain")
def update(name, image, replicas, domain):
    """Update application deployment"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        update_data = {}
        if image:
            update_data["image"] = image
        if replicas is not None:
            update_data["replicas"] = replicas
        if domain:
            update_data["domain"] = domain

        if not update_data:
            console.print("[yellow]No updates specified[/yellow]")
            return

        client = APIClient()
        result = client.update_app(name, update_data)

        console.print(f"[green]✓ Updated {name}[/green]")
        if result.get('url'):
            console.print(f"URL: {result['url']}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.argument("replicas", type=int)
def scale(name, replicas):
    """Scale application replicas"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        client.scale_app(name, replicas)
        console.print(f"[green]✓ Scaled {name} to {replicas} replicas[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this app?")
def delete(name):
    """Delete application"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        client.delete_app(name)
        console.print(f"[green]✓ Deleted {name}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command("list")
def list_apps():
    """List all applications"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        apps = client.list_apps()

        if not apps:
            console.print("[yellow]No applications deployed[/yellow]")
            return

        # Create table
        table = Table(title="Deployed Applications")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Replicas", justify="center")
        table.add_column("Image", style="blue")
        table.add_column("Domain", style="magenta")

        for app in apps:
            table.add_row(
                app['name'],
                app['status'],
                str(app['replicas']),
                app['image'].split('/')[-1][:40],  # Truncate image
                app.get('domain', '-')
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("name")
def get(name):
    """Get application details"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        app = client.get_app(name)

        console.print(f"\n[bold]Application: {app['name']}[/bold]\n")
        console.print(f"Status: {app['status']}")
        console.print(f"Namespace: {app['namespace']}")
        console.print(f"Image: {app['image']}")
        console.print(f"Port: {app['port']}")
        console.print(f"Replicas: {app['replicas']}")
        if app.get('domain'):
            console.print(f"Domain: {app['domain']}")
        if app.get('url'):
            console.print(f"URL: [link]{app['url']}[/link]")

        if app.get('env_vars'):
            console.print("\nEnvironment Variables:")
            for k, v in app['env_vars'].items():
                console.print(f"  {k}: {v}")

        console.print()

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--tail", "-n", default=100, help="Number of lines to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(name, tail, follow):
    """Get application logs"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        logs = client.get_logs(name, tail)
        console.print(logs)

        # TODO: Implement follow with streaming

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to rollback?")
def rollback(name):
    """Rollback to previous deployment"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        result = client.rollback_app(name)
        console.print(f"[green]✓ Rolled back {name} to {result['image']}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


# ============================================================================
# Analysis Commands
# ============================================================================

@cli.command()
@click.argument("path", default=".")
def analyze(path):
    """Analyze repository with AI (without deploying)"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        console.print("\n[blue]🤖 Analyzing repository...[/blue]\n")

        analyzer = LocalAnalyzer()
        analysis = analyzer.analyze_local_repo(path)

        console.print(f"[green]Language:[/green] {analysis['detected_language']}")
        if analysis.get('detected_framework'):
            console.print(f"[green]Framework:[/green] {analysis['detected_framework']}")
        if analysis.get('package_manager'):
            console.print(f"[green]Package Manager:[/green] {analysis['package_manager']}")
        if analysis.get('entry_point'):
            console.print(f"[green]Entry Point:[/green] {analysis['entry_point']}")
        if analysis.get('detected_port'):
            console.print(f"[green]Port:[/green] {analysis['detected_port']}")

        if analysis.get('dependencies'):
            console.print(f"\n[bold]Dependencies:[/bold]")
            for dep in analysis['dependencies'][:5]:
                console.print(f"  • {dep}")

        console.print(f"\n[bold]Recommended Resources:[/bold]")
        console.print(f"  CPU: {analysis['recommended_resources']['cpu']}")
        console.print(f"  Memory: {analysis['recommended_resources']['memory']}")

        if analysis.get('suggested_env_vars'):
            console.print(f"\n[bold]Suggested Environment Variables:[/bold]")
            for var in analysis['suggested_env_vars']:
                console.print(f"  • {var}")

        console.print(f"\n[dim]Confidence: {analysis['confidence']:.0%}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Check App-Sink API status"""
    if not config.is_configured():
        console.print("[red]Error: CLI not configured. Run: app-sink config init[/red]")
        sys.exit(1)

    try:
        client = APIClient()
        health = client.health()

        status_color = "green" if health['status'] == "healthy" else "yellow"

        console.print(f"\n[{status_color}]Status: {health['status']}[/{status_color}]")
        console.print(f"Version: {health['version']}")
        console.print(f"Kubernetes: {'✓' if health['kubernetes'] else '✗'}")
        console.print(f"Database: {'✓' if health['database'] else '✗'}\n")

    except Exception as e:
        console.print(f"[red]API Unavailable: {str(e)}[/red]")
        sys.exit(1)


# Register config group
cli.add_command(config_cmd, name="config")


if __name__ == "__main__":
    cli()
