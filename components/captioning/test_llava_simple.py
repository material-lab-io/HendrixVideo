#!/usr/bin/env python3
"""Direct test of LLaVA model"""

from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch

print("Loading model...")
model_name = "llava-hf/llava-v1.6-vicuna-7b-hf"
processor = LlavaNextProcessor.from_pretrained(model_name)
model = LlavaNextForConditionalGeneration.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

print(f"Model loaded on device: {model.device}")

# Test prompt
prompt = "USER: Hello, please describe a beautiful sunset over the ocean in 2-3 sentences. ASSISTANT:"

print(f"\nPrompt: {prompt}")
print("-" * 50)

# Process and generate
inputs = processor(text=prompt, return_tensors="pt")
inputs = {k: v.to(model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

print(f"Input shape: {inputs['input_ids'].shape}")

with torch.no_grad():
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id
    )

print(f"Generated shape: {generate_ids.shape}")

# Decode
generated_text = processor.batch_decode(
    generate_ids[:, inputs['input_ids'].shape[1]:], 
    skip_special_tokens=True, 
    clean_up_tokenization_spaces=True
)[0]

print(f"\nGenerated text: '{generated_text}'")
print(f"Length: {len(generated_text)}")