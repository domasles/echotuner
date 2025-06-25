from pathlib import Path

class TemplateService:
    """Service for loading and rendering HTML templates"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self._cache = {}
    
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

        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        
        return template_content
    
    def clear_cache(self):
        """Clear the template cache (useful for development)"""

        self._cache.clear()

template_service = TemplateService()
