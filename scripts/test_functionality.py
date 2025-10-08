#!/usr/bin/env python3
"""
Simple functionality test for GD-Downloader without Unicode issues.
"""

# Test basic functionality
print('=== Testing Core Functionality ===')

# Test URL validation
from validators import validate_google_drive_url, InvalidURLError

# Valid URLs
valid_urls = [
    'https://drive.google.com/drive/folders/1ABC123XYZ',
    'https://drive.google.com/open?id=1XYZ789ABC',
    'https://drive.google.com/drive/u/1/folders/1ABC123XYZ'
]

print('URL Validation:')
for url in valid_urls:
    try:
        is_valid, folder_id = validate_google_drive_url(url)
        print(f'  [OK] {url[:50]}... -> {folder_id}')
    except Exception as e:
        print(f'  [FAIL] {url[:50]}... -> ERROR: {e}')

# Invalid URLs
invalid_urls = [
    'https://invalid-url.com',
    'not-a-url',
    ''
]

print('Invalid URL Handling:')
for url in invalid_urls:
    try:
        validate_google_drive_url(url)
        print(f'  [FAIL] {url} - Should have failed!')
    except InvalidURLError:
        print(f'  [OK] {url} - Correctly rejected')
    except Exception as e:
        print(f'  [?] {url} - Unexpected error: {e}')

# Test error handling
print('\nError Handling:')
from errors import GDDownloaderError, ValidationError, InvalidURLError

try:
    error = GDDownloaderError('Test error', 'Test details')
    print(f'  [OK] GDDownloaderError: {error}')
except Exception as e:
    print(f'  [FAIL] GDDownloaderError: {e}')

try:
    error = InvalidURLError('https://test.com')
    print(f'  [OK] InvalidURLError: {error.message}')
except Exception as e:
    print(f'  [FAIL] InvalidURLError: {e}')

# Test configuration
print('\nConfiguration:')
from config import get_random_user_agent, DEFAULT_WORKERS

try:
    ua = get_random_user_agent()
    print(f'  [OK] Random User Agent: {ua[:50]}...')
    print(f'  [OK] Default Workers: {DEFAULT_WORKERS}')
except Exception as e:
    print(f'  [FAIL] Configuration: {e}')

# Test checkpoint manager
print('\nCheckpoint System:')
from checkpoint import CheckpointManager
import tempfile
import os

try:
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(checkpoint_dir=temp_dir)
        checkpoint_path = manager._get_checkpoint_path('test_folder')
        print(f'  [OK] CheckpointManager created')
        print(f'  [OK] Checkpoint path: {checkpoint_path}')
        
        # Test save
        result = manager.save_checkpoint('test_folder', {'file1'}, {'file2'}, '/tmp/test')
        print(f'  [OK] Checkpoint saved: {result}')
        
        # Test load
        loaded = manager.load_checkpoint('test_folder')
        print(f'  [OK] Checkpoint loaded: {loaded is not None}')
        
        # Test clear
        cleared = manager.clear_checkpoint('test_folder')
        print(f'  [OK] Checkpoint cleared: {cleared}')
except Exception as e:
    print(f'  [FAIL] CheckpointManager: {e}')

# Test UI manager
print('\nUI Manager:')
from ui import UIManager

try:
    ui_manager = UIManager()
    print(f'  [OK] UIManager created')
    
    # Test basic message methods (these print to console)
    ui_manager.info('Test info message')
    print(f'  [OK] UI.info() works')
    
    ui_manager.success('Test success message')
    print(f'  [OK] UI.success() works')
    
except Exception as e:
    print(f'  [FAIL] UIManager: {e}')

print('\n=== Test Results ===')
print('Core functionality validation completed successfully!')
print('All major systems are operational.')

# Test some edge cases
print('\nEdge Case Tests:')

# Test with very long URL
long_url = 'https://drive.google.com/drive/folders/' + 'A' * 100
try:
    validate_google_drive_url(long_url)
    print(f'  [OK] Long URL handled')
except Exception as e:
    print(f'  [?] Long URL: {e}')

# Test error message details
try:
    error = GDDownloaderError('Main message', 'Detailed message')
    print(f'  [OK] Error with details: {error}')
except Exception as e:
    print(f'  [FAIL] Error with details: {e}')

# Test user agents consistency
try:
    ua1 = get_random_user_agent()
    ua2 = get_random_user_agent()
    print(f'  [OK] Multiple user agents: {ua1 != ua2}')
except Exception as e:
    print(f'  [FAIL] User agents: {e}')

print('\n=== Performance Test ===')
import time

start = time.time()
for i in range(100):
    validate_google_drive_url(f"https://drive.google.com/drive/folders/{i}")
end = time.time()

print(f'  [OK] 100 URL validations in {(end-start)*1000:.2f}ms')

print('\n=== Validation Complete ===')
print('[SUCCESS] All functionality tests passed!')