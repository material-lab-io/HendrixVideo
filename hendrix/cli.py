"""
Hendrix Video Analysis CLI

Modern command-line interface for the hendrix video analysis pipeline.
"""

import sys
from pathlib import Path
from typing import List, Optional
import click
import logging

from .core.pipeline import Pipeline
from .core.config import ConfigManager, list_all_models
from .core.exceptions import HendrixError
from .__version__ import __version__

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="hendrix")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def main(ctx, verbose):
    """
    Hendrix Video Analysis Pipeline
    
    AI-powered video analysis for shot detection, transcription, and caption generation.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        

@main.command()
@click.argument('video_path', type=click.Path(exists=True))
@click.option('--output', '-o', 'output_dir', help='Output directory')
@click.option('--profile', '-p', default='balanced', 
              type=click.Choice(['fast', 'balanced', 'quality', 'test']),
              help='Configuration profile to use')
@click.option('--components', '-c', multiple=True,
              type=click.Choice(['video', 'audio', 'caption']),
              help='Components to run (default: all)')
@click.option('--model', '-m', 'vlm_model', help='Vision-language model to use')
@click.option('--whisper-model', default='base', 
              type=click.Choice(['tiny', 'base', 'small', 'medium', 'large']),
              help='Whisper model size for audio transcription')
@click.option('--device', help='Device to use (cuda:0, cuda:1, cpu, auto)')
@click.option('--quantize', type=click.Choice(['8bit', '4bit']),
              help='Model quantization to reduce memory usage')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.pass_context
def analyze(
    ctx, 
    video_path: str, 
    output_dir: Optional[str],
    profile: str,
    components: tuple,
    vlm_model: Optional[str],
    whisper_model: str,
    device: Optional[str],
    quantize: Optional[str],
    dry_run: bool
):
    """Analyze a video file and generate captions."""
    
    try:
        # Load configuration
        config = ConfigManager(profile=profile)
        
        # Apply CLI overrides
        if vlm_model:
            config.set_active_model(vlm_model)
        if whisper_model:
            config.set("audio_models.whisper.model", whisper_model)
        if device:
            config.set("pipeline.device", device)
        if quantize:
            active_model = config.get("active_model")
            if active_model:
                config.set(f"models.{active_model}.device_config.load_in_{quantize}", True)
        
        # Set components to run
        components_to_run = list(components) if components else ["video", "audio", "caption"]
        
        if dry_run:
            _show_dry_run_info(video_path, config, components_to_run, output_dir)
            return
        
        # Create and run pipeline
        pipeline = Pipeline(config)
        
        click.echo(f"🎬 Analyzing video: {video_path}")
        click.echo(f"📊 Profile: {profile}")
        click.echo(f"🧩 Components: {', '.join(components_to_run)}")
        
        results = pipeline.analyze(
            video_path, 
            output_dir=output_dir,
            components=components_to_run
        )
        
        click.echo(f"✅ Analysis complete!")
        click.echo(f"📁 Results saved to: {results['output_dir']}")
        
        # Show summary
        for component, result in results.get('results', {}).items():
            status = result.get('status', 'unknown')
            if status == 'success':
                click.echo(f"   ✓ {component}: Success")
            elif status == 'failed':
                click.echo(f"   ✗ {component}: Failed - {result.get('error', 'Unknown error')}")
            else:
                click.echo(f"   - {component}: {status}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@main.command()
@click.option('--config', '-c', help='Path to config file')
def verify(config: Optional[str]):
    """Verify installation and dependencies."""
    
    try:
        pipeline = Pipeline(config)
        verification = pipeline.verify_installation()
        
        click.echo("🔍 Verifying Hendrix Pipeline installation...")
        click.echo()
        
        # Show component status
        for component, status in verification.get('components', {}).items():
            click.echo(f"  {component}: {status}")
        
        click.echo()
        
        # Show overall status
        if verification['status'] == 'success':
            click.echo("✅ Installation verified successfully!")
        else:
            click.echo("❌ Installation issues found:")
            for issue in verification.get('issues', []):
                click.echo(f"  - {issue}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Verification failed: {e}", err=True)
        sys.exit(1)


@main.command('list-models')
@click.option('--config', '-c', help='Path to config file')
def list_models_cmd(config: Optional[str]):
    """List available AI models."""
    try:
        list_all_models(config or "configs/base_config.yaml")
    except Exception as e:
        click.echo(f"❌ Error listing models: {e}", err=True)


@main.command('download-models')
@click.option('--model', '-m', multiple=True, help='Specific models to download')
@click.option('--minimal', is_flag=True, help='Download only essential models')
@click.option('--all', 'download_all', is_flag=True, help='Download all available models')
@click.option('--cache-dir', help='Directory to cache downloaded models')
def download_models(
    model: tuple, 
    minimal: bool, 
    download_all: bool, 
    cache_dir: Optional[str]
):
    """Download AI models for offline use."""
    
    click.echo("🔄 Model download functionality coming soon!")
    click.echo()
    click.echo("For now, models will be downloaded automatically when first used.")
    click.echo("This requires an internet connection.")
    
    # TODO: Implement actual model downloading
    if minimal:
        click.echo("📦 Minimal models would include:")
        click.echo("  - Basic Whisper model for transcription")
        click.echo("  - Lightweight vision model for shot detection")
    
    if download_all:
        click.echo("📦 All models would include:")
        click.echo("  - All Whisper variants (tiny to large)")
        click.echo("  - LLaVA 7B and 13B vision-language models")
        click.echo("  - Speaker diarization models")


@main.command()
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['json', 'yaml', 'table']), 
              default='table',
              help='Output format')
def config(output_format: str):
    """Show current configuration."""
    
    try:
        config_manager = ConfigManager()
        config_data = config_manager.to_dict()
        
        if output_format == 'json':
            import json
            click.echo(json.dumps(config_data, indent=2))
        elif output_format == 'yaml':
            import yaml
            click.echo(yaml.dump(config_data, default_flow_style=False))
        else:
            # Table format - show key information
            click.echo("📋 Current Hendrix Configuration")
            click.echo()
            click.echo(f"Active Model: {config_data.get('active_model', 'Not set')}")
            click.echo(f"Device: {config_data.get('pipeline', {}).get('device', 'Auto')}")
            click.echo(f"Batch Size: {config_data.get('pipeline', {}).get('batch_size', 'Not set')}")
            
            whisper_model = config_data.get('audio_models', {}).get('whisper', {}).get('model', 'Not set')
            click.echo(f"Whisper Model: {whisper_model}")
            
    except Exception as e:
        click.echo(f"❌ Error reading configuration: {e}", err=True)


def _show_dry_run_info(
    video_path: str, 
    config: ConfigManager, 
    components: List[str], 
    output_dir: Optional[str]
):
    """Show what would be executed in a dry run"""
    
    click.echo("=" * 50)
    click.echo("🔍 DRY RUN - No processing will be performed")
    click.echo("=" * 50)
    click.echo()
    
    click.echo(f"📹 Input video: {video_path}")
    click.echo(f"🧩 Components to run: {', '.join(components)}")
    
    active_model = config.get('active_model', 'Not set')
    whisper_model = config.get('audio_models.whisper.model', 'Not set') 
    device = config.get('pipeline.device', 'Auto')
    
    click.echo()
    click.echo("🤖 Active models:")
    click.echo(f"  Vision-Language: {active_model}")
    click.echo(f"  Whisper: {whisper_model}")
    click.echo(f"  Device: {device}")
    
    output_formats = config.get('output.formats', [])
    click.echo(f"📄 Output formats: {', '.join(output_formats)}")
    
    if output_dir:
        click.echo(f"📁 Output directory: {output_dir}")
    else:
        click.echo("📁 Output directory: Auto-generated")
    
    click.echo()
    click.echo("▶️  To execute, remove the --dry-run flag")


if __name__ == '__main__':
    main()