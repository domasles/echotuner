"""
Spotify OAuth Provider.
Handles Spotify OAuth2 authentication flow.
"""

import base64
import httpx
from urllib.parse import urlencode
from typing import Dict, Any

from .base_oauth import BaseOAuthProvider

class SpotifyOAuthProvider(BaseOAuthProvider):
    """Spotify OAuth2 provider implementation."""
    
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    USER_INFO_URL = "https://api.spotify.com/v1/me"
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate Spotify OAuth authorization URL."""
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'playlist-modify-public playlist-modify-private user-read-private user-read-email'
        }
        
        if state:
            params['state'] = state
            
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    async def handle_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle Spotify OAuth callback and return user data."""
        
        # Exchange code for tokens
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            # Get tokens
            token_response = await client.post(self.TOKEN_URL, headers=headers, data=data)
            
            if token_response.status_code != 200:
                raise Exception(f"Token exchange failed: {token_response.text}")
            
            token_data = token_response.json()
            
            # Get user info
            user_headers = {'Authorization': f"Bearer {token_data['access_token']}"}
            user_response = await client.get(self.USER_INFO_URL, headers=user_headers)
            
            if user_response.status_code != 200:
                raise Exception(f"User info request failed: {user_response.text}")
            
            user_data = user_response.json()
            
            return {
                'provider': 'spotify',
                'provider_user_id': user_data['id'],
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in'),
                'user_info': user_data
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Spotify access token."""
        
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, headers=headers, data=data)
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            return response.json()
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "spotify"
