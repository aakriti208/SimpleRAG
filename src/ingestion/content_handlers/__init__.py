"""Content handlers for different Canvas content types."""

from .page_handler import PageHandler
from .module_handler import ModuleHandler
from .assignment_handler import AssignmentHandler
from .announcement_handler import AnnouncementHandler
from .discussion_handler import DiscussionHandler
from .file_handler import FileHandler
from .syllabus_handler import SyllabusHandler

__all__ = [
    'PageHandler',
    'ModuleHandler',
    'AssignmentHandler',
    'AnnouncementHandler',
    'DiscussionHandler',
    'FileHandler',
    'SyllabusHandler',
]
