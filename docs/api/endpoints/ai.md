# AI Endpoints

These endpoints provide access to AI-related functionality and debugging features.

## GET /ai/models

**[DEBUG ONLY]** Get available AI models and their configurations.

**Response:**
```json
{
  "providers": [
    {
      "name": "openai",
      "display_name": "OpenAI",
      "models": [
        {
          "id": "gpt-4",
          "name": "GPT-4",
          "max_tokens": 8192,
          "supports_embeddings": true
        },
        {
          "id": "gpt-3.5-turbo",
          "name": "GPT-3.5 Turbo", 
          "max_tokens": 4096,
          "supports_embeddings": true
        }
      ],
      "status": "available",
      "configuration": {
        "api_key_configured": true,
        "base_url": "https://api.openai.com/v1"
      }
    },
    {
      "name": "ollama",
      "display_name": "Ollama",
      "models": [
        {
          "id": "llama2",
          "name": "Llama 2",
          "max_tokens": 4096,
          "supports_embeddings": true
        }
      ],
      "status": "available",
      "configuration": {
        "base_url": "http://localhost:11434"
      }
    }
  ],
  "current_provider": "openai",
  "total_providers": 3
}
```

## POST /ai/test

**[DEBUG ONLY]** Test AI model with a simple prompt.

**Request Body:**
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "prompt": "Generate a 5-song playlist for a rainy day",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "success": true,
  "provider": "openai",
  "model": "gpt-4",
  "response": {
    "content": "Here's a perfect rainy day playlist:\n1. The Sound of Silence - Simon & Garfunkel\n2. Mad World - Gary Jules\n3. Black - Pearl Jam\n4. The Night We Met - Lord Huron\n5. Skinny Love - Bon Iver",
    "usage": {
      "prompt_tokens": 15,
      "completion_tokens": 85,
      "total_tokens": 100
    }
  },
  "response_time": 1.2
}
```

## Provider Information

The AI system supports multiple providers:

### OpenAI
- **Models**: GPT-4, GPT-3.5 Turbo
- **Features**: Chat completion, embeddings
- **Configuration**: Requires `CLOUD_API_KEY`

### Google
- **Models**: Gemini Pro
- **Features**: Chat completion, embeddings
- **Configuration**: Requires `CLOUD_API_KEY`

### Ollama
- **Models**: Local models (Llama 2, Mistral, etc.)
- **Features**: Chat completion, embeddings
- **Configuration**: Requires local Ollama installation

## Error Responses

- `400 Bad Request`: Invalid provider, model, or prompt
- `401 Unauthorized`: API key missing or invalid
- `403 Forbidden`: Endpoint requires debug mode
- `429 Too Many Requests`: API rate limit exceeded
- `500 Internal Server Error`: AI provider error
- `503 Service Unavailable`: AI provider temporarily unavailable

**Error Format:**
```json
{
  "detail": "string",
  "error": "string",
  "provider": "string"
}
```

## Notes

- AI endpoints are primarily for debugging and testing
- The `/ai/models` endpoint shows which providers are properly configured
- The `/ai/test` endpoint allows testing different models with custom prompts
- All AI endpoints require debug mode to be enabled
- Provider availability depends on proper configuration of API keys and endpoints
