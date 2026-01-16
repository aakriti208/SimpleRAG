#!/usr/bin/env python3
"""
List Available Canvas Courses

Shows all courses you have access to with their IDs.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.canvas_client import CanvasClient
from src.config import CANVAS_API_TOKEN, CANVAS_BASE_URL


def main():
    print("="*80)
    print("AVAILABLE CANVAS COURSES")
    print("="*80)

    try:
        client = CanvasClient(CANVAS_API_TOKEN, CANVAS_BASE_URL)

        # Get all courses
        print("\nFetching your courses...\n")
        response = client.session.get(
            f"{client.base_url}/api/v1/courses",
            params={
                "enrollment_state": "active",
                "per_page": 100
            }
        )
        response.raise_for_status()
        courses = response.json()

        if not courses:
            print("No courses found!")
            return

        print(f"Found {len(courses)} courses:\n")
        print(f"{'ID':<15} {'Course Name':<60} {'Code':<20}")
        print("-" * 95)

        for course in courses:
            course_id = course.get('id', 'N/A')
            course_name = course.get('name', 'Unknown')
            course_code = course.get('course_code', 'N/A')

            # Truncate long names
            if len(course_name) > 57:
                course_name = course_name[:54] + "..."

            print(f"{course_id:<15} {course_name:<60} {course_code:<20}")

        print("\n" + "="*80)
        print("To add a course to your knowledge base:")
        print("1. Copy the Course ID from above")
        print("2. Add to .env file: CANVAS_COURSE_IDS=id1,id2,NEW_ID")
        print("3. Run: python scripts/ingest_data.py --course NEW_ID --full")
        print("="*80)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
