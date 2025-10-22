#!/usr/bin/env python3
"""
Vocabulary Update CLI Tool
Usage: python3 update_vocabularies.py [command] [options]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from updaters.update_manager import UpdateManager


def cmd_status(manager: UpdateManager, args):
    """Show status of all vocabularies"""
    print("="*80)
    print("📊 VOCABULARY STATUS")
    print("="*80)
    
    status = manager.get_update_status()
    
    for vocab_name, info in status.items():
        print(f"\n🔹 {vocab_name.upper()}")
        if info['exists']:
            print(f"   File: {info['filename']}")
            print(f"   Last Updated: {info['last_updated']}")
            print(f"   Version: {info['version']}")
            print(f"   Items: {info['count']}")
        else:
            print(f"   ❌ Not found: {info['filename']}")


def cmd_update(manager: UpdateManager, args):
    """Update vocabularies"""
    vocab = args.vocabulary
    dry_run = args.dry_run
    
    print("="*80)
    if vocab == 'all':
        print(f"🔄 UPDATING ALL VOCABULARIES {'(DRY RUN)' if dry_run else ''}")
    else:
        print(f"🔄 UPDATING {vocab.upper()} {'(DRY RUN)' if dry_run else ''}")
    print("="*80)
    
    if vocab == 'all':
        results = manager.update_all(dry_run=dry_run)
        
        print("\n" + "="*80)
        print("📊 UPDATE SUMMARY")
        print("="*80)
        
        for vocab_name, result in results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"\n{status} {vocab_name.upper()}")
            
            if result.get('changes'):
                changes = result['changes']
                if 'new_file' not in changes:
                    print(f"   Added: {len(changes.get('added', []))}")
                    print(f"   Modified: {len(changes.get('modified', []))}")
                    print(f"   Removed: {len(changes.get('removed', []))}")
            
            if result.get('errors'):
                for error in result['errors']:
                    print(f"   Error: {error}")
    
    else:
        result = manager.update_vocabulary(vocab, dry_run=dry_run)
        
        if result.get('success'):
            print(f"\n✅ Update successful")
            
            if result.get('changes'):
                changes = result['changes']
                if 'new_file' not in changes:
                    print(f"\n📈 Changes:")
                    print(f"   Added: {len(changes.get('added', []))}")
                    print(f"   Modified: {len(changes.get('modified', []))}")
                    print(f"   Removed: {len(changes.get('removed', []))}")
                    print(f"   Unchanged: {changes.get('unchanged', 0)}")
        else:
            print(f"\n❌ Update failed")
            if result.get('error'):
                print(f"   Error: {result['error']}")


def cmd_history(manager: UpdateManager, args):
    """Show update history"""
    print("="*80)
    print("📜 UPDATE HISTORY")
    print("="*80)
    
    history = manager.get_update_history(args.vocabulary, limit=args.limit)
    
    if not history:
        print("\nNo update history found")
        return
    
    for entry in history:
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        vocab = entry.get('vocabulary', 'unknown')
        
        print(f"\n🕒 {timestamp} - {vocab.upper()}")
        print(f"   File: {entry.get('filename', 'unknown')}")
        
        if 'changes' in entry:
            changes = entry['changes']
            if 'new_file' not in changes:
                print(f"   Changes: +{len(changes.get('added', []))} / ~{len(changes.get('modified', []))} / -{len(changes.get('removed', []))}")


def cmd_backups(manager: UpdateManager, args):
    """List backups"""
    vocab = args.vocabulary
    
    print("="*80)
    print(f"💾 BACKUPS - {vocab.upper()}")
    print("="*80)
    
    backups = manager.list_backups(vocab)
    
    if not backups:
        print(f"\nNo backups found for {vocab}")
        return
    
    for backup in backups:
        timestamp = datetime.fromisoformat(backup['created']).strftime('%Y-%m-%d %H:%M:%S')
        size_kb = backup['size'] / 1024
        
        print(f"\n📦 {backup['filename']}")
        print(f"   Created: {timestamp}")
        print(f"   Size: {size_kb:.1f} KB")


def cmd_rollback(manager: UpdateManager, args):
    """Rollback to previous version"""
    vocab = args.vocabulary
    
    print("="*80)
    print(f"⏪ ROLLBACK - {vocab.upper()}")
    print("="*80)
    
    # Show available backups
    backups = manager.list_backups(vocab)
    
    if not backups:
        print(f"\n❌ No backups available for {vocab}")
        return
    
    print(f"\nAvailable backups:")
    for i, backup in enumerate(backups[:5], 1):
        timestamp = datetime.fromisoformat(backup['created']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"   {i}. {backup['filename']} ({timestamp})")
    
    # Confirm rollback
    if not args.yes:
        response = input(f"\n⚠️  Rollback to most recent backup? (y/n): ")
        if response.lower() != 'y':
            print("❌ Rollback cancelled")
            return
    
    # Perform rollback
    success = manager.rollback(vocab)
    
    if success:
        print(f"\n✅ Rolled back successfully")
    else:
        print(f"\n❌ Rollback failed")


def cmd_clean(manager: UpdateManager, args):
    """Clean old backups"""
    vocab = args.vocabulary if args.vocabulary != 'all' else None
    keep = args.keep
    
    print("="*80)
    print(f"🧹 CLEANING OLD BACKUPS")
    print("="*80)
    print(f"\nKeeping last {keep} backups per vocabulary")
    
    if not args.yes:
        response = input(f"\n⚠️  Continue? (y/n): ")
        if response.lower() != 'y':
            print("❌ Cleaning cancelled")
            return
    
    manager.clean_old_backups(vocab, keep_last_n=keep)
    print(f"\n✅ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(
        description='MTBParser Vocabulary Update Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Status command
    subparsers.add_parser('status', help='Show vocabulary status')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update vocabularies')
    update_parser.add_argument('vocabulary', choices=['all', 'hgnc', 'rxnorm'],
                               help='Vocabulary to update')
    update_parser.add_argument('--dry-run', action='store_true',
                              help='Perform dry run without saving')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show update history')
    history_parser.add_argument('--vocabulary', choices=['hgnc', 'rxnorm'],
                               help='Filter by vocabulary')
    history_parser.add_argument('--limit', type=int, default=10,
                               help='Number of entries to show')
    
    # Backups command
    backups_parser = subparsers.add_parser('backups', help='List backups')
    backups_parser.add_argument('vocabulary', choices=['hgnc', 'rxnorm'],
                               help='Vocabulary to list backups for')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to previous version')
    rollback_parser.add_argument('vocabulary', choices=['hgnc', 'rxnorm'],
                                help='Vocabulary to rollback')
    rollback_parser.add_argument('--yes', action='store_true',
                                help='Skip confirmation')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old backups')
    clean_parser.add_argument('vocabulary', choices=['all', 'hgnc', 'rxnorm'],
                             help='Vocabulary to clean backups for')
    clean_parser.add_argument('--keep', type=int, default=5,
                             help='Number of backups to keep')
    clean_parser.add_argument('--yes', action='store_true',
                             help='Skip confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    manager = UpdateManager()
    
    # Execute command
    commands = {
        'status': cmd_status,
        'update': cmd_update,
        'history': cmd_history,
        'backups': cmd_backups,
        'rollback': cmd_rollback,
        'clean': cmd_clean
    }
    
    if args.command in commands:
        commands[args.command](manager, args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
