"""
Session manager for tenant-isolated Playwright sessions
"""
from pathlib import Path
import json
import os
from typing import Optional

from ..core.config import settings


class TenantSessionManager:
    """Manages isolated browser sessions per tenant"""
    
    def __init__(self, base_path: str = None):
        """
        Initialize session manager.
        
        Args:
            base_path: Base directory for sessions. Defaults to settings.SESSIONS_BASE_PATH
        """
        self.base_path = Path(base_path or settings.SESSIONS_BASE_PATH)
        # Create base path if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_session_dir(self, tenant_id: str) -> Path:
        """
        Get or create isolated session directory for tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Path to tenant's session directory
        """
        tenant_dir = self.base_path / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir
    
    def get_storage_state_path(self, tenant_id: str) -> Path:
        """
        Get path to Playwright storage_state.json file.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Path to storage state file
        """
        return self.get_session_dir(tenant_id) / "storage_state.json"
    
    def get_user_data_dir(self, tenant_id: str) -> Path:
        """
        Get path to browser user data directory (for persistent profiles).
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Path to user data directory
        """
        user_data = self.get_session_dir(tenant_id) / "user_data"
        user_data.mkdir(exist_ok=True)
        return user_data
    
    def session_exists(self, tenant_id: str) -> bool:
        """
        Check if a saved session exists for tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            True if storage_state.json exists
        """
        return self.get_storage_state_path(tenant_id).exists()
    
    def get_session_info(self, tenant_id: str) -> Optional[dict]:
        """
        Get session metadata if exists.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Session info dict or None
        """
        info_path = self.get_session_dir(tenant_id) / "session_info.json"
        if info_path.exists():
            with open(info_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_session_info(self, tenant_id: str, info: dict):
        """
        Save session metadata.
        
        Args:
            tenant_id: Unique tenant identifier
            info: Session metadata to save
        """
        info_path = self.get_session_dir(tenant_id) / "session_info.json"
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2, default=str)
    
    def clear_session(self, tenant_id: str):
        """
        Clear all session data for tenant.
        
        Args:
            tenant_id: Unique tenant identifier
        """
        import shutil
        session_dir = self.get_session_dir(tenant_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
            session_dir.mkdir(parents=True, exist_ok=True)
    
    def get_screenshots_dir(self, tenant_id: str) -> Path:
        """
        Get path to screenshots directory for debugging.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            Path to screenshots directory
        """
        screenshots = self.get_session_dir(tenant_id) / "screenshots"
        screenshots.mkdir(exist_ok=True)
        return screenshots
    
    def list_all_sessions(self) -> list[str]:
        """
        List all tenant IDs with active sessions.
        
        Returns:
            List of tenant IDs
        """
        if not self.base_path.exists():
            return []
        
        return [
            d.name for d in self.base_path.iterdir()
            if d.is_dir() and (d / "storage_state.json").exists()
        ]
