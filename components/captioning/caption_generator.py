"""
Caption Generator with MLLM Interface

This module provides interfaces for various Multi-modal Large Language Models (MLLMs)
to generate narrative captions from scene context data.
"""

import os
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import requests

try:
    from .data_fusion_engine import SceneContextPacket
except ImportError:
    from data_fusion_engine import SceneContextPacket
try:
    from .prompt_templates import PromptTemplate, get_prompt_template
except ImportError:
    from prompt_templates import PromptTemplate, get_prompt_template

try:
    from .prompt_templates_improved import ImprovedPromptTemplate, get_improved_template
    IMPROVED_TEMPLATES_AVAILABLE = True
except ImportError:
    try:
        from prompt_templates_improved import ImprovedPromptTemplate, get_improved_template
        IMPROVED_TEMPLATES_AVAILABLE = True
    except ImportError:
        IMPROVED_TEMPLATES_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    max_tokens: int = 200
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = None
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


class MLLMInterface(ABC):
    """Abstract base class for MLLM interfaces"""
    
    def __init__(self, api_key: str, model_name: str, config: GenerationConfig = None):
        self.api_key = api_key
        self.model_name = model_name
        self.config = config or GenerationConfig()
    
    @abstractmethod
    def generate_caption(self, prompt: str) -> str:
        """Generate caption from prompt"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available"""
        pass


class LLaVAInterface(MLLMInterface):
    """
    Interface for LLaVA-NeXT (LLaVA 1.6) models
    This integrates with the local LLaVA model already available in Hendrix_Video_Analysis
    """
    
    def __init__(self, api_key: str = None, model_name: str = "llava-hf/llava-v1.6-vicuna-7b-hf", 
                 config: GenerationConfig = None):
        # api_key not used for local model, but kept for interface compatibility
        super().__init__(api_key or "local", model_name, config)
        self.model = None
        self.processor = None
        self.device = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLaVA model and processor"""
        try:
            import torch
            from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
            
            # Determine device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Initializing LLaVA-NeXT on {self.device}")
            
            # Load processor and model
            self.processor = LlavaNextProcessor.from_pretrained(self.model_name)
            self.model = LlavaNextForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True
            )
            
            # Move model to device
            self.model = self.model.to(self.device)
            self.model.eval()
            
            logger.info("LLaVA-NeXT model loaded successfully")
            
        except ImportError as e:
            logger.error(f"Required dependencies not found: {e}")
            logger.error("Please install: pip install transformers torch pillow")
            raise
        except Exception as e:
            logger.error(f"Error initializing LLaVA-NeXT: {e}")
            raise
    
    def generate_caption(self, prompt: str, image_path: Optional[str] = None) -> str:
        """
        Generate caption using LLaVA-NeXT
        
        Args:
            prompt: Text prompt
            image_path: Optional path to image for visual context
            
        Returns:
            Generated caption text
        """
        try:
            import torch
            from PIL import Image
            
            # Prepare inputs
            if image_path and os.path.exists(image_path):
                # Load and process image if provided
                image = Image.open(image_path).convert("RGB")
                # LLaVA requires <image> token in prompt when using images
                if "<image>" not in prompt:
                    prompt = "<image>\n" + prompt
                inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            else:
                # Text-only input
                inputs = self.processor(text=prompt, return_tensors="pt")
            
            # Move inputs to device
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                     for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                generate_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    do_sample=True if self.config.temperature > 0 else False,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id
                )
            
            # Decode the generated text
            generated_text = self.processor.batch_decode(
                generate_ids[:, inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=True
            )[0]
            
            # Debug logging
            if len(generated_text.strip()) < 10:
                logger.debug(f"Short caption generated. Prompt length: {len(prompt)}")
                logger.debug(f"Input IDs shape: {inputs['input_ids'].shape}")
                logger.debug(f"Generated IDs shape: {generate_ids.shape}")
                logger.debug(f"Raw generated text: '{generated_text}'")
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Error generating with LLaVA-NeXT: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LLaVA-NeXT is available"""
        return self.model is not None and self.processor is not None


class OpenAIInterface(MLLMInterface):
    """
    Interface for OpenAI models (GPT-4, etc.)
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4", 
                 config: GenerationConfig = None):
        super().__init__(api_key, model_name, config)
        self.base_url = "https://api.openai.com/v1"
        
        # Import OpenAI SDK if available
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.use_sdk = True
        except ImportError:
            logger.warning("OpenAI SDK not found. Using REST API instead.")
            self.client = None
            self.use_sdk = False
    
    def generate_caption(self, prompt: str) -> str:
        """Generate caption using OpenAI"""
        if self.use_sdk:
            return self._generate_with_sdk(prompt)
        else:
            return self._generate_with_api(prompt)
    
    def _generate_with_sdk(self, prompt: str) -> str:
        """Generate using OpenAI SDK"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional video caption writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                stop=self.config.stop_sequences if self.config.stop_sequences else None
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating with OpenAI SDK: {e}")
            raise
    
    def _generate_with_api(self, prompt: str) -> str:
        """Generate using REST API"""
        endpoint = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a professional video caption writer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty
        }
        
        if self.config.stop_sequences:
            data["stop"] = self.config.stop_sequences
        
        try:
            response = requests.post(endpoint, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Error generating with OpenAI API: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        try:
            endpoint = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(endpoint, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False


class MockMLLMInterface(MLLMInterface):
    """
    Mock MLLM for testing without API calls
    """
    
    def generate_caption(self, prompt: str) -> str:
        """Generate a mock caption"""
        # Extract some context from the prompt
        lines = prompt.split('\n')
        scene_time = None
        characters = None
        
        for line in lines:
            if "Scene Timestamp:" in line:
                scene_time = line.split(":")[-1].strip()
            elif "Characters Present:" in line:
                characters = line.split(":")[-1].strip()
        
        # Generate a simple mock caption
        if characters and characters != "No identified characters":
            return f"In this scene, {characters} engage in a meaningful interaction that advances the plot."
        else:
            return "The scene unfolds with visual elements that contribute to the narrative progression."
    
    def is_available(self) -> bool:
        """Mock is always available"""
        return True


class CaptionGenerator:
    """
    Main caption generator that uses MLLM interfaces
    """
    
    def __init__(self, 
                 mllm_interface: MLLMInterface,
                 prompt_template: Union[str, PromptTemplate] = "narrative",
                 retry_attempts: int = 3,
                 retry_delay: float = 1.0,
                 use_improved_templates: bool = True):
        """
        Initialize the caption generator
        
        Args:
            mllm_interface: The MLLM interface to use
            prompt_template: Template name or PromptTemplate instance
            retry_attempts: Number of retry attempts on failure
            retry_delay: Delay between retries in seconds
            use_improved_templates: Whether to use improved templates if available
        """
        self.mllm = mllm_interface
        
        if isinstance(prompt_template, str):
            # Try improved templates first if requested and available
            if use_improved_templates and IMPROVED_TEMPLATES_AVAILABLE:
                # Map old names to new improved versions
                template_mapping = {
                    "narrative": "enhanced_narrative",
                    "narrative_with_emotions": "narrative_emotions",
                    "descriptive": "concise_descriptive",
                    "summary": "action_focused"
                }
                improved_name = template_mapping.get(prompt_template, prompt_template)
                try:
                    self.prompt_template = get_improved_template(improved_name)
                    logger.info(f"Using improved template: {improved_name}")
                except:
                    self.prompt_template = get_prompt_template(prompt_template)
                    logger.info(f"Falling back to original template: {prompt_template}")
            else:
                self.prompt_template = get_prompt_template(prompt_template)
        else:
            self.prompt_template = prompt_template
            
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
    
    def generate_scene_caption(self, context: SceneContextPacket, 
                             keyframe_path: Optional[str] = None) -> str:
        """
        Generate a caption for a single scene
        
        Args:
            context: Scene context packet
            keyframe_path: Optional path to scene keyframe for visual context
            
        Returns:
            Generated caption text
        """
        # Generate the prompt
        prompt = self.prompt_template.generate_prompt(context)
        
        # Generate caption with retries
        for attempt in range(self.retry_attempts):
            try:
                # Check if MLLM supports image input (like LLaVA)
                if isinstance(self.mllm, LLaVAInterface) and keyframe_path:
                    caption = self.mllm.generate_caption(prompt, image_path=keyframe_path)
                else:
                    caption = self.mllm.generate_caption(prompt)
                
                # Basic validation
                if caption and len(caption) > 10:
                    return caption
                else:
                    logger.warning(f"Generated caption too short: {caption}")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
        
        # Fallback
        return "Caption generation failed after multiple attempts."
    
    def generate_captions_batch(self, contexts: List[SceneContextPacket], 
                              update_context: bool = True) -> List[Dict[str, Any]]:
        """
        Generate captions for multiple scenes
        
        Args:
            contexts: List of scene context packets
            update_context: Whether to update prior_scene_summary between scenes
            
        Returns:
            List of caption dictionaries
        """
        captions = []
        
        for i, context in enumerate(contexts):
            logger.info(f"Generating caption for scene {context.scene_id} ({i+1}/{len(contexts)})")
            
            try:
                # Generate caption
                caption_text = self.generate_scene_caption(context)
                
                # Create caption entry
                caption_entry = {
                    "caption_id": f"SCENE_CAP_{context.scene_id:03d}",
                    "scene_id": context.scene_id,
                    "start_time": context.start_time,
                    "end_time": context.end_time,
                    "duration": context.end_time - context.start_time,
                    "caption": caption_text,
                    "characters": context.characters_present,
                    "has_dialogue": len(context.dialogue_transcript) > 0
                }
                
                captions.append(caption_entry)
                
                # Update context for next scene
                if update_context and i < len(contexts) - 1:
                    contexts[i + 1].prior_scene_summary = caption_text
                
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
                captions.append(caption_entry)
        
        return captions


def create_mllm_interface(provider: str, api_key: str = None, model_name: str = None,
                         config: GenerationConfig = None) -> MLLMInterface:
    """
    Factory function to create MLLM interfaces
    
    Args:
        provider: Provider name (llava, openai, mock)
        api_key: API key for the provider (not needed for llava)
        model_name: Model name (optional, uses defaults)
        config: Generation configuration
        
    Returns:
        MLLMInterface instance
    """
    providers = {
        "llava": (LLaVAInterface, "llava-hf/llava-v1.6-vicuna-7b-hf"),
        "openai": (OpenAIInterface, "gpt-4"),
        "mock": (MockMLLMInterface, "mock-model")
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(providers.keys())}")
    
    interface_class, default_model = providers[provider]
    
    if provider in ["mock", "llava"]:
        return interface_class(api_key, model_name or default_model, config)
    
    return interface_class(api_key, model_name or default_model, config)


if __name__ == "__main__":
    # Test the caption generator
    try:
        from .data_fusion_engine import SceneContextPacket
    except ImportError:
        from data_fusion_engine import SceneContextPacket, DialogueEntry
    
    # Create a sample context
    sample_context = SceneContextPacket(
        scene_id=1,
        start_time=0.0,
        end_time=10.0,
        visual_description="A peaceful forest with sunlight filtering through trees",
        characters_present=["Character_1", "Character_2"],
        dialogue_transcript=[
            DialogueEntry(
                speaker="Character_1",
                character_id="1",
                text="Look at this beautiful place!",
                start_time=2.0,
                end_time=4.0,
                emotion="happy"
            )
        ],
        prior_scene_summary="The story begins."
    )
    
    # Test with mock interface
    mock_interface = MockMLLMInterface("mock-key", "mock-model")
    generator = CaptionGenerator(mock_interface)
    
    caption = generator.generate_scene_caption(sample_context)
    print(f"Generated caption: {caption}")