import os
import time
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# 1. Load Env
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key length: {len(api_key)}")

# 2. Configure code
GEMINI_BATCH_MODEL_NAME = "gemini-1.5-flash"
if api_key:
    genai.configure(api_key=api_key)

# 3. Test Logic
def test_generate():
    if not api_key:
        print("No API Key found.")
        return

    model_name = "gemini-flash-latest"
    model = genai.GenerativeModel(model_name)
    
    # Simple Prompt
    prompt = "Hello, are you working? Reply with JSON { \"status\": \"ok\" }"
    
    json_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"}
        }
    }
    
    config = GenerationConfig(
        response_mime_type="application/json",
        response_schema=json_schema
    )

    print(f"Requesting model: {model_name}...")
    try:
        response = model.generate_content(prompt, generation_config=config)
        print("Response received.")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_generate()
