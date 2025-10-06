"""
Configuration module for Nexero VR Real Estate Analytics Platform.

This module manages environment variables and application settings using Pydantic.
Settings are loaded from .env file and can be overridden by environment variables.

Environment Variables:
- SUPABASE_URL: Supabase project URL
- SUPABASE_KEY: Supabase service role key (keep secret!)
- ENVIRONMENT: Application environment (development/staging/production)
- LOG_LEVEL: Logging level (debug/info/warning/error)
- CORS_ORIGINS: List of allowed CORS origins (comma-separated)
- API_VERSION: API version string

Usage:
    from app.config import get_settings
    
    settings = get_settings()
    print(settings.SUPABASE_URL)
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses Pydantic BaseSettings to automatically load and validate
    configuration from .env file and environment variables.
    """
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Service role key for backend operations
    
    # Application Configuration
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: List[str] = ["*"]
    API_VERSION: str = "v1"
    
    class Config:
        """Pydantic configuration for Settings class."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached Settings instance (singleton pattern).
    
    Uses lru_cache to ensure only one Settings instance is created
    during the application lifetime. This improves performance and
    ensures consistent configuration across the application.
    
    Returns:
        Settings: Singleton Settings instance
        
    Example:
        settings = get_settings()
        supabase_url = settings.SUPABASE_URL
    """
    return Settings()
