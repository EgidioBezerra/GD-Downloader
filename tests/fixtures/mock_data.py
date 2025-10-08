"""
Mock data factories and utilities for testing GD-Downloader.

This module provides factory functions and pre-defined mock data
for creating realistic test scenarios.
"""

import json
from typing import Any, Dict, List
from datetime import datetime


class MockDataFactory:
    """Factory for creating mock data for tests."""

    # File types and their corresponding MIME types
    FILE_TYPES = {
        'pdf': 'application/pdf',
        'doc': 'application/vnd.google-apps.document',
        'sheet': 'application/vnd.google-apps.spreadsheet',
        'slide': 'application/vnd.google-apps.presentation',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'txt': 'text/plain',
        'zip': 'application/zip',
    }

    @staticmethod
    def create_file_data(
        file_id: str,
        name: str,
        file_type: str = 'pdf',
        size: int = 1024,
        can_download: bool = True,
        folder_id: str = None
    ) -> Dict[str, Any]:
        """Create mock file data."""
        mime_type = MockDataFactory.FILE_TYPES.get(file_type, 'application/octet-stream')
        
        file_data = {
            'id': file_id,
            'name': name,
            'mimeType': mime_type,
            'size': str(size),
            'createdTime': datetime.now().isoformat() + 'Z',
            'modifiedTime': datetime.now().isoformat() + 'Z',
            'webViewLink': f'https://drive.google.com/file/d/{file_id}/view',
            'webContentLink': f'https://drive.google.com/file/d/{file_id}/export',
            'capabilities': {
                'canDownload': can_download,
                'canCopy': True,
                'canEdit': False,
                'canComment': False,
                'canAddChildren': False,
                'canDelete': False,
                'canDownload': can_download,
                'canEditContent': False,
            }
        }
        
        if folder_id:
            file_data['parents'] = [folder_id]
            
        return file_data

    @staticmethod
    def create_folder_data(
        folder_id: str,
        name: str,
        parent_id: str = None
    ) -> Dict[str, Any]:
        """Create mock folder data."""
        folder_data = {
            'id': folder_id,
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'createdTime': datetime.now().isoformat() + 'Z',
            'modifiedTime': datetime.now().isoformat() + 'Z',
            'webViewLink': f'https://drive.google.com/drive/folders/{folder_id}',
            'capabilities': {
                'canDownload': True,
                'canCopy': True,
                'canEdit': False,
                'canComment': False,
                'canAddChildren': True,
                'canDelete': False,
                'canEditContent': False,
            }
        }
        
        if parent_id:
            folder_data['parents'] = [parent_id]
            
        return folder_data

    @staticmethod
    def create_google_doc_data(file_id: str, name: str) -> Dict[str, Any]:
        """Create mock Google Doc data."""
        return MockDataFactory.create_file_data(
            file_id=file_id,
            name=name,
            file_type='doc',
            can_download=False  # Requires export
        )

    @staticmethod
    def create_video_data(
        file_id: str,
        name: str,
        file_type: str = 'mp4',
        size: int = 50 * 1024 * 1024,  # 50MB
        view_only: bool = True
    ) -> Dict[str, Any]:
        """Create mock video file data."""
        return MockDataFactory.create_file_data(
            file_id=file_id,
            name=name,
            file_type=file_type,
            size=size,
            can_download=not view_only
        )

    @staticmethod
    def create_pdf_data(
        file_id: str,
        name: str,
        size: int = 5 * 1024 * 1024,  # 5MB
        view_only: bool = False
    ) -> Dict[str, Any]:
        """Create mock PDF data."""
        return MockDataFactory.create_file_data(
            file_id=file_id,
            name=name,
            file_type='pdf',
            size=size,
            can_download=not view_only
        )

    @staticmethod
    def create_image_data(
        file_id: str,
        name: str,
        file_type: str = 'jpg',
        size: int = 2 * 1024 * 1024  # 2MB
    ) -> Dict[str, Any]:
        """Create mock image data."""
        return MockDataFactory.create_file_data(
            file_id=file_id,
            name=name,
            file_type=file_type,
            size=size
        )


class MockResponseFactory:
    """Factory for creating mock HTTP responses."""

    @staticmethod
    def create_oauth_token_response(access_token: str = "mock_access_token") -> Dict[str, Any]:
        """Create OAuth token response."""
        return {
            'access_token': access_token,
            'refresh_token': 'mock_refresh_token',
            'expires_in': 3600,
            'token_type': 'Bearer'
        }

    @staticmethod
    def create_drive_file_response(file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Drive API file response."""
        return {
            'kind': 'drive#file',
            'id': file_data['id'],
            'name': file_data['name'],
            'mimeType': file_data['mimeType'],
            'size': file_data.get('size', '0'),
            'createdTime': file_data['createdTime'],
            'modifiedTime': file_data['modifiedTime'],
            'webViewLink': file_data['webViewLink'],
            'webContentLink': file_data.get('webContentLink'),
            'parents': file_data.get('parents', []),
            'capabilities': file_data['capabilities']
        }

    @staticmethod
    def create_drive_folder_response(folder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Drive API folder response."""
        return MockResponseFactory.create_drive_file_response(folder_data)

    @staticmethod
    def create_drive_files_list_response(
        files: List[Dict[str, Any]],
        next_page_token: str = None
    ) -> Dict[str, Any]:
        """Create Drive API files list response."""
        response = {
            'kind': 'drive#fileList',
            'files': [MockResponseFactory.create_drive_file_response(f) for f in files],
            'incompleteSearch': False
        }
        
        if next_page_token:
            response['nextPageToken'] = next_page_token
            
        return response


class MockCheckpointFactory:
    """Factory for creating mock checkpoint data."""

    @staticmethod
    def create_checkpoint_data(
        folder_id: str,
        completed_files: List[str] = None,
        failed_files: List[str] = None,
        destination_path: str = "/tmp/test"
    ) -> Dict[str, Any]:
        """Create mock checkpoint data."""
        import hashlib
        
        completed = completed_files or []
        failed = failed_files or []
        
        checkpoint_data = {
            'version': '2.0',
            'folder_id': folder_id,
            'destination_path': destination_path,
            'timestamp': datetime.now().isoformat(),
            'completed_files': completed,
            'failed_files': failed,
            'total_completed': len(completed),
            'total_failed': len(failed),
        }
        
        # Add checksum
        checksum_str = json.dumps(checkpoint_data, sort_keys=True)
        checkpoint_data['checksum'] = hashlib.sha256(checksum_str.encode()).hexdigest()
        
        return checkpoint_data


# Pre-defined mock data sets
class MockDataSets:
    """Pre-defined sets of mock data for common test scenarios."""

    @staticmethod
    def get_sample_folder_contents() -> List[Dict[str, Any]]:
        """Get a sample set of files for testing folder contents."""
        factory = MockDataFactory()
        
        return [
            factory.create_file_data("file_1", "document1.pdf", "pdf", 1024*1024),
            factory.create_file_data("file_2", "video1.mp4", "mp4", 50*1024*1024, False),
            factory.create_file_data("file_3", "image1.jpg", "jpg", 2*1024*1024),
            factory.create_google_doc_data("file_4", "spreadsheet"),
            factory.create_file_data("file_5", "archive.zip", "zip", 10*1024*1024),
            factory.create_video_data("file_6", "presentation.mov", "mov", 100*1024*1024),
            factory.create_pdf_data("file_7", "report.pdf", 5*1024*1024, True),  # view-only
            factory.create_file_data("file_8", "notes.txt", "txt", 1024),
        ]

    @staticmethod
    def get_large_folder_contents(count: int = 100) -> List[Dict[str, Any]]:
        """Get a large set of files for stress testing."""
        factory = MockDataFactory()
        files = []
        
        for i in range(count):
            file_type = ['pdf', 'jpg', 'txt', 'doc', 'video'][i % 5]
            if file_type == 'video':
                files.append(factory.create_video_data(f"file_{i}", f"video_{i}.mp4"))
            elif file_type == 'doc':
                files.append(factory.create_google_doc_data(f"file_{i}", f"doc_{i}"))
            else:
                files.append(factory.create_file_data(f"file_{i}", f"file_{i}.{file_type}", file_type))
        
        return files

    @staticmethod
    def get_problematic_files() -> List[Dict[str, Any]]:
        """Get files with problematic characteristics for edge case testing."""
        factory = MockDataFactory()
        
        return [
            factory.create_file_data("file_long_name", "a" * 300 + ".pdf", "pdf"),  # Long name
            factory.create_file_data("file_unicode", "文件_测试.pdf", "pdf"),  # Unicode name
            factory.create_file_data("file_special", 'file<>:"|?*.pdf', "pdf"),  # Special chars
            factory.create_file_data("file_zero_size", "empty.txt", "txt", 0),  # Empty file
            factory.create_file_data("file_huge", "huge.mp4", "mp4", 1024**3),  # 1GB file
        ]


# Mock data constants
class MockConstants:
    """Constants used in mock data."""
    
    SAMPLE_FOLDER_ID = "test_folder_12345"
    SAMPLE_FILE_ID = "test_file_67890"
    SAMPLE_VIDEO_ID = "test_video_11111"
    SAMPLE_DOC_ID = "test_doc_22222"
    
    SAMPLE_URLS = {
        'folder': "https://drive.google.com/drive/folders/test_folder_12345",
        'file': "https://drive.google.com/file/d/test_file_67890/view",
        'video': "https://drive.google.com/file/d/test_video_11111/view",
        'doc': "https://drive.google.com/document/d/test_doc_22222/edit",
    }
    
    SAMPLE_CONTENTS = {
        'pdf': b'MOCK_PDF_CONTENT',
        'video': b'MOCK_VIDEO_CONTENT',
        'image': b'MOCK_IMAGE_CONTENT',
        'text': b'MOCK_TEXT_CONTENT',
    }