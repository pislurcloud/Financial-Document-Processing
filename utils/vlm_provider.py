"""
Vision Language Model Provider - Standalone Version
Multi-provider abstraction with automatic fallback
Copied from bill-management-agent for independence
"""

import os
import base64
import time
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# Model configurations
MODEL_PROVIDERS = {
    "openrouter_gemini": {
        "provider": "openrouter",
        "model": "google/gemini-2.5-flash",
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "supports_vision": True,
        "speed": "fast",
        "description": "Google Gemini Flash - Best for document processing"
    },
    
    "groq_llama_scout": {
        "provider": "groq",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "supports_vision": True,
        "speed": "very_fast",
        "description": "Llama 4 Scout - Fast fallback"
    }
}


class VLMProvider:
    """Vision Language Model provider interface"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        self.config = provider_config
        self.provider_name = provider_config["provider"]
        self.model_name = provider_config["model"]
        self.client = self._initialize_client()
        
        print(f"✅ Initialized VLM: {self.provider_name} - {self.model_name}")
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI-compatible client"""
        api_key_env = self.config["api_key_env"]
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(
                f"API key not found: {api_key_env}. "
                f"Please set it in your .env file."
            )
        
        client = OpenAI(
            api_key=api_key,
            base_url=self.config["base_url"]
        )
        
        return client
    
    def analyze_image(self, image_path: str, prompt: str, temperature: float = 0.1) -> str:
        """Analyze image using VLM"""
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        ext = image_path.split('.')[-1].lower()
        image_format = 'jpeg' if ext == 'jpg' else ext
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                temperature=temperature,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"VLM Error ({self.model_name}): {str(e)}")


class ModelManager:
    """Manages multiple VLM providers with automatic fallback"""
    
    def __init__(
        self, 
        primary_model: str = "openrouter_gemini",
        fallback_model: Optional[str] = "groq_llama_scout"
    ):
        self.primary_model_name = primary_model
        self.fallback_model_name = fallback_model
        
        print(f"\n🤖 Initializing Model Manager")
        print(f"   Primary: {primary_model}")
        print(f"   Fallback: {fallback_model if fallback_model else 'None'}")
        print()
        
        # Initialize providers
        try:
            self.primary = VLMProvider(MODEL_PROVIDERS[primary_model])
        except Exception as e:
            print(f"❌ Failed to initialize primary model: {e}")
            raise
        
        if fallback_model:
            try:
                self.fallback = VLMProvider(MODEL_PROVIDERS[fallback_model])
            except Exception as e:
                print(f"⚠️  Failed to initialize fallback model: {e}")
                self.fallback = None
        else:
            self.fallback = None
        
        print()
    
    def analyze_image_with_fallback(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Analyze image with automatic fallback"""
        start_time = time.time()
        
        # Try primary model
        try:
            response = self.primary.analyze_image(image_path, prompt)
            elapsed = time.time() - start_time
            
            return {
                "success": True,
                "response": response,
                "model_used": self.primary_model_name,
                "fallback_used": False,
                "processing_time": elapsed
            }
        
        except Exception as primary_error:
            print(f"\n⚠️ Primary model ({self.primary_model_name}) failed: {primary_error}\n")
            
            # Try fallback if available
            if self.fallback:
                try:
                    print(f"🔄 Trying fallback model ({self.fallback_model_name})...\n")
                    response = self.fallback.analyze_image(image_path, prompt)
                    elapsed = time.time() - start_time
                    
                    return {
                        "success": True,
                        "response": response,
                        "model_used": self.fallback_model_name,
                        "fallback_used": True,
                        "primary_error": str(primary_error),
                        "processing_time": elapsed
                    }
                
                except Exception as fallback_error:
                    elapsed = time.time() - start_time
                    return {
                        "success": False,
                        "error": f"Both models failed.\nPrimary: {primary_error}\nFallback: {fallback_error}",
                        "fallback_used": True,
                        "processing_time": elapsed
                    }
            else:
                elapsed = time.time() - start_time
                return {
                    "success": False,
                    "error": str(primary_error),
                    "fallback_used": False,
                    "processing_time": elapsed
                }


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON from VLM response (handles markdown)"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try extracting from markdown code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
            return json.loads(json_str)
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
            return json.loads(json_str)
        else:
            # Try finding JSON object
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
