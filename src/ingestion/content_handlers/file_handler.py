"""File content handler (PDF/PowerPoint)."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler
from src.config import MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)


class FileHandler(BaseContentHandler):
    """Handler for Canvas files (PDF and PowerPoint)."""

    content_type = "file"

    SUPPORTED_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-powerpoint'
    ]

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch all supported files for a course."""
        files = self.client.get_files(course_id)

        # Filter for supported types and size
        supported_files = []
        for file in files:
            if self._should_process_file(file):
                supported_files.append(file)

        logger.info(f"Found {len(supported_files)} processable files out of {len(files)} total files")
        return supported_files

    def _should_process_file(self, file_item: Dict) -> bool:
        """Check if file should be processed."""
        # Check file size
        file_size = file_item.get('size', 0)
        max_size = MAX_FILE_SIZE_MB * 1024 * 1024

        if file_size > max_size:
            logger.debug(f"Skipping large file {file_item.get('display_name')}: {file_size / 1024 / 1024:.1f}MB")
            return False

        # Check file type
        content_type = file_item.get('content-type', file_item.get('mime_class', ''))
        if content_type not in self.SUPPORTED_TYPES:
            logger.debug(f"Skipping unsupported file type: {content_type}")
            return False

        return True

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from file item."""
        metadata = self._get_base_metadata(item, course_info)

        # Add file-specific metadata
        metadata.update({
            'file_type': self._get_file_type(item),
            'file_size': item.get('size', 0),
            'display_name': item.get('display_name', ''),
        })

        return metadata

    def _get_file_type(self, item: Dict) -> str:
        """Determine file type from content-type."""
        content_type = item.get('content-type', item.get('mime_class', ''))
        if 'pdf' in content_type.lower():
            return 'pdf'
        elif 'powerpoint' in content_type.lower() or 'presentation' in content_type.lower():
            return 'pptx'
        return 'unknown'

    def process_content(self, course_id: str, course_name: str) -> List[Dict]:
        """Process files with special handling for binary content."""
        logger.info(f"Processing {self.content_type} content for course {course_id}")

        try:
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

                    # Download file content
                    file_id = item.get('id')
                    file_bytes = self.client.get_file(file_id)

                    # Process based on file type
                    file_type = self._get_file_type(item)
                    mime_type = item.get('content-type', '')

                    if file_type == 'pdf':
                        chunks = self.processor.process_pdf_content(file_bytes, metadata)
                    elif file_type == 'pptx':
                        chunks = self.processor.process_pptx_content(file_bytes, metadata)
                    else:
                        logger.warning(f"Unsupported file type for {item.get('display_name')}")
                        continue

                    if chunks:
                        all_chunks.extend(chunks)
                        logger.debug(f"Processed {item.get('display_name')}: {len(chunks)} chunks")
                    else:
                        logger.warning(f"No chunks generated for file {item.get('display_name')}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing file {item.get('display_name')}: {e}")
                    continue

            if failed_count > 0:
                logger.warning(f"Failed to process {failed_count} files")

            logger.info(f"Generated {len(all_chunks)} chunks from {len(raw_items)} files")
            return all_chunks

        except Exception as e:
            logger.error(f"Error fetching file content: {e}")
            return []
