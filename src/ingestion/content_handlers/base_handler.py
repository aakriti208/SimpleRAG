"""
Base Content Handler

Abstract base class for all Canvas content type handlers.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseContentHandler(ABC):
    """Base class for handling different Canvas content types."""

    content_type = "base"  # Override in subclasses

    def __init__(self, canvas_client, doc_processor):
        """
        Initialize handler.

        Args:
            canvas_client: CanvasClient instance
            doc_processor: DocumentProcessor instance
        """
        self.client = canvas_client
        self.processor = doc_processor

    @abstractmethod
    def fetch_content(self, course_id: str) -> List[Dict]:
        """
        Fetch raw content from Canvas API.

        Args:
            course_id: Canvas course ID

        Returns:
            List of content items from Canvas API
        """
        pass

    @abstractmethod
    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """
        Extract metadata from Canvas API response.

        Args:
            item: Content item from Canvas API
            course_info: Dict with course_id and course_name

        Returns:
            Metadata dict
        """
        pass

    def get_content_text(self, item: Dict) -> str:
        """
        Get text content from item (to be overridden if needed).

        Args:
            item: Content item

        Returns:
            HTML or text content
        """
        # Default: look for common Canvas fields
        return item.get('body', item.get('description', item.get('message', '')))

    def process_content(self, course_id: str, course_name: str) -> List[Dict]:
        """
        Main processing pipeline for this content type.

        Args:
            course_id: Canvas course ID
            course_name: Course name

        Returns:
            List of chunks with metadata
        """
        logger.info(f"Processing {self.content_type} content for course {course_id}")

        try:
            # Fetch raw items from Canvas
            raw_items = self.fetch_content(course_id)
            logger.info(f"Fetched {len(raw_items)} {self.content_type} items")

            all_chunks = []
            failed_count = 0

            for item in raw_items:
                try:
                    # Extract metadata
                    metadata = self.extract_metadata(item, {
                        'course_id': course_id,
                        'course_name': course_name
                    })

                    # Get content text
                    content_text = self.get_content_text(item)

                    if not content_text or not content_text.strip():
                        logger.debug(f"Skipping {self.content_type} item {item.get('id')} - no content")
                        continue

                    # Process into chunks
                    chunks = self.processor.process_html_content(content_text, metadata)

                    if chunks:
                        all_chunks.extend(chunks)
                    else:
                        logger.warning(f"No chunks generated for {self.content_type} item {item.get('id')}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing {self.content_type} item {item.get('id')}: {e}")
                    continue

            if failed_count > 0:
                logger.warning(f"Failed to process {failed_count} {self.content_type} items")

            logger.info(f"Generated {len(all_chunks)} chunks from {len(raw_items)} {self.content_type} items")
            return all_chunks

        except Exception as e:
            logger.error(f"Error fetching {self.content_type} content: {e}")
            return []

    def _get_base_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """
        Get base metadata fields common to all content types.

        Args:
            item: Content item
            course_info: Course information

        Returns:
            Base metadata dict
        """
        # Generate unique content_id
        item_id = item.get('id') or item.get('page_id')
        if not item_id:
            # Fallback: use title hash for items without ID
            import hashlib
            title = item.get('title', item.get('name', 'untitled'))
            item_id = hashlib.md5(title.encode()).hexdigest()[:12]

        return {
            'content_id': str(item_id),
            'content_type': self.content_type,
            'course_id': course_info.get('course_id', ''),
            'course_name': course_info.get('course_name', ''),
            'title': item.get('title', item.get('name', 'Untitled')),
            'source': 'Canvas LMS',
            'url': item.get('html_url', ''),
            'created_at': item.get('created_at', ''),
            'updated_at': item.get('updated_at', ''),
            'ingested_at': datetime.now().isoformat(),
        }
