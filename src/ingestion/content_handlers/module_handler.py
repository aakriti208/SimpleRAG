"""Module content handler."""

import logging
from typing import List, Dict
from .base_handler import BaseContentHandler

logger = logging.getLogger(__name__)


class ModuleHandler(BaseContentHandler):
    """Handler for Canvas modules and module items."""

    content_type = "module"

    def fetch_content(self, course_id: str) -> List[Dict]:
        """Fetch all modules and their items."""
        modules = self.client.get_modules(course_id)
        all_items = []

        for module in modules:
            try:
                module_id = module.get('id')
                items = self.client.get_module_items(course_id, module_id)

                # Attach module context to each item
                for item in items:
                    item['module_name'] = module.get('name', '')
                    item['module_position'] = module.get('position', 0)
                    item['module_id'] = module_id

                all_items.extend(items)

            except Exception as e:
                logger.warning(f"Error fetching module {module.get('name')}: {e}")
                continue

        return all_items

    def extract_metadata(self, item: Dict, course_info: Dict) -> Dict:
        """Extract metadata from module item."""
        metadata = self._get_base_metadata(item, course_info)

        # Add module-specific metadata
        metadata.update({
            'module_name': item.get('module_name', ''),
            'module_position': item.get('module_position', 0),
            'module_id': str(item.get('module_id', '')),
            'item_type': item.get('type', ''),
            'position': item.get('position', 0),
        })

        return metadata

    def get_content_text(self, item: Dict) -> str:
        """Get module item content."""
        # Module items can have different content based on type
        content = item.get('content_details', {}).get('body', '')
        if not content:
            content = item.get('title', '') + '\n' + item.get('text', '')
        return content
