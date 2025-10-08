#!/usr/bin/env python3
"""
Clean up unnecessary files and organize the project directory.
"""

import os
import shutil
from pathlib import Path
import tempfile
import sys

# Files and directories to remove
UNNECESSARY_FILES = [
    # Python cache
    '**/__pycache__/**',
    '**/*.pyc',
    '**/*.pyo',
    '**/*.pyd',
    
    # Test artifacts
    '**/.pytest_cache/**',
    '**/htmlcov/**',
    '**/.coverage',
    '**/coverage.xml',
    
    # Temporary files
    '**/*.tmp',
    '**/*.temp',
    '**/*.bak',
    '**/*.backup',
    '**/*.old',
    
    # Log files
    '**/*.log',
    '**/*.out',
    
    # OS files
    '**/.DS_Store',
    '**/Thumbs.db',
    '**/desktop.ini',
    
    # Development artifacts
    '**/.idea/**',
    '**/.vscode/settings.json',
    
    # Backup and temporary test directories
    'test_checkpoints',
    'test_downloads',
    '.claude',
    '.crush',
    'CRUSH.md',
    'temp_pdf_downloads',
    'test_artifacts',
    'test_reports',
    'htmlcov',
]

def is_safe_to_remove(path):
    """Check if a path is safe to remove."""
    path = Path(path)
    
    # Never remove:
    never_remove = [
        'README.md',
        'requirements.txt',
        'requirements_and_setup.md',
        '.gitignore',
        'pyproject.toml',
        'pytest.ini',
        'LICENSE',
        'COPYRIGHT',
        'CONTRIBUTING.md',
        'CHANGELOG.md',
    ]
    
    if path.name in never_remove:
        return False
    
    # Never remove configuration files
    if path.name.endswith(('.json', '.yml', '.yaml', '.toml', '.ini', '.cfg')):
        if path.name not in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']:
            return False
    
    # Never remove main code files
    if path.name.endswith('.py') and not path.name.startswith('test_'):
        if path.name not in ['conftest.py', 'test_basic_validation.py', 'test_functionality.py']:
            return False
    
    return True

def clean_directory(directory='.'):
    """Clean up unnecessary files in directory."""
    directory = Path(directory)
    removed_count = 0
    total_size = 0
    
    print(f"Cleaning directory: {directory.absolute()}")
    
    # Process files to remove
    for pattern in UNNECESSARY_FILES:
        for path in directory.glob(pattern):
            if path.exists() and is_safe_to_remove(path):
                try:
                    # Calculate size before removal
                    if path.is_file():
                        size = path.stat().st_size
                        total_size += size
                        path.unlink()
                        removed_count += 1
                    elif path.is_dir() and path.name in ['__pycache__', '.pytest_cache', 'htmlcov']:
                        shutil.rmtree(path)
                        removed_count += 1
                except Exception as e:
                    print(f"  [SKIP] {path}: {e}")
    
    return removed_count, total_size

def organize_files():
    """Organize project structure."""
    print("\n=== Organizing Project Structure ===")
    
    # Create directories if they don't exist
    directories = [
        'docs',
        'examples',
        'scripts',
        'tests/integration',
        'tests/e2e',
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"  [OK] Created/verified: {dir_path}")
    
    # Move documentation files to docs/
    doc_files = ['TESTING_GUIDE.md', 'TEST_IMPLEMENTATION_SUMMARY.md', 'FINAL_STATUS_REPORT.md']
    
    for doc_file in doc_files:
        src = Path(doc_file)
        dst = Path('docs') / doc_file
        
        if src.exists() and not dst.exists():
            try:
                shutil.move(str(src), str(dst))
                print(f"  [MOVED] {doc_file} -> docs/{doc_file}")
            except Exception as e:
                print(f"  [SKIP] Moving {doc_file}: {e}")
    
    # Move test scripts
    test_scripts = ['quick_test.py', 'test_functionality.py']
    
    for script in test_scripts:
        src = Path(script)
        dst = Path('scripts') / script
        
        if src.exists() and not dst.exists():
            try:
                Path('scripts').mkdir(exist_ok=True)
                shutil.move(str(src), str(dst))
                print(f"  [MOVED] {script} -> scripts/{script}")
            except Exception as e:
                print(f"  [SKIP] Moving {script}: {e}")

def check_project_structure():
    """Check if project structure is organized."""
    print("\n=== Checking Project Structure ===")
    
    expected_structure = {
        'src/': 'Source code directory',
        'tests/': 'Test directory',
        'tests/unit/': 'Unit tests',
        'tests/integration/': 'Integration tests',
        'tests/e2e/': 'End-to-end tests',
        'tests/fixtures/': 'Test fixtures',
        'tests/utils/': 'Test utilities',
        'docs/': 'Documentation',
        'scripts/': 'Test scripts',
    }
    
    all_good = True
    
    for dir_path, description in expected_structure.items():
        path = Path(dir_path)
        if path.exists():
            print(f"  [OK] {dir_path} - {description}")
        else:
            print(f"  [MISSING] {dir_path} - {description}")
            all_good = False
    
    return all_good

def main():
    """Main cleanup routine."""
    print("=== GD-Downloader Project Cleanup ===")
    
    # Clean current directory
    removed_files, total_size = clean_directory('.')
    
    print(f"\n=== Cleanup Results ===")
    print(f"Files removed: {removed_files}")
    print(f"Space freed: {total_size / 1024:.2f} KB")
    
    # Organize files
    organize_files()
    
    # Check structure
    structure_ok = check_project_structure()
    
    print("\n=== Final Status ===")
    if structure_ok:
        print("[SUCCESS] Project structure is organized!")
    else:
        print("[WARNING] Some expected directories are missing.")
    
    print("[COMPLETE] Cleanup finished successfully!")
    
    return 0 if structure_ok else 1

if __name__ == "__main__":
    sys.exit(main())