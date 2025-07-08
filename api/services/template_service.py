"""
Template service.
This service is responsible for loading and rendering HTML templates.
"""

import secrets

from pathlib import Path

from core.singleton import SingletonServiceBase

class TemplateService(SingletonServiceBase):
    """Service for loading and rendering HTML templates"""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize the TemplateService."""

        self.templates_dir = Path(__file__).parent.parent / "templates"
        self._cache = {}

    def generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce for CSP"""

        return secrets.token_urlsafe(16)

    def load_template(self, template_name: str) -> str:
        """Load a template from file, with caching"""

        if template_name not in self._cache:
            template_path = self.templates_dir / template_name

            if not template_path.exists():
                raise FileNotFoundError(f"Template {template_name} not found")

            with open(template_path, 'r', encoding='utf-8') as f:
                self._cache[template_name] = f.read()

        return self._cache[template_name]

    def render_template(self, template_name: str, **kwargs) -> str:
        """Render a template with the given variables"""

        template_content = self.load_template(template_name)

        if 'nonce' not in kwargs:
            kwargs['nonce'] = self.generate_nonce()

        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))

        return template_content

    def clear_cache(self):
        """Clear the template cache (useful for development)"""

        self._cache.clear()

template_service = TemplateService()
