"""
Canvas LMS API Client

Handles all interactions with the Canvas LMS API 

"""

import requests
import time
import logging
from typing import List, Dict, Optional
from src.config import INGEST_RATE_LIMIT_THRESHOLD

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 5, 15]  # seconds


class CanvasAPIError(Exception):
    """Base exception for Canvas API errors."""
    pass


class RateLimitError(CanvasAPIError):
    """Rate limit exceeded."""
    pass


class AuthenticationError(CanvasAPIError):
    """Invalid API token."""
    pass


class NotFoundError(CanvasAPIError):
    """Content not found (deleted)."""
    pass


class CanvasClient:
    """Canvas LMS API client with pagination, rate limiting, and error handling."""

    def __init__(self, api_token: str, base_url: str):
        """
        Initialize Canvas API client.

        Args:
            api_token: Canvas API access token
            base_url: Canvas instance base URL (e.g., https://canvas.txstate.edu)
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'application/json+canvas-string-ids'
        })

    def _make_request(self, endpoint: str, params: Dict = None) -> requests.Response:
        """
        Make HTTP request with error handling and retries.

        Args:
            endpoint: API endpoint (e.g., '/courses/12345/modules')
            params: Query parameters

        Returns:
            Response object

        Raises:
            CanvasAPIError: On API errors
        """
        url = f"{self.api_base}{endpoint}"
        params = params or {}

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    # Check rate limit 
                    remaining_str = response.headers.get('X-Rate-Limit-Remaining', '999')
                    remaining = int(float(remaining_str))
                    if remaining < INGEST_RATE_LIMIT_THRESHOLD:
                        logger.warning(f"Rate limit warning: {remaining} requests remaining")
                        time.sleep(2)  # Slow down

                    return response

                elif response.status_code == 403:
                    # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                elif response.status_code == 404:
                    raise NotFoundError(f"Content not found: {endpoint}")

                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API token")

                elif response.status_code >= 500:
                    # Server error, retry
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAYS[attempt]
                        logger.warning(f"Server error. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise CanvasAPIError(f"Server error: {response.status_code}")

                else:
                    raise CanvasAPIError(f"Unexpected status code: {response.status_code}")

            except requests.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    raise CanvasAPIError(f"Request failed: {e}")
                time.sleep(RETRY_DELAYS[attempt])

        raise CanvasAPIError(f"Max retries exceeded for {endpoint}")

    def _handle_pagination(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Handle paginated API responses.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            List of all items across all pages
        """
        all_items = []
        params = params or {}
        params['per_page'] = 100  # Max items per page

        while True:
            response = self._make_request(endpoint, params)
            items = response.json()

            if isinstance(items, list):
                all_items.extend(items)
            else:
                # Single item response
                all_items.append(items)
                break

            # Check for next page
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

            # Extract next page URL
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    # Parse URL from <URL>; rel="next"
                    next_url = link.split(';')[0].strip('<> ')
                    # Make next request (full URL already includes params)
                    endpoint = next_url.replace(self.api_base, '')
                    params = {}  # URL already has params
                    break

        return all_items

    def get_course(self, course_id: str) -> Dict:
        """
        Get course information.

        Args:
            course_id: Canvas course ID

        Returns:
            Course information dict
        """
        endpoint = f"/courses/{course_id}"
        response = self._make_request(endpoint)
        return response.json()

    def get_modules(self, course_id: str) -> List[Dict]:
        """
        Get all modules for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            List of module dicts
        """
        endpoint = f"/courses/{course_id}/modules"
        return self._handle_pagination(endpoint)

    def get_module_items(self, course_id: str, module_id: str) -> List[Dict]:
        """
        Get all items in a module.

        Args:
            course_id: Canvas course ID
            module_id: Module ID

        Returns:
            List of module item dicts
        """
        endpoint = f"/courses/{course_id}/modules/{module_id}/items"
        return self._handle_pagination(endpoint)

    def get_pages(self, course_id: str) -> List[Dict]:
        """
        Get all pages for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            List of page dicts (metadata only)
        """
        endpoint = f"/courses/{course_id}/pages"
        return self._handle_pagination(endpoint)

    def get_page_content(self, course_id: str, page_url: str) -> Dict:
        """
        Get full content of a specific page.

        Args:
            course_id: Canvas course ID
            page_url: Page URL slug

        Returns:
            Page dict with full body content
        """
        endpoint = f"/courses/{course_id}/pages/{page_url}"
        response = self._make_request(endpoint)
        return response.json()

    def get_assignments(self, course_id: str) -> List[Dict]:
        """
        Get all assignments for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            List of assignment dicts with rubric info
        """
        endpoint = f"/courses/{course_id}/assignments"
        params = {'include[]': 'rubric'}
        return self._handle_pagination(endpoint, params)

    def get_announcements(self, course_id: str) -> List[Dict]:
        """
        Get all announcements for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            List of announcement dicts
        """
        endpoint = f"/courses/{course_id}/discussion_topics"
        params = {'only_announcements': 'true'}
        return self._handle_pagination(endpoint, params)

    def get_discussions(self, course_id: str) -> List[Dict]:
        """
        Get all discussion topics for a course (excluding announcements).

        Args:
            course_id: Canvas course ID

        Returns:
            List of discussion topic dicts
        """
        endpoint = f"/courses/{course_id}/discussion_topics"
        return self._handle_pagination(endpoint)

    def get_discussion_entries(self, course_id: str, topic_id: str) -> List[Dict]:
        """
        Get all entries (posts) for a discussion topic.

        Args:
            course_id: Canvas course ID
            topic_id: Discussion topic ID

        Returns:
            List of discussion entry dicts
        """
        endpoint = f"/courses/{course_id}/discussion_topics/{topic_id}/entries"
        return self._handle_pagination(endpoint)

    def get_files(self, course_id: str) -> List[Dict]:
        """
        Get all files for a course.

        Args:
            course_id: Canvas course ID

        Returns:
            List of file metadata dicts
        """
        endpoint = f"/courses/{course_id}/files"
        return self._handle_pagination(endpoint)

    def get_file(self, file_id: str) -> bytes:
        """
        Download file content.

        Args:
            file_id: Canvas file ID

        Returns:
            File content as bytes
        """
        # First get file metadata to get download URL
        endpoint = f"/files/{file_id}"
        response = self._make_request(endpoint)
        file_data = response.json()

        # Download from the URL
        download_url = file_data.get('url')
        if not download_url:
            raise CanvasAPIError(f"No download URL for file {file_id}")

        # Download with timeout
        download_response = requests.get(download_url, timeout=60)
        download_response.raise_for_status()

        return download_response.content

    def get_file_metadata(self, file_id: str) -> Dict:
        """
        Get file metadata without downloading.

        Args:
            file_id: Canvas file ID

        Returns:
            File metadata dict
        """
        endpoint = f"/files/{file_id}"
        response = self._make_request(endpoint)
        return response.json()
