#!/usr/bin/env python3
"""
Script for automatic test structure reorganization.

This script reorganizes tests in the ./tests/ directory to duplicate 
the main project structure, creating a more organized hierarchy.

Usage:
    python scripts/reorganize_tests.py [--dry-run] [--backup] [--rollback]
"""

import os
import shutil
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime


class TestReorganizer:
    """Class for test structure reorganization"""
    
    def __init__(self, tests_dir: str = "tests", dry_run: bool = False):
        self.tests_dir = Path(tests_dir)
        self.dry_run = dry_run
        self.backup_dir = None
        self.moved_files = []
        self.updated_imports = []
        
        # Define structure for reorganization
        self.target_structure = {
            "repositories": [
                "test_user_repository.py",
                "test_api_key_repository.py", 
                "test_category_repository.py",
                "test_rss_feed_repository.py",
                "test_source_repository.py"
            ],
            "utils": [
                "test_utils.py",
                "test_utils_api.py",
                "test_utils_cleanup.py", 
                "test_utils_image.py",
                "test_utils_async_mocks.py",
                "test_utils_retry.py",
                "test_image.py",
                "test_image_utils.py",
                "test_video.py",
                "test_cleanup.py",
                "test_cache.py",
                "test_retry.py",
                "test_text.py"
            ],
            "exceptions": [
                "test_cache_exceptions.py",
                "test_database_exceptions.py",
                "test_service_exceptions.py",
                "test_exceptions.py"
            ],
            "services": {
                "translation": [
                    "test_translation_service.py"
                ],
                "text_analysis": [
                    "test_duplicate_detector.py"
                ],
                "user": [
                    "test_user_service.py"
                ],
                "email": [
                    "test_email.py",
                    "test_email_sender.py",
                    "test_registration_success_email.py"
                ],
                "maintenance": [
                    "test_maintenance_service.py"
                ]
            },
            "apps": {
                "api": {
                    "": [
                        "test_api.py",
                        "test_auth.py", 
                        "test_models.py",
                        "test_middleware.py",
                        "test_websocket.py"
                    ],
                    "routers": [
                        "test_api_keys.py",
                        "test_categories.py",
                        "test_rss_feeds.py",
                        "test_rss_items_router.py",
                        "test_rss_router.py",
                        "test_telegram.py",
                        "test_users.py"
                    ]
                },
                "rss_parser": {
                    "": [
                        "test_rss_fetcher.py",
                        "test_rss_manager.py",
                        "test_rss_storage.py",
                        "test_rss_validator.py"
                    ],
                    "services": [
                        "test_services.py"
                    ]
                }
            },
            "integration": [
                "test_di_integration.py",
                "test_database.py", 
                "test_database_pool_adapter.py",
                "test_app.py",
                "test_main.py"
            ]
        }
    
    def create_backup(self) -> Path:
        """Creates a backup copy of the current test structure"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.tests_dir.parent / f"tests_backup_{timestamp}"
        
        if not self.dry_run:
            print(f"Creating backup: {self.backup_dir}")
            shutil.copytree(self.tests_dir, self.backup_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        
        return self.backup_dir
    
    def create_directory_structure(self):
        """Creates the target directory structure"""
        print("Creating directory structure...")
        
        def create_dirs_recursive(structure: Dict, base_path: Path):
            for key, value in structure.items():
                dir_path = base_path / key
                
                if isinstance(value, list):
                    # Skip empty keys
                    if key == "":
                        continue
                    # Create directory and files as list
                    if not self.dry_run:
                        dir_path.mkdir(exist_ok=True)
                        (dir_path / "__init__.py").touch()
                    print(f"  Created: {dir_path}")
                elif isinstance(value, dict):
                    # Recursively create subdirectories
                    if not self.dry_run:
                        dir_path.mkdir(exist_ok=True)
                        (dir_path / "__init__.py").touch()
                    print(f"  Created: {dir_path}")
                    create_dirs_recursive(value, dir_path)
        
        create_dirs_recursive(self.target_structure, self.tests_dir)
    
    def move_files(self):
        """Moves files to corresponding directories"""
        print("Moving files to new structure...")
        
        # Flat list of all files to move
        files_to_move = []
        
        def collect_files(structure: Dict, current_path: List[str] = []):
            for key, value in structure.items():
                if isinstance(value, list):
                    # Skip empty keys
                    if key == "":
                        for filename in value:
                            files_to_move.append((filename, current_path))
                    else:
                        for filename in value:
                            files_to_move.append((filename, current_path + [key]))
                elif isinstance(value, dict):
                    collect_files(value, current_path + [key])
        
        collect_files(self.target_structure)
        
        for filename, target_path in files_to_move:
            source_file = self.tests_dir / filename
            target_dir = self.tests_dir / Path(*target_path)
            target_file = target_dir / filename
            
            if source_file.exists():
                if not self.dry_run:
                    # Create directory if it doesn't exist
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(source_file), str(target_file))
                    
                    # Create __init__.py if it doesn't exist
                    init_file = target_dir / "__init__.py"
                    if not init_file.exists():
                        init_file.touch()
                
                self.moved_files.append((source_file, target_file))
                print(f"  Moved: {filename} -> {'/'.join(target_path)}/")
            else:
                print(f"  WARNING: {filename} not found in tests directory")
    
    def update_imports(self):
        """Updates imports in moved files"""
        print("Updating imports in moved files...")
        
        for source_file, target_file in self.moved_files:
            try:
                if not target_file.exists():
                    continue
                    
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Regular expressions for finding imports
                import_patterns = [
                    r"from tests\.(\w+)",  # from tests.module
                    r"import tests\.(\w+)",  # import tests.module
                    r"from \.(\w+)",  # from .module
                ]
                
                for pattern in import_patterns:
                    def replace_import(match):
                        module_name = match.group(1)
                        relative_path = self.get_relative_import_path(target_file, module_name)
                        return match.group(0).replace(match.group(1), relative_path)
                    
                    content = re.sub(pattern, replace_import, content)
                
                if content != original_content:
                    if not self.dry_run:
                        with open(target_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                    
                    self.updated_imports.append(target_file)
                    print(f"  Updated imports in: {target_file.relative_to(self.tests_dir)}")
                    
            except Exception as e:
                print(f"  ERROR updating imports in {target_file}: {e}")
    
    def get_relative_import_path(self, target_file: Path, module_name: str) -> str:
        """Calculates relative import path"""
        # Determine where the module was moved to
        for structure_key, structure_value in self.target_structure.items():
            if isinstance(structure_value, list):
                if module_name in structure_value:
                    return str(Path(structure_key) / module_name).replace('.py', '')
            elif isinstance(structure_value, dict):
                def find_in_dict(d, target_module):
                    for key, value in d.items():
                        if isinstance(value, list):
                            if target_module in value:
                                return str(Path(structure_key) / key / target_module).replace('.py', '')
                        elif isinstance(value, dict):
                            result = find_in_dict(value, target_module)
                            if result:
                                return str(Path(structure_key) / key / result).replace('.py', '')
                    return None
                
                result = find_in_dict(structure_value, module_name)
                if result:
                    return result
        
        # If not found, return original name
        return module_name
    
    def clean_empty_files(self):
        """Removes empty files and old files"""
        print("Cleaning up...")
        
        # Remove files that were moved
        for source_file, _ in self.moved_files:
            if source_file.exists() and not self.dry_run:
                source_file.unlink()
                print(f"  Removed old file: {source_file.name}")
    
    def verify_structure(self):
        """Verifies correctness of new structure"""
        print("Verifying new structure...")
        
        def check_files_recursive(structure: Dict, base_path: Path):
            for key, value in structure.items():
                dir_path = base_path / key
                
                if isinstance(value, list):
                    # Skip empty keys
                    if key == "":
                        for filename in value:
                            file_path = base_path / filename
                            if file_path.exists():
                                print(f"  ✓ {filename}")
                            else:
                                print(f"  ✗ MISSING: {filename}")
                    else:
                        for filename in value:
                            file_path = dir_path / filename
                            if file_path.exists():
                                print(f"  ✓ {dir_path.name}/{filename}")
                            else:
                                print(f"  ✗ MISSING: {dir_path.name}/{filename}")
                elif isinstance(value, dict):
                    check_files_recursive(value, dir_path)
        
        check_files_recursive(self.target_structure, self.tests_dir)
    
    def generate_summary(self):
        """Generates reorganization report"""
        print("\n" + "="*50)
        print("REORGANIZATION SUMMARY")
        print("="*50)
        
        print(f"Moved files: {len(self.moved_files)}")
        for _, target_file in self.moved_files:
            print(f"  → {target_file.relative_to(self.tests_dir)}")
        
        print(f"\nUpdated imports: {len(self.updated_imports)}")
        for file_path in self.updated_imports:
            print(f"  → {file_path.relative_to(self.tests_dir)}")
        
        print(f"\nBackup created: {self.backup_dir}")
        print("="*50)
    
    def run(self):
        """Performs complete reorganization"""
        print(f"Starting test reorganization (dry_run={self.dry_run})")
        print(f"Tests directory: {self.tests_dir}")
        
        # Create backup
        self.create_backup()
        
        # Perform reorganization
        self.create_directory_structure()
        self.move_files()
        self.update_imports()
        self.clean_empty_files()
        self.verify_structure()
        self.generate_summary()
        
        print("\nReorganization completed!")


def main():
    parser = argparse.ArgumentParser(description="Reorganize test structure")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--backup", action="store_true", 
                       help="Always create backup")
    parser.add_argument("--rollback", type=str, 
                       help="Rollback from backup directory")
    
    args = parser.parse_args()
    
    if args.rollback:
        # Perform rollback
        backup_dir = Path(args.rollback)
        if backup_dir.exists():
            print(f"Rolling back from: {backup_dir}")
            if not args.dry_run:
                # Remove current tests and restore from backup
                shutil.rmtree("tests")
                shutil.copytree(backup_dir, "tests")
            print("Rollback completed!")
        else:
            print(f"Backup directory not found: {backup_dir}")
        return
    
    # Create and run reorganizer
    reorganizer = TestReorganizer(dry_run=args.dry_run)
    reorganizer.run()


if __name__ == "__main__":
    main()