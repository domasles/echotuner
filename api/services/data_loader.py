import asyncio
import logging
import json
import os

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from functools import lru_cache

try:
    import ujson as json_lib

except ImportError:
    import json as json_lib

logger = logging.getLogger(__name__)

class DataLoader:
    """Utility class to load and manage JSON configuration data with performance optimizations"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self._cache = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    @lru_cache(maxsize=32)
    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file with caching and performance optimizations"""
        
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(file_path):
                logger.error(f"Configuration file not found: {file_path}")
                raise FileNotFoundError(f"Configuration file not found: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json_lib.load(file)
                logger.info(f"Loaded configuration from {filename}")

                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            raise ValueError(f"Invalid JSON in {filename}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise RuntimeError(f"Failed to load {filename}: {e}")
    
    async def _load_json_file_async(self, filename: str) -> Dict[str, Any]:
        """Asynchronously load a JSON file"""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._load_json_file, filename)
    
    def get_prompt_references(self) -> List[str]:
        """Get music reference texts for embedding validation"""
        
        data = self._load_json_file('prompt_references.json')
        return data.get('music_references', [])
    def get_mood_patterns(self) -> Dict[str, List[str]]:
        """Get mood keyword patterns for AI parsing"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('mood_patterns', {})
    
    def get_genre_patterns(self) -> Dict[str, List[str]]:
        """Get genre keyword patterns for AI parsing"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('genre_patterns', {})
    
    def get_genre_artists(self) -> Dict[str, List[str]]:
        """Get artists associated with each genre"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('genre_artists', {})
    
    def get_broader_keywords(self) -> List[str]:
        """Get broader search keywords for additional song searches"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('broader_keywords', ['popular', 'trending'])
    
    def get_energy_terms(self) -> Dict[str, Dict[str, List[str]]]:
        """Get energy level terms and search keywords"""
        
        data = self._load_json_file('energy_terms.json')
        return data.get('energy_terms', {})
    
    def get_energy_trigger_words(self) -> Dict[str, List[str]]:
        """Get words that trigger specific energy levels"""
        
        data = self._load_json_file('energy_terms.json')
        return data.get('energy_trigger_words', {})
    
    def get_activity_patterns(self) -> Dict[str, List[str]]:
        """Get activity-related keyword patterns"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('activity_patterns', {})
    
    def get_emotion_intensities(self) -> Dict[str, List[str]]:
        """Get emotion intensity modifiers"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('emotion_intensities', {})
    
    def get_time_contexts(self) -> Dict[str, List[str]]:
        """Get time-related context patterns"""
        
        data = self._load_json_file('ai_patterns.json')
        return data.get('time_contexts', {})
    
    def get_activity_energy_mapping(self) -> Dict[str, str]:
        """Get mapping of activities to energy levels"""
        
        data = self._load_json_file('energy_terms.json')
        return data.get('activity_energy_mapping', {})
    
    def get_tempo_ranges(self) -> Dict[str, Dict[str, str]]:
        """Get BPM ranges for different energy levels"""
        
        data = self._load_json_file('energy_terms.json')
        return data.get('tempo_ranges', {})
    
    def get_mood_energy_correlations(self) -> Dict[str, str]:
        """Get correlations between moods and energy levels"""
        
        data = self._load_json_file('energy_terms.json')
        return data.get('mood_energy_correlations', {})
    
    def reload_cache(self):
        """Clear cache to force reload of all configuration files"""

        self._load_json_file.cache_clear()
        logger.info("Configuration cache cleared - files will be reloaded on next access")
    
    def __del__(self):
        """Cleanup executor on destruction"""

        try:
            self._executor.shutdown(wait=False)

        except:
            pass

data_loader = DataLoader()
