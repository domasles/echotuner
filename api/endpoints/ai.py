"""AI-related endpoint implementations"""

import logging

from fastapi import HTTPException, APIRouter

from config.security import security_config

from services.ai.ai import ai_service

from core.auth.decorators import debug_only
from core.validation.validators import UniversalValidator, validate_request

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/models")
async def get_ai_models():
    """Get available AI models and their configurations"""

    models = {}

    for model_id in ai_service.list_available_providers():
        try:
            model_info = ai_service.get_provider_info(model_id)
            models[model_id] = model_info

        except Exception as e:
            models[model_id] = {"error": str(e)}

    return {
        "available_models": models,
    }

@router.post("/test")
@debug_only
async def test_ai_model(request):
    """Test AI model with a simple prompt"""

    try:
        data = await request.json()
        model_id = data.get("model_id")
        prompt = data.get("prompt", "Hello, this is a test.")
        response = await ai_service.generate_text(prompt, model_id=model_id)

        return {
            "success": True,
            "model_used": ai_service.get_provider_info(model_id),
            "response": response
        }

    except Exception as e:
        sanitized_error = UniversalValidator.sanitize_error_message(str(e))
        raise HTTPException(status_code=500, detail=f"AI test failed: {sanitized_error}")

@debug_only
async def production_readiness_check():
    """Check if the API is ready for production deployment"""

    issues = security_config.validate_production_readiness()

    return {
        "production_ready": len(issues) == 0,
        "issues": issues,
        "recommendations": [
            "Set DEBUG=false in production",
            "Enable AUTH_REQUIRED=true",
            "Enable SECURE_HEADERS=true",
            "Configure rate limiting",
            "Use HTTPS in production",
            "Set up proper logging",
            "Configure monitoring"
        ]
    }
