"""
Google OAuth Provider.
Handles Google OAuth2 authentication flow.
"""

import httpx
from urllib.parse import urlencode
from typing import Dict, Any

from .base import BaseOAuthProvider

class GoogleOAuthProvider(BaseOAuthProvider):
    """Google OAuth2 provider implementation."""
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL."""
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        if state:
            params['state'] = state
            
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    async def handle_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        """Handle Google OAuth callback and return user data."""
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            # Get tokens
            token_response = await client.post(self.TOKEN_URL, data=data)
            
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
                'provider': 'google',
                'provider_user_id': user_data['id'],
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in'),
                'user_info': user_data
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google access token."""
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data)
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            return response.json()
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "google"
