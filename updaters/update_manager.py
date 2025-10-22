#!/usr/bin/env python3
"""
Update Manager - Centralized management of vocabulary updates
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from .hgnc_updater import HGNCUpdater
from .rxnorm_updater import RxNormUpdater


class UpdateManager:
    """
    Manages updates for all vocabularies
    """

    def __init__(self, vocab_dir: Optional[Path] = None):
        """
        Initialize update manager

        Args:
            vocab_dir: Vocabulary directory
        """
        self.vocab_dir = vocab_dir or (Path(__file__).parent.parent / 'vocabularies')
        self.updaters = {
            'hgnc': HGNCUpdater(vocab_dir),
            'rxnorm': RxNormUpdater(vocab_dir)
        }
        
        self.update_history_file = self.vocab_dir / 'update_history.json'
        self.update_history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """
        Load update history from file

        Returns:
            List of update records
        """
        if self.update_history_file.exists():
            with open(self.update_history_file, 'r') as f:
                return json.load(f)
        return []

    def _save_history(self):
        """Save update history to file"""
        with open(self.update_history_file, 'w') as f:
            json.dump(self.update_history, f, indent=2, default=str)

    def update_vocabulary(self, vocab_name: str, dry_run: bool = False) -> Dict:
        """
        Update a specific vocabulary

        Args:
            vocab_name: Vocabulary name ('hgnc', 'rxnorm')
            dry_run: If True, don't save changes

        Returns:
            Update result
        """
        if vocab_name not in self.updaters:
            return {
                'success': False,
                'error': f"Unknown vocabulary: {vocab_name}. Available: {list(self.updaters.keys())}"
            }

        updater = self.updaters[vocab_name]
        result = updater.update(dry_run=dry_run)

        # Record in history
        if result['success'] and not dry_run:
            self.update_history.append({
                'vocabulary': vocab_name,
                'timestamp': datetime.now().isoformat(),
                'changes': result.get('changes', {}),
                'filename': result.get('filename', '')
            })
            self._save_history()

        return result

    def update_all(self, dry_run: bool = False) -> Dict:
        """
        Update all vocabularies

        Args:
            dry_run: If True, don't save changes

        Returns:
            Combined update results
        """
        results = {}
        
        for vocab_name in self.updaters.keys():
            print(f"\n{'='*80}")
            print(f"Updating {vocab_name.upper()}...")
            print(f"{'='*80}")
            
            results[vocab_name] = self.update_vocabulary(vocab_name, dry_run=dry_run)

        return results

    def get_update_status(self) -> Dict:
        """
        Get status of all vocabularies

        Returns:
            Status information
        """
        status = {}

        for vocab_name, updater in self.updaters.items():
            filename = updater.get_vocabulary_filename()
            vocab_path = self.vocab_dir / filename
            
            if vocab_path.exists():
                with open(vocab_path, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
                    
                    status[vocab_name] = {
                        'exists': True,
                        'filename': filename,
                        'last_updated': metadata.get('last_updated', 'Unknown'),
                        'version': metadata.get('version', 'Unknown'),
                        'count': self._get_item_count(data)
                    }
            else:
                status[vocab_name] = {
                    'exists': False,
                    'filename': filename
                }

        return status

    def _get_item_count(self, data: Dict) -> int:
        """
        Get count of items in vocabulary

        Args:
            data: Vocabulary data

        Returns:
            Item count
        """
        for key in data.keys():
            if key != 'metadata' and isinstance(data[key], dict):
                return len(data[key])
        return 0

    def list_backups(self, vocab_name: str) -> List[Dict]:
        """
        List backups for a vocabulary

        Args:
            vocab_name: Vocabulary name

        Returns:
            List of backup info
        """
        if vocab_name not in self.updaters:
            return []

        updater = self.updaters[vocab_name]
        filename = updater.get_vocabulary_filename()
        return updater.list_backups(filename)

    def rollback(self, vocab_name: str, backup_file: Optional[str] = None) -> bool:
        """
        Rollback a vocabulary to previous version

        Args:
            vocab_name: Vocabulary name
            backup_file: Specific backup file (or most recent if None)

        Returns:
            True if successful
        """
        if vocab_name not in self.updaters:
            return False

        updater = self.updaters[vocab_name]
        filename = updater.get_vocabulary_filename()
        return updater.rollback(filename, backup_file)

    def get_update_history(self, vocab_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get update history

        Args:
            vocab_name: Filter by vocabulary name (None for all)
            limit: Maximum number of entries

        Returns:
            List of update records
        """
        history = self.update_history

        if vocab_name:
            history = [h for h in history if h.get('vocabulary') == vocab_name]

        return sorted(history, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def clean_old_backups(self, vocab_name: Optional[str] = None, keep_last_n: int = 5):
        """
        Clean old backups

        Args:
            vocab_name: Vocabulary name (None for all)
            keep_last_n: Number of backups to keep
        """
        if vocab_name:
            if vocab_name in self.updaters:
                self.updaters[vocab_name].clear_old_backups(keep_last_n)
        else:
            for updater in self.updaters.values():
                updater.clear_old_backups(keep_last_n)
