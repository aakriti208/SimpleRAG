"""Page content handler."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler

logger = logging.getLogger(__name__)


class PageHandler(BaseContentHandler):
    """Handler for Canvas course pages."""

    content_type = "page"

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch all pages for a course."""
        pages = self.client.get_pages(course_id)

        # Fetch full content for each page
        full_pages = []
        for page in pages:
            try:
                page_url = page.get('url')
                if page_url:
                    full_page = self.client.get_page_content(course_id, page_url)
                    full_pages.append(full_page)
            except Exception as e:
                logger.warning(f"Could not fetch page {page.get('title')}: {e}")
                continue

        return full_pages

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from page item."""
        metadata = self._get_base_metadata(item, course_info)

        # Add page-specific metadata
        metadata.update({
            'published': item.get('published', False),
            'front_page': item.get('front_page', False),
        })

        return metadata

    def get_content_text(self, item: Dict) -> str:
        """Get page body content."""
        return item.get('body', '')
