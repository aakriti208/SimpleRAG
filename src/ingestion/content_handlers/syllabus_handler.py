"""Syllabus content handler."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler

logger = logging.getLogger(__name__)


class SyllabusHandler(BaseContentHandler):
    """Handler for Canvas course syllabus."""

    content_type = "syllabus"

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch course syllabus."""
        course_data = self.client.get_course(course_id, include_syllabus=True)

        # Only return if syllabus_body exists and has content
        syllabus_body = course_data.get('syllabus_body', '')
        print(f"this is the syllabus body", syllabus_body)
        if syllabus_body and syllabus_body.strip():
            # Create a pseudo-item with the syllabus data
            return [{
                'id': f"{course_id}_syllabus",
                'title': f"{course_data.get('name', 'Course')} - Syllabus",
                'name': 'Course Syllabus',
                'body': syllabus_body,
                'html_url': course_data.get('html_url', ''),
                'created_at': course_data.get('created_at', ''),
                'updated_at': course_data.get('updated_at', ''),
                'course_code': course_data.get('course_code', ''),
            }]

        return []

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from syllabus."""
        metadata = self._get_base_metadata(item, course_info)

        # Add syllabus-specific metadata
        metadata.update({
            'course_code': item.get('course_code', ''),
            'is_syllabus': True,
        })

        return metadata

    def get_content_text(self, item: Dict) -> str:
        """Get syllabus content."""
        return item.get('body', '')
