import numpy as np
import requests
import os

class PromptValidatorService:
    """
    Lightweight model to validate if user input is music/mood related.
    Uses Ollama with thenlper/gte-small for embedding-based validation.
    """
    
    def __init__(self):
        self.is_initialized = False

        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        self.model_name = os.getenv("OLLAMA_VALIDATION_MODEL")
        self.use_ollama = os.getenv("USE_OLLAMA").lower() == "true"

        self.music_reference_embeddings = None
        
    async def initialize(self):
        """Initialize the model asynchronously"""

        try:
            print("Initializing mood validation with Ollama...")
            
            if not self.use_ollama:
                print("ERROR: Ollama is required for this application")
                raise SystemExit("Ollama must be enabled. Set USE_OLLAMA=true in environment variables.")

            if not await self._check_ollama_connection():
                print("ERROR: Ollama not running or not accessible")
                raise SystemExit("Ollama is not running. Please start Ollama and try again.")
            
            await self._ensure_model_available()
            await self._compute_reference_embeddings()
            
            self.is_initialized = True
            print("Mood validation with Ollama initialized successfully!")
            
        except SystemExit:
            raise

        except Exception as e:
            print(f"ERROR: Prompt validator initialization failed: {e}")
            raise SystemExit(f"Failed to initialize prompt validator: {e}")
    
    def is_ready(self) -> bool:
        return self.is_initialized
    
    async def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""

        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        
        except:
            return False
    
    async def _ensure_model_available(self):
        """Ensure the model is available in Ollama"""

        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")

            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name not in model_names:
                    print(f"Pulling model {self.model_name}...")

                    pull_response = requests.post(
                        f"{self.ollama_base_url}/api/pull",
                        json={"name": self.model_name}
                    )

                    if pull_response.status_code == 200:
                        print(f"Model {self.model_name} pulled successfully")

                    else:
                        print(f"ERROR: Failed to pull model: {pull_response.text}")
                        raise SystemExit(f"Failed to pull model {self.model_name}")
                    
                else:
                    print(f"Model {self.model_name} already available")

        except SystemExit:
            raise

        except Exception as e:
            print(f"ERROR: Model availability check failed: {e}")
            raise SystemExit(f"Model availability check failed: {e}")
    
    async def _compute_reference_embeddings(self):
        """Pre-compute embeddings for music-related reference texts"""

        try:
            music_references = [
                "I want to listen to music",
                "I'm feeling happy and want upbeat songs",
                "I need relaxing music",
                "Play some energetic music",
                "I'm sad and want emotional songs",
                "I want to hear my favorite artist",
                "Put on some background music",
                "I need workout music",
                "Play romantic songs",
                "I want to discover new music"
            ]
            
            embeddings = []

            for text in music_references:
                embedding = await self._get_embedding(text)
                if embedding is not None:
                    embeddings.append(embedding)
            
            if embeddings:
                self.music_reference_embeddings = np.array(embeddings)
                print(f"Computed {len(embeddings)} reference embeddings")

            else:
                print("ERROR: No reference embeddings computed")
                raise SystemExit("Failed to compute reference embeddings")
                
        except SystemExit:
            raise
        
        except Exception as e:
            print(f"ERROR: Reference embeddings computation failed: {e}")
            raise SystemExit(f"Failed to compute reference embeddings: {e}")
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using Ollama"""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return np.array(result.get('embedding', []))
            
            else:
                print(f"ERROR: Failed to get embedding: {response.text}")
                raise SystemExit(f"Failed to get embedding from Ollama")
                
        except SystemExit:
            raise

        except Exception as e:
            print(f"ERROR: Embedding request failed: {e}")
            raise SystemExit(f"Embedding request failed: {e}")
    
    async def validate_prompt(self, prompt: str) -> bool:
        """
        Validate if the prompt is related to music, mood, or emotions.
        Returns True if valid, False otherwise.
        """

        if not self.is_initialized:
            await self.initialize()
        
        prompt = prompt.lower().strip()
        
        if len(prompt) < 3 or len(prompt) > 500:
            return False
        if self.music_reference_embeddings is not None:
            try:
                prompt_embedding = await self._get_embedding(prompt)

                if prompt_embedding is not None and len(prompt_embedding) > 0:
                    similarities = np.dot(self.music_reference_embeddings, prompt_embedding) / (
                        np.linalg.norm(self.music_reference_embeddings, axis=1) * 
                        np.linalg.norm(prompt_embedding)
                    )

                    max_similarity = np.max(similarities)
                    threshold = 0.6
                    is_similar = max_similarity > threshold

                    print(f"Semantic similarity: {max_similarity:.3f}, threshold: {threshold}, valid: {is_similar}")
                    return is_similar
                
                else:
                    print("ERROR: Failed to get prompt embedding")
                    raise SystemExit("Failed to get prompt embedding")
                    
            except SystemExit:
                raise

            except Exception as e:
                print(f"ERROR: Prompt validation failed: {e}")
                raise SystemExit(f"Prompt validation failed: {e}")
            
        else:
            print("ERROR: Reference embeddings not available")
            raise SystemExit("Reference embeddings not available for validation")

