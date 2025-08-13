#!/usr/bin/env python3
"""Test LLaVA directly to debug generation issues"""

import sys
sys.path.append('/dev-work/comprehensive_captioning')

from comprehensive_captioning.caption_generator import LLaVAInterface

# Create interface
interface = LLaVAInterface(api_key=None, model_name="llava-hf/llava-v1.6-vicuna-7b-hf", config={})

# Test with a simple prompt
simple_prompt = "Hello, can you describe what you see in this scene?"
print("Testing with simple prompt...")
try:
    result = interface.generate_caption(simple_prompt)
    print(f"Result: '{result}'")
    print(f"Length: {len(result)}")
except Exception as e:
    print(f"Error: {e}")

# Test with a more complex prompt
complex_prompt = """You are a helpful assistant. Please describe the following scene:

A person is walking in a park. There are trees and flowers around.

Please provide a brief 2-3 sentence description."""

print("\nTesting with complex prompt...")
try:
    result = interface.generate_caption(complex_prompt)
    print(f"Result: '{result}'")
    print(f"Length: {len(result)}")
except Exception as e:
    print(f"Error: {e}")