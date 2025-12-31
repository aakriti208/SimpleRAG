"""
Metadata Tracker

Tracks ingestion state for incremental updates by monitoring:
- Which content items have been processed
- When they were last updated
- Which items have been deleted
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from src.config import METADATA_DIR

logger = logging.getLogger(__name__)


class MetadataTracker:
    """Tracks ingestion state for incremental updates."""

    def __init__(self, state_file: Path = None):
        """
        Initialize metadata tracker.

        Args:
            state_file: Path to state file (default: data/metadata/ingestion_state.json)
        """
        self.state_file = state_file or (METADATA_DIR / 'ingestion_state.json')
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """
        Load state from file.

        Returns:
            State dict
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading state file: {e}")
                return self._get_empty_state()
        return self._get_empty_state()

    def _get_empty_state(self) -> Dict:
        """
        Get empty state structure.

        Returns:
            Empty state dict
        """
        return {
            'last_full_sync': None,
            'courses': {},
            'content_items': {}
        }

    def _save_state(self):
        """Save state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state file: {e}")

    def should_process_item(self, content_id: str, updated_at: str) -> bool:
        """
        Check if item needs processing based on updated_at timestamp.

        Args:
            content_id: Canvas content ID
            updated_at: ISO 8601 timestamp from Canvas

        Returns:
            True if item should be processed (new or modified)
        """
        item_key = f"item_{content_id}"

        if item_key not in self.state['content_items']:
            return True  # New item

        last_updated = self.state['content_items'][item_key].get('updated_at')
        if not last_updated:
            return True

        # Compare timestamps (ISO 8601 strings compare lexicographically)
        return updated_at > last_updated

    def mark_item_processed(self, content_id: str, content_type: str,
                           updated_at: str, chunk_count: int):
        """
        Record that an item has been processed.

        Args:
            content_id: Canvas content ID
            content_type: Type of content (page, assignment, etc.)
            updated_at: When the item was last updated in Canvas
            chunk_count: Number of chunks generated
        """
        item_key = f"item_{content_id}"
        self.state['content_items'][item_key] = {
            'content_type': content_type,
            'updated_at': updated_at,
            'processed_at': datetime.now().isoformat(),
            'chunk_count': chunk_count,
            'deleted': False
        }
        self._save_state()

    def mark_item_deleted(self, content_id: str):
        """
        Mark item as deleted (for cleanup).

        Args:
            content_id: Canvas content ID
        """
        item_key = f"item_{content_id}"
        if item_key in self.state['content_items']:
            self.state['content_items'][item_key]['deleted'] = True
            self._save_state()

    def get_deleted_items(self) -> list:
        """
        Get list of deleted content IDs.

        Returns:
            List of content IDs marked as deleted
        """
        deleted = []
        for item_key, item_data in self.state['content_items'].items():
            if item_data.get('deleted', False):
                content_id = item_key.replace('item_', '')
                deleted.append(content_id)
        return deleted

    def get_last_sync_time(self, course_id: str) -> Optional[str]:
        """
        Get last sync timestamp for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            ISO 8601 timestamp or None
        """
        return self.state['courses'].get(course_id, {}).get('last_sync')

    def update_course_sync(self, course_id: str):
        """
        Update last sync time for a course.

        Args:
            course_id: Canvas course ID
        """
        if course_id not in self.state['courses']:
            self.state['courses'][course_id] = {}

        self.state['courses'][course_id]['last_sync'] = datetime.now().isoformat()
        self._save_state()

    def update_full_sync(self):
        """Mark that a full sync was completed."""
        self.state['last_full_sync'] = datetime.now().isoformat()
        self._save_state()

    def get_stats(self) -> Dict:
        """
        Get ingestion statistics.

        Returns:
            Stats dict with counts and timestamps
        """
        total_items = len(self.state['content_items'])
        deleted_items = sum(
            1 for item in self.state['content_items'].values()
            if item.get('deleted', False)
        )
        active_items = total_items - deleted_items

        # Count by content type
        by_type = {}
        for item_data in self.state['content_items'].values():
            if not item_data.get('deleted', False):
                content_type = item_data.get('content_type', 'unknown')
                by_type[content_type] = by_type.get(content_type, 0) + 1

        return {
            'total_items': total_items,
            'active_items': active_items,
            'deleted_items': deleted_items,
            'by_type': by_type,
            'last_full_sync': self.state.get('last_full_sync'),
            'courses_tracked': len(self.state['courses'])
        }

    def reset(self):
        """Reset all tracking state."""
        self.state = self._get_empty_state()
        self._save_state()
        logger.info("Metadata tracker reset")
