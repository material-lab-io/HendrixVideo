"""
Comprehensive Captioning Pipeline

This module orchestrates the complete captioning process, from loading data
to generating captions and saving outputs.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import yaml

try:
    # Try relative imports first (when used as a package)
    from .data_fusion_engine import DataFusionEngine, SceneContextPacket
    from .caption_generator import CaptionGenerator, create_mllm_interface, GenerationConfig
    from .prompt_templates import get_prompt_template
    from .output_formats import OutputFormatter
except ImportError:
    # Fall back to direct imports (when run as script)
    from data_fusion_engine import DataFusionEngine, SceneContextPacket
    from caption_generator import CaptionGenerator, create_mllm_interface, GenerationConfig
    from prompt_templates import get_prompt_template
    from output_formats import OutputFormatter

logger = logging.getLogger(__name__)


class ComprehensiveCaptioningPipeline:
    """
    Main pipeline for comprehensive video captioning
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the pipeline
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.data_fusion_engine = None
        self.caption_generator = None
        self.output_formatter = None
        
        # Pipeline state
        self.context_packets = []
        self.generated_captions = []
        self.keyframe_mapping = {}  # scene_id -> keyframe_path
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "mllm": {
                "provider": "llava",
                "model": "llava-hf/llava-v1.6-vicuna-7b-hf",
                "generation": {
                    "temperature": 0.7,
                    "max_tokens": 200,
                    "top_p": 0.9
                }
            },
            "fusion": {
                "include_emotions": True,
                "include_visual_descriptions": True,
                "min_dialogue_confidence": 0.5
            },
            "prompt": {
                "template": "narrative_with_emotions"
            },
            "output": {
                "formats": ["json", "srt", "webvtt"],
                "include_metadata": True
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                return self._merge_configs(default_config, user_config)
        
        return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def initialize_components(self, 
                            audio_analysis_path: str,
                            scene_analysis_path: str,
                            mllm_api_key: Optional[str] = None):
        """
        Initialize all pipeline components
        
        Args:
            audio_analysis_path: Path to audio analysis output
            scene_analysis_path: Path to scenes.json
            mllm_api_key: API key for MLLM (not needed for LLaVA)
        """
        logger.info("Initializing pipeline components...")
        
        # Initialize data fusion engine
        self.data_fusion_engine = DataFusionEngine(
            audio_analysis_path=audio_analysis_path,
            scene_analysis_path=scene_analysis_path,
            include_emotions=self.config["fusion"]["include_emotions"],
            min_dialogue_confidence=self.config["fusion"]["min_dialogue_confidence"]
        )
        
        # Initialize MLLM interface
        gen_config = GenerationConfig(**self.config["mllm"]["generation"])
        mllm_interface = create_mllm_interface(
            provider=self.config["mllm"]["provider"],
            api_key=mllm_api_key,
            model_name=self.config["mllm"]["model"],
            config=gen_config
        )
        
        # Initialize caption generator
        prompt_template_name = self.config["prompt"]["template"]
        use_improved = self.config.get("prompt", {}).get("use_improved_templates", True)
        self.caption_generator = CaptionGenerator(
            mllm_interface=mllm_interface,
            prompt_template=prompt_template_name,
            use_improved_templates=use_improved
        )
        
        # Initialize output formatter
        self.output_formatter = OutputFormatter(
            formats=self.config["output"]["formats"],
            include_metadata=self.config["output"]["include_metadata"]
        )
        
        logger.info("All components initialized successfully")
    
    def load_keyframe_mapping(self, keyframes_dir: Optional[str] = None):
        """
        Load mapping of scene IDs to keyframe paths
        
        Args:
            keyframes_dir: Directory containing keyframe images
        """
        if not keyframes_dir:
            logger.info("No keyframes directory provided, skipping keyframe mapping")
            return
            
        keyframes_path = Path(keyframes_dir)
        if not keyframes_path.exists():
            logger.warning(f"Keyframes directory not found: {keyframes_dir}")
            return
        
        # Look for keyframe images
        for image_file in keyframes_path.glob("*.jpg"):
            # Extract scene ID from filename (assuming format like "shot_0001.jpg")
            try:
                filename = image_file.stem
                if filename.startswith("shot_"):
                    shot_id = int(filename.split("_")[1])
                    # Map shot to scene (this is simplified, may need scene data)
                    self.keyframe_mapping[shot_id] = str(image_file)
            except (ValueError, IndexError):
                continue
        
        logger.info(f"Loaded {len(self.keyframe_mapping)} keyframe mappings")
    
    def process_scenes(self) -> List[SceneContextPacket]:
        """
        Process all scenes and create context packets
        
        Returns:
            List of context packets
        """
        logger.info("Processing scenes to create context packets...")
        
        self.context_packets = self.data_fusion_engine.process_all_scenes()
        
        logger.info(f"Created {len(self.context_packets)} context packets")
        return self.context_packets
    
    def generate_captions(self, use_keyframes: bool = True) -> List[Dict[str, Any]]:
        """
        Generate captions for all scenes
        
        Args:
            use_keyframes: Whether to use keyframe images for visual context
            
        Returns:
            List of generated captions
        """
        logger.info("Generating captions for all scenes...")
        
        self.generated_captions = []
        
        for i, context in enumerate(self.context_packets):
            logger.info(f"Processing scene {context.scene_id} ({i+1}/{len(self.context_packets)})")
            
            # Get keyframe if available
            keyframe_path = None
            if use_keyframes and context.shot_ids:
                # Use first shot's keyframe
                shot_id = context.shot_ids[0] if context.shot_ids else None
                keyframe_path = self.keyframe_mapping.get(shot_id)
            
            try:
                # Generate caption
                caption_text = self.caption_generator.generate_scene_caption(
                    context, 
                    keyframe_path=keyframe_path
                )
                
                # Create caption entry
                caption_entry = {
                    "caption_id": f"SCENE_CAP_{context.scene_id:03d}",
                    "scene_id": context.scene_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time,
                    "duration": context.end_time - context.start_time,
                    "caption": caption_text,
                    "characters": context.characters_present,
                    "has_dialogue": len(context.dialogue_transcript) > 0,
                    "keyframe_used": keyframe_path is not None
                }
                
                self.generated_captions.append(caption_entry)
                
                # Update context for next scene with smart summarization
                if i < len(self.context_packets) - 1 and self.config["pipeline"]["update_context"]:
                    # Create a concise summary for context (max 50 words)
                    summary = self._create_concise_summary(caption_text)
                    self.context_packets[i + 1].prior_scene_summary = summary
                
            except Exception as e:
                logger.error(f"Failed to generate caption for scene {context.scene_id}: {e}")
                
                # Add error caption
                caption_entry = {
                    "caption_id": f"SCENE_CAP_{context.scene_id:03d}",
                    "scene_id": context.scene_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time,
                    "duration": context.end_time - context.start_time,
                    "caption": f"[Caption generation failed: {str(e)}]",
                    "characters": context.characters_present,
                    "has_dialogue": len(context.dialogue_transcript) > 0,
                    "error": str(e)
                }
                self.generated_captions.append(caption_entry)
        
        logger.info(f"Generated {len(self.generated_captions)} captions")
        return self.generated_captions
    
    def save_outputs(self, output_dir: str) -> Dict[str, str]:
        """
        Save all outputs in configured formats
        
        Args:
            output_dir: Directory to save outputs
            
        Returns:
            Dictionary mapping format to file path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Prepare output data
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_scenes": len(self.generated_captions),
                "total_duration": sum(c["duration"] for c in self.generated_captions),
                "pipeline_config": self.config
            },
            "captions": self.generated_captions
        }
        
        # Save in different formats
        saved_files = self.output_formatter.save_all_formats(
            output_data,
            output_path,
            base_filename="comprehensive_captions"
        )
        
        # Also save context packets for debugging
        context_file = output_path / "context_packets.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_packets": len(self.context_packets),
                "packets": [p.to_dict() for p in self.context_packets]
            }, f, indent=2, ensure_ascii=False)
        saved_files["context"] = str(context_file)
        
        logger.info(f"Saved outputs to {output_dir}")
        return saved_files
    
    def _create_concise_summary(self, caption_text: str, max_words: int = 30) -> str:
        """Create a concise summary of the caption for context"""
        # Simple word-based truncation with smart ending
        words = caption_text.split()
        if len(words) <= max_words:
            return caption_text
        
        # Find a good stopping point (end of sentence within limit)
        summary_words = words[:max_words]
        summary = " ".join(summary_words)
        
        # Try to end at a sentence boundary
        last_period = summary.rfind('.')
        last_comma = summary.rfind(',')
        
        if last_period > len(summary) * 0.6:  # If period is in last 40% of text
            summary = summary[:last_period + 1]
        elif last_comma > len(summary) * 0.7:  # If comma is in last 30% of text
            summary = summary[:last_comma] + "..."
        else:
            summary = summary.rstrip() + "..."
        
        return summary
    
    def run(self, 
            audio_analysis_path: str,
            scene_analysis_path: str,
            output_dir: str,
            keyframes_dir: Optional[str] = None,
            mllm_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete captioning pipeline
        
        Args:
            audio_analysis_path: Path to audio analysis output
            scene_analysis_path: Path to scenes.json
            output_dir: Directory to save outputs
            keyframes_dir: Optional directory containing keyframes
            mllm_api_key: Optional API key for MLLM
            
        Returns:
            Dictionary with pipeline results
        """
        start_time = datetime.now()
        
        logger.info("Starting comprehensive captioning pipeline...")
        
        # Initialize components
        self.initialize_components(
            audio_analysis_path,
            scene_analysis_path,
            mllm_api_key
        )
        
        # Load keyframe mapping if available
        if keyframes_dir:
            self.load_keyframe_mapping(keyframes_dir)
        
        # Process scenes
        self.process_scenes()
        
        # Generate captions
        self.generate_captions(use_keyframes=bool(keyframes_dir))
        
        # Save outputs
        saved_files = self.save_outputs(output_dir)
        
        # Calculate statistics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        results = {
            "status": "success",
            "processing_time": processing_time,
            "total_scenes": len(self.generated_captions),
            "successful_captions": sum(1 for c in self.generated_captions if "error" not in c),
            "failed_captions": sum(1 for c in self.generated_captions if "error" in c),
            "saved_files": saved_files,
            "timestamp": end_time.isoformat()
        }
        
        logger.info(f"Pipeline completed in {processing_time:.2f} seconds")
        logger.info(f"Generated {results['successful_captions']} successful captions")
        
        return results


def main():
    """Run pipeline from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive captioning pipeline")
    parser.add_argument("--audio-analysis", required=True, help="Path to audio analysis output")
    parser.add_argument("--scene-analysis", required=True, help="Path to scenes.json")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--keyframes", help="Directory containing keyframe images")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--api-key", help="API key for MLLM (if needed)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run pipeline
    pipeline = ComprehensiveCaptioningPipeline(args.config)
    
    results = pipeline.run(
        audio_analysis_path=args.audio_analysis,
        scene_analysis_path=args.scene_analysis,
        output_dir=args.output_dir,
        keyframes_dir=args.keyframes,
        mllm_api_key=args.api_key
    )
    
    print(f"\nPipeline Results:")
    print(f"  Status: {results['status']}")
    print(f"  Processing Time: {results['processing_time']:.2f}s")
    print(f"  Total Scenes: {results['total_scenes']}")
    print(f"  Successful Captions: {results['successful_captions']}")
    print(f"  Failed Captions: {results['failed_captions']}")
    print(f"\nOutput Files:")
    for format_name, filepath in results['saved_files'].items():
        print(f"  {format_name}: {filepath}")


if __name__ == "__main__":
    main()