#!/usr/bin/env python3
"""
Base Vocabulary Updater - Abstract base class for vocabulary updates
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from abc import ABC, abstractmethod


class VocabularyUpdater(ABC):
    """
    Abstract base class for vocabulary updaters.
    Provides common functionality for backup, versioning, and file management.
    """

    def __init__(self, vocab_dir: Optional[Path] = None, backup_dir: Optional[Path] = None):
        """
        Initialize updater

        Args:
            vocab_dir: Directory containing vocabulary files
            backup_dir: Directory for backups (default: vocab_dir/backups)
        """
        if vocab_dir is None:
            vocab_dir = Path(__file__).parent.parent / 'vocabularies'
        else:
            vocab_dir = Path(vocab_dir)

        self.vocab_dir = vocab_dir
        self.backup_dir = backup_dir or (vocab_dir / 'backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Update metadata
        self.last_update = None
        self.update_log = []

    @abstractmethod
    def fetch_data(self) -> Dict:
        """
        Fetch data from external API.
        Must be implemented by subclasses.

        Returns:
            Dictionary with fetched data
        """
        pass

    @abstractmethod
    def transform_data(self, raw_data: Dict) -> Dict:
        """
        Transform fetched data to vocabulary format.
        Must be implemented by subclasses.

        Args:
            raw_data: Raw data from API

        Returns:
            Transformed data ready for vocabulary file
        """
        pass

    @abstractmethod
    def get_vocabulary_filename(self) -> str:
        """
        Get the vocabulary filename.
        Must be implemented by subclasses.

        Returns:
            Filename (e.g., 'hgnc_genes.json')
        """
        pass

    def backup_vocabulary(self, filename: str) -> Optional[Path]:
        """
        Create backup of existing vocabulary file

        Args:
            filename: Vocabulary filename

        Returns:
            Path to backup file, or None if original doesn't exist
        """
        original_path = self.vocab_dir / filename
        if not original_path.exists():
            return None

        # Create timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{filename.replace('.json', '')}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(original_path, backup_path)
        
        self._log(f"Backup created: {backup_path}")
        return backup_path

    def save_vocabulary(self, data: Dict, filename: str, create_backup: bool = True) -> Path:
        """
        Save vocabulary data to file

        Args:
            data: Vocabulary data
            filename: Filename to save
            create_backup: Whether to create backup first

        Returns:
            Path to saved file
        """
        # Create backup if requested
        if create_backup:
            self.backup_vocabulary(filename)

        # Save new data
        output_path = self.vocab_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._log(f"Vocabulary saved: {output_path}")
        return output_path

    def load_vocabulary(self, filename: str) -> Optional[Dict]:
        """
        Load existing vocabulary file

        Args:
            filename: Vocabulary filename

        Returns:
            Vocabulary data, or None if file doesn't exist
        """
        vocab_path = self.vocab_dir / filename
        if not vocab_path.exists():
            return None

        with open(vocab_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def rollback(self, filename: str, backup_file: Optional[str] = None) -> bool:
        """
        Rollback to a previous backup

        Args:
            filename: Current vocabulary filename
            backup_file: Specific backup file to restore (if None, uses most recent)

        Returns:
            True if rollback successful
        """
        # Find backup to restore
        if backup_file is None:
            # Get most recent backup
            pattern = f"{filename.replace('.json', '')}_*.json"
            backups = sorted(self.backup_dir.glob(pattern), reverse=True)
            if not backups:
                self._log(f"No backups found for {filename}")
                return False
            backup_path = backups[0]
        else:
            backup_path = self.backup_dir / backup_file

        if not backup_path.exists():
            self._log(f"Backup file not found: {backup_path}")
            return False

        # Restore backup
        vocab_path = self.vocab_dir / filename
        shutil.copy2(backup_path, vocab_path)

        self._log(f"Rolled back to: {backup_path}")
        return True

    def list_backups(self, filename: str) -> List[Dict]:
        """
        List all backups for a vocabulary file

        Args:
            filename: Vocabulary filename

        Returns:
            List of backup info dictionaries
        """
        pattern = f"{filename.replace('.json', '')}_*.json"
        backups = sorted(self.backup_dir.glob(pattern), reverse=True)

        backup_list = []
        for backup_path in backups:
            stat = backup_path.stat()
            backup_list.append({
                'filename': backup_path.name,
                'path': str(backup_path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return backup_list

    def update(self, dry_run: bool = False) -> Dict:
        """
        Perform complete update workflow

        Args:
            dry_run: If True, don't save changes

        Returns:
            Update result dictionary
        """
        result = {
            'success': False,
            'filename': self.get_vocabulary_filename(),
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'changes': {},
            'errors': []
        }

        try:
            # Fetch data
            self._log(f"Fetching data from API...")
            raw_data = self.fetch_data()
            
            if not raw_data:
                raise ValueError("No data fetched from API")

            # Transform data
            self._log(f"Transforming data...")
            transformed_data = self.transform_data(raw_data)

            # Load existing vocabulary
            filename = self.get_vocabulary_filename()
            existing_data = self.load_vocabulary(filename)

            # Calculate changes
            if existing_data:
                result['changes'] = self._calculate_changes(existing_data, transformed_data)
            else:
                result['changes'] = {'new_file': True}

            # Save if not dry run
            if not dry_run:
                self.save_vocabulary(transformed_data, filename, create_backup=True)
                result['success'] = True
            else:
                result['success'] = True
                result['note'] = 'Dry run - no changes saved'

            self.last_update = datetime.now()

        except Exception as e:
            result['errors'].append(str(e))
            self._log(f"Error during update: {e}")

        return result

    def _calculate_changes(self, old_data: Dict, new_data: Dict) -> Dict:
        """
        Calculate differences between old and new vocabulary data

        Args:
            old_data: Existing vocabulary
            new_data: New vocabulary

        Returns:
            Dictionary describing changes
        """
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'unchanged': 0
        }

        # Get main data key (e.g., 'genes', 'drugs', 'diagnoses')
        data_key = self._get_main_data_key(new_data)
        
        if data_key not in old_data or data_key not in new_data:
            return changes

        old_items = old_data[data_key]
        new_items = new_data[data_key]

        old_keys = set(old_items.keys())
        new_keys = set(new_items.keys())

        # Find changes
        changes['added'] = list(new_keys - old_keys)
        changes['removed'] = list(old_keys - new_keys)
        
        # Check for modifications
        for key in old_keys & new_keys:
            if old_items[key] != new_items[key]:
                changes['modified'].append(key)
            else:
                changes['unchanged'] += 1

        return changes

    def _get_main_data_key(self, data: Dict) -> Optional[str]:
        """
        Get the main data key from vocabulary structure

        Args:
            data: Vocabulary data

        Returns:
            Main data key (e.g., 'genes', 'drugs')
        """
        # Skip metadata
        for key in data.keys():
            if key != 'metadata':
                return key
        return None

    def _log(self, message: str):
        """
        Log update message

        Args:
            message: Log message
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.update_log.append(log_entry)
        print(log_entry)

    def get_update_log(self) -> List[str]:
        """
        Get update log entries

        Returns:
            List of log entries
        """
        return self.update_log.copy()

    def clear_old_backups(self, keep_last_n: int = 5):
        """
        Remove old backups, keeping only the most recent N

        Args:
            keep_last_n: Number of recent backups to keep
        """
        filename = self.get_vocabulary_filename()
        pattern = f"{filename.replace('.json', '')}_*.json"
        backups = sorted(self.backup_dir.glob(pattern), reverse=True)

        # Remove old backups
        for backup in backups[keep_last_n:]:
            backup.unlink()
            self._log(f"Removed old backup: {backup.name}")
