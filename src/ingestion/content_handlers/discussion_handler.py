"""Discussion content handler."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler

logger = logging.getLogger(__name__)


class DiscussionHandler(BaseContentHandler):
    """Handler for Canvas discussion topics and entries."""

    content_type = "discussion"

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch all discussion topics and their entries."""
        topics = self.client.get_discussions(course_id)
        all_content = []

        for topic in topics:
            # Skip if this is an announcement (handled separately)
            if topic.get('is_announcement'):
                continue

            try:
                # Add main topic
                all_content.append({
                    'type': 'topic',
                    'data': topic
                })

                # Fetch and add discussion entries
                topic_id = topic.get('id')
                if topic_id:
                    entries = self.client.get_discussion_entries(course_id, topic_id)

                    for entry in entries:
                        all_content.append({
                            'type': 'entry',
                            'parent_topic_id': topic_id,
                            'parent_topic_title': topic.get('title', ''),
                            'data': entry
                        })

            except Exception as e:
                logger.warning(f"Error fetching discussion {topic.get('title')}: {e}")
                continue

        return all_content

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from discussion item."""
        if item['type'] == 'topic':
            data = item['data']
            metadata = self._get_base_metadata(data, course_info)
            metadata.update({
                'discussion_type': data.get('discussion_type', 'threaded'),
                'is_topic': True,
            })
        else:  # entry
            data = item['data']
            metadata = {
                'content_id': str(data.get('id', 'unknown')),
                'content_type': 'discussion_entry',
                'course_id': course_info.get('course_id', ''),
                'course_name': course_info.get('course_name', ''),
                'title': f"Reply to: {item['parent_topic_title']}",
                'source': 'Canvas LMS',
                'url': '',
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
                'parent_topic_id': str(item['parent_topic_id']),
                'author_id': str(data.get('user_id', '')),
                'is_topic': False,
            }

        return metadata

    def get_content_text(self, item: Dict) -> str:
        """Get discussion content."""
        data = item['data']
        return data.get('message', '')
