"""Assignment content handler."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler

logger = logging.getLogger(__name__)


class AssignmentHandler(BaseContentHandler):
    """Handler for Canvas assignments."""

    content_type = "assignment"

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch all assignments for a course."""
        return self.client.get_assignments(course_id)

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from assignment item."""
        metadata = self._get_base_metadata(item, course_info)

        # Add assignment-specific metadata
        metadata.update({
            'assignment_type': item.get('submission_types', ['none'])[0] if item.get('submission_types') else 'none',
            'points_possible': item.get('points_possible', 0),
            'due_date': item.get('due_at', ''),
            'has_rubric': bool(item.get('rubric', [])),
            'published': item.get('published', False),
        })

        return metadata

    def get_content_text(self, item: Dict) -> str:
        """Get assignment description and rubric."""
        content = item.get('description', '')

        # Add rubric information if available
        rubric = item.get('rubric', [])
        if rubric:
            rubric_text = "\n\nRubric:\n"
            for criterion in rubric:
                rubric_text += f"\n{criterion.get('description', '')}"
                rubric_text += f" ({criterion.get('points', 0)} points)"
            content += rubric_text

        return content
