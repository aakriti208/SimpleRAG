"""Announcement content handler."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler

logger = logging.getLogger(__name__)


class AnnouncementHandler(BaseContentHandler):
    """Handler for Canvas announcements."""

    content_type = "announcement"

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch all announcements for a course."""
        return self.client.get_announcements(course_id)

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from announcement item."""
        metadata = self._get_base_metadata(item, course_info)

        # Add announcement-specific metadata
        metadata.update({
            'posted_at': item.get('posted_at', ''),
            'author_id': str(item.get('author', {}).get('id', '')),
            'author_name': item.get('author', {}).get('display_name', ''),
        })

        return metadata

    def get_content_text(self, item: Dict) -> str:
        """Get announcement message."""
        return item.get('message', '')
