# AI Endpoints

These endpoints provide access to AI-related functionality and debugging features.

## GET /ai/models (debug only)

Get available AI models and their configurations.

**Response:**
```json
{
    "available_models": {
        "openai": {
            "name": "openai",
            "endpoint": "https://api.openai.com/v1",
            "generation_model": "gpt-4",
            "embedding_model": "text-embedding-3-small",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60
        },
        "ollama": {
            "name": "ollama",
            "endpoint": "http://localhost:11434",
            "generation_model": "llama2",
            "embedding_model": "nomic-embed-text",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60
        },
        "google": {
            "name": "google",
            "endpoint": "https://generativelanguage.googleapis.com",
            "generation_model": "gemini-2.0-flash-lite",
            "embedding_model": "embedding-001",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60
        }
    }
}
```

## POST /ai/test (debug only)

Test AI model with a simple prompt.

**Request Body:**
```json
{
    "model_id": "openai",
    "prompt": "Generate a 5-song playlist for a rainy day"
}
```

**Response:**
```json
{
    "success": true,
    "model_used": {
        "name": "openai",
        "endpoint": "https://api.openai.com/v1",
        "generation_model": "gpt-4.1-nano",
        "embedding_model": "text-embedding-3-small",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60
    },
    "response": "Here's a perfect rainy day playlist:\n1. The Sound of Silence - Simon & Garfunkel\n2. Mad World - Gary Jules\n3. Black - Pearl Jam\n4. The Night We Met - Lord Huron\n5. Skinny Love - Bon Iver"
}
```

## Error Responses

- `400 Bad Request`: Invalid request body or missing required fields
- `403 Forbidden`: Endpoint requires debug mode
- `500 Internal Server Error`: AI test failed, model unavailable, or provider error

**Error Format:**
```json
{
    "detail": "string"
}
```

**Debug Mode Restriction:**
```json
{
    "detail": "This endpoint is only available in debug mode"
}
```

**AI Service Errors:**
```json
{
    "detail": "AI test failed: Connection timeout"
}
```

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
