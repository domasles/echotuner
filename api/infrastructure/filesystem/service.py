"""
Filesystem utility service.
Manages filesystem validation and directory creation for the EchoTuner API.
"""

import logging
import os
from typing import List, Dict, Any
from pathlib import Path

from infrastructure.singleton import SingletonServiceBase
from domain.config.app_constants import AppConstants

logger = logging.getLogger(__name__)


class FilesystemService(SingletonServiceBase):
    """Service for managing filesystem operations and validating required directories"""

    def __init__(self):
        super().__init__()

    async def _setup_service(self):
        """Initialize the filesystem service."""

        self.required_directories = AppConstants.REQUIRED_DIRECTORIES

        try:
            await self._ensure_required_directories()
            logger.info("Filesystem validation completed successfully")

        except Exception as e:
            logger.error(f"Failed to initialize filesystem service: {e}")
            raise

    async def _ensure_required_directories(self):
        """Ensure all required directories exist, create them if they don't."""

        for directory in self.required_directories:
            try:
                directory_path = Path(directory)

                if not directory_path.exists():
                    directory_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created required directory: {directory}")
                else:
                    logger.debug(f"Required directory already exists: {directory}")

            except Exception as e:
                logger.error(f"Failed to create directory '{directory}': {e}")
                raise

    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure a specific directory exists, create it if it doesn't.

        Args:
            directory_path: Path to the directory to ensure exists

        Returns:
            bool: True if directory exists or was created successfully
        """

        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)
            return True

        except Exception as e:
            logger.error(f"Failed to ensure directory exists '{directory_path}': {e}")
            return False

    def directory_exists(self, directory_path: str) -> bool:
        """
        Check if a directory exists.

        Args:
            directory_path: Path to check

        Returns:
            bool: True if directory exists
        """

        return Path(directory_path).exists()

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file exists
        """

        return Path(file_path).is_file()

    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            file_path: Path to the file

        Returns:
            int: File size in bytes, 0 if file doesn't exist
        """

        try:
            path = Path(file_path)
            return path.stat().st_size if path.exists() else 0

        except Exception as e:
            logger.error(f"Failed to get file size for '{file_path}': {e}")
            return 0

    async def get_status(self) -> Dict[str, Any]:
        """Get filesystem service status and information."""

        directory_status = {}

        for directory in self.required_directories:
            path = Path(directory)
            directory_status[directory] = {
                "exists": path.exists(),
                "is_directory": path.is_dir() if path.exists() else False,
                "absolute_path": str(path.absolute()),
            }

        return {
            "service_name": "filesystem_service",
            "status": "active",
            "required_directories": self.required_directories,
            "directory_status": directory_status,
        }


# Create singleton instance
filesystem_service = FilesystemService()
