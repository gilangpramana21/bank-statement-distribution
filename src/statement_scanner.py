"""
Statement Scanner component for discovering bank statements in Google Drive.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import config
from src.database import db
from src.models import StatementFile, ProcessingStatus
from src.logger import get_logger
import io
from googleapiclient.http import MediaIoBaseDownload

logger = get_logger(__name__)


class StatementScanner:
    """Discovers and monitors bank statement files in Google Drive."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.csv', '.xls', '.xlsx'}
    
    def __init__(self):
        """Initialize Statement Scanner."""
        self.service = None
        self.rate_limiter = RateLimiter(
            max_requests_per_second=config.gdrive_rate_limit,
            threshold=config.rate_limit_threshold
        )
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Google Drive API."""
        try:
            credentials_file = config.google_drive_credentials_file
            
            if not Path(credentials_file).exists():
                raise FileNotFoundError(f"Google Drive credentials file not found: {credentials_file}")
            
            # Use service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("google_drive_authenticated")
            
        except Exception as e:
            logger.error("google_drive_authentication_failed", error=str(e))
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((HttpError, ConnectionError)),
        reraise=True
    )
    def _list_files_in_folder(self, folder_id: str, depth: int = 0) -> List[Dict]:
        """
        List files in a Google Drive folder recursively.
        
        Args:
            folder_id: Google Drive folder ID
            depth: Current recursion depth
            
        Returns:
            List of file metadata dictionaries
        """
        if depth > config.max_depth:
            logger.warning("max_depth_reached", folder_id=folder_id, depth=depth)
            return []
        
        files = []
        page_token = None
        
        try:
            while True:
                # Rate limiting
                self.rate_limiter.wait_if_needed()
                
                # Query files in folder
                query = f"'{folder_id}' in parents and trashed=false"
                response = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)',
                    pageToken=page_token
                ).execute()
                
                items = response.get('files', [])
                
                for item in items:
                    mime_type = item.get('mimeType', '')
                    
                    # If it's a folder, recurse
                    if mime_type == 'application/vnd.google-apps.folder':
                        subfolder_files = self._list_files_in_folder(item['id'], depth + 1)
                        files.extend(subfolder_files)
                    else:
                        # Check if it's a supported file type
                        file_name = item.get('name', '')
                        file_ext = Path(file_name).suffix.lower()
                        
                        if file_ext in self.SUPPORTED_EXTENSIONS:
                            files.append(item)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return files
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("google_drive_permission_error", 
                           folder_id=folder_id, 
                           error=str(e))
                return []
            raise
    
    def _get_folder_id_by_name(self, folder_name: str) -> Optional[str]:
        """
        Get folder ID by folder name.
        
        Args:
            folder_name: Name of the folder
            
        Returns:
            Folder ID or None if not found
        """
        try:
            self.rate_limiter.wait_if_needed()
            
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = response.get('files', [])
            if files:
                return files[0]['id']
            
            return None
            
        except Exception as e:
            logger.error("folder_lookup_failed", folder_name=folder_name, error=str(e))
            return None
    
    def _extract_metadata(self, file_item: Dict, bank_group: str) -> Optional[Dict]:
        """
        Extract metadata from Google Drive file item.
        
        Args:
            file_item: Google Drive file metadata
            bank_group: Bank group name
            
        Returns:
            Extracted metadata dictionary or None if extraction fails
        """
        try:
            file_path = self._get_file_path(file_item['id'])
            path_parts = file_path.split('/')
            
            # Extract bank name and entity name from path
            # Expected structure: BankGroup/Bank/Entity/File
            if len(path_parts) >= 3:
                bank_name = path_parts[-3]  # Parent folder at level 1
                entity_name = path_parts[-2]  # Parent folder at level 2
            else:
                logger.warning("invalid_path_structure", file_path=file_path)
                return None
            
            # Parse modified time
            modified_time_str = file_item.get('modifiedTime', '')
            modified_time = datetime.fromisoformat(modified_time_str.replace('Z', '+00:00'))
            
            metadata = {
                'file_path': file_path,
                'bank_name': bank_name,
                'entity_name': entity_name,
                'file_size': int(file_item.get('size', 0)),
                'last_modified': modified_time,
                'file_id': file_item['id']
            }
            
            return metadata
            
        except Exception as e:
            logger.error("metadata_extraction_failed", 
                        file_id=file_item.get('id'), 
                        error=str(e))
            return None
    
    def _get_file_path(self, file_id: str) -> str:
        """
        Get full file path in Google Drive.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Full file path
        """
        try:
            self.rate_limiter.wait_if_needed()
            
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, parents'
            ).execute()
            
            path_parts = [file_metadata['name']]
            parents = file_metadata.get('parents', [])
            
            # Traverse up to root
            while parents:
                parent_id = parents[0]
                self.rate_limiter.wait_if_needed()
                
                parent_metadata = self.service.files().get(
                    fileId=parent_id,
                    fields='name, parents'
                ).execute()
                
                path_parts.insert(0, parent_metadata['name'])
                parents = parent_metadata.get('parents', [])
            
            return '/'.join(path_parts)
            
        except Exception as e:
            logger.error("file_path_retrieval_failed", file_id=file_id, error=str(e))
            return f"unknown/{file_id}"
    
    def _calculate_checksum(self, file_id: str) -> str:
        """
        Calculate SHA-256 checksum for a file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            SHA-256 checksum (hex string)
        """
        try:
            self.rate_limiter.wait_if_needed()
            
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            checksum = hashlib.sha256(file_content.read()).hexdigest()
            
            return checksum
            
        except Exception as e:
            logger.error("checksum_calculation_failed", file_id=file_id, error=str(e))
            # Return a placeholder checksum if calculation fails
            return hashlib.sha256(file_id.encode()).hexdigest()
    
    def discover_statements(self) -> List[StatementFile]:
        """
        Discover new bank statements in Google Drive.
        
        Returns:
            List of discovered StatementFile objects
        """
        discovered_files = []
        
        try:
            for bank_group in config.bank_groups:
                logger.info("scanning_bank_group", bank_group=bank_group)
                
                # Get folder ID
                folder_id = self._get_folder_id_by_name(bank_group)
                if not folder_id:
                    logger.error("bank_group_folder_not_found", bank_group=bank_group)
                    continue
                
                # List files in folder
                try:
                    files = self._list_files_in_folder(folder_id)
                    logger.info("files_discovered", 
                              bank_group=bank_group, 
                              count=len(files))
                    
                    # Process each file
                    for file_item in files:
                        metadata = self._extract_metadata(file_item, bank_group)
                        if not metadata:
                            continue
                        
                        # Check if file already processed
                        with db.get_session() as session:
                            existing = session.query(StatementFile).filter_by(
                                file_path=metadata['file_path']
                            ).first()
                            
                            if existing and existing.status == ProcessingStatus.DELIVERED:
                                logger.debug("file_already_processed", 
                                           file_path=metadata['file_path'])
                                continue
                        
                        # Calculate checksum
                        checksum = self._calculate_checksum(metadata['file_id'])
                        
                        # Create StatementFile object
                        statement_file = StatementFile(
                            file_path=metadata['file_path'],
                            bank_name=metadata['bank_name'],
                            entity_name=metadata['entity_name'],
                            file_size=metadata['file_size'],
                            last_modified=metadata['last_modified'],
                            checksum=checksum,
                            status=ProcessingStatus.UNPROCESSED
                        )
                        
                        # Save to database
                        with db.get_session() as session:
                            # Check for duplicates by file path
                            existing = session.query(StatementFile).filter_by(
                                file_path=statement_file.file_path
                            ).first()
                            
                            if existing:
                                # Update if modified time is newer
                                if statement_file.last_modified > existing.last_modified:
                                    existing.last_modified = statement_file.last_modified
                                    existing.checksum = checksum
                                    existing.file_size = statement_file.file_size
                                    logger.info("file_metadata_updated", 
                                              file_path=statement_file.file_path)
                            else:
                                session.add(statement_file)
                                discovered_files.append(statement_file)
                                logger.info("file_discovered", 
                                          file_path=statement_file.file_path,
                                          entity=statement_file.entity_name)
                
                except Exception as e:
                    logger.error("bank_group_scan_failed", 
                               bank_group=bank_group, 
                               error=str(e))
                    continue
            
            logger.info("discovery_complete", total_discovered=len(discovered_files))
            return discovered_files
            
        except Exception as e:
            logger.error("discovery_failed", error=str(e))
            raise


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_requests_per_second: int, threshold: float = 0.8):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_second: Maximum requests per second
            threshold: Threshold (0.0 to 1.0) at which to start pausing
        """
        self.max_requests = max_requests_per_second
        self.threshold = threshold
        self.request_count = 0
        self.window_start = datetime.now()
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit threshold is reached."""
        import time
        
        now = datetime.now()
        elapsed = (now - self.window_start).total_seconds()
        
        # Reset counter if window has passed
        if elapsed >= 1.0:
            self.request_count = 0
            self.window_start = now
        
        # Check if threshold reached
        if self.request_count >= (self.max_requests * self.threshold):
            sleep_time = 1.0 - elapsed
            if sleep_time > 0:
                logger.debug("rate_limit_pause", sleep_time=sleep_time)
                time.sleep(sleep_time)
                self.request_count = 0
                self.window_start = datetime.now()
        
        self.request_count += 1
