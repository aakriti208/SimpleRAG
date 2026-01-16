#!/usr/bin/env python3
"""
Canvas Data Ingestion Script

Main orchestration script for ingesting Canvas LMS content into the RAG pipeline.

Usage:
    python scripts/ingest_data.py --full              # Full sync
    python scripts/ingest_data.py --incremental       # Only new/updated (default)
    python scripts/ingest_data.py --course 2295372    # Single course
    python scripts/ingest_data.py --content-type page # Specific type
    python scripts/ingest_data.py --reset             # Clear ChromaDB first
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.canvas_client import CanvasClient
from src.ingestion.document_processor import DocumentProcessor
from src.ingestion.metadata_tracker import MetadataTracker
from src.ingestion.content_handlers import (
    PageHandler,
    ModuleHandler,
    AssignmentHandler,
    AnnouncementHandler,
    DiscussionHandler,
    FileHandler
)
from src.vectorstore.chroma_manager import ChromaManager
from src.config import (
    CANVAS_API_TOKEN,
    CANVAS_BASE_URL,
    CANVAS_COURSE_IDS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    LOG_DIR,
    LOG_LEVEL
)

# Setup logging
def setup_logging():
    """Configure logging for ingestion pipeline."""
    from datetime import datetime

    log_file = LOG_DIR / f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging to {log_file}")


logger = logging.getLogger(__name__)


class CanvasIngestionPipeline:
    """Orchestrates Canvas data ingestion into ChromaDB."""

    def __init__(self, incremental=True):
        """
        Initialize ingestion pipeline.

        Args:
            incremental: If True, only process new/updated content
        """
        
        logger.info("Initializing Canvas ingestion pipeline...")

        self.client = CanvasClient(CANVAS_API_TOKEN, CANVAS_BASE_URL)
        self.processor = DocumentProcessor(CHUNK_SIZE, CHUNK_OVERLAP)
        self.tracker = MetadataTracker()
        self.chroma = ChromaManager()

        # Initialize handlers
        self.handlers = {
            'page': PageHandler(self.client, self.processor),
            'module': ModuleHandler(self.client, self.processor),
            'assignment': AssignmentHandler(self.client, self.processor),
            'announcement': AnnouncementHandler(self.client, self.processor),
            'discussion': DiscussionHandler(self.client, self.processor),
            'file': FileHandler(self.client, self.processor),
        }

        self.incremental = incremental
        logger.info(f"Pipeline initialized (incremental={incremental})")

    def ingest_course(self, course_id: str, content_types: list = None):
        """
        Ingest content from a single course.

        Args:
            course_id: Canvas course ID
            content_types: List of content types to ingest (default: all)

        Returns:
            Stats dict with counts per content type
        """
        logger.info("="*70)
        logger.info(f"Ingesting course: {course_id}")
        logger.info("="*70)

        # Get course info
        try:
            course_info = self.client.get_course(course_id)
            course_name = course_info.get('name', 'Unknown Course')
            logger.info(f"Course name: {course_name}")
        except Exception as e:
            logger.error(f"Error fetching course info: {e}")
            course_name = f"Course {course_id}"

        # Determine which handlers to run
        handlers_to_run = content_types or list(self.handlers.keys())
        logger.info(f"Processing content types: {', '.join(handlers_to_run)}")

        all_chunks = []
        stats = {handler: 0 for handler in handlers_to_run}

        for handler_name in handlers_to_run:
            if handler_name not in self.handlers:
                logger.warning(f"Unknown handler: {handler_name}")
                continue

            logger.info(f"\nProcessing {handler_name}s...")
            handler = self.handlers[handler_name]

            try:
                chunks = handler.process_content(course_id, course_name)

                # Filter for incremental updates
                if self.incremental:
                    chunks = self._filter_incremental(chunks)
                    logger.info(f"After incremental filter: {len(chunks)} chunks")

                all_chunks.extend(chunks)
                stats[handler_name] = len(chunks)

            except Exception as e:
                logger.error(f"Error processing {handler_name}s: {e}", exc_info=True)
                continue

        # Add to ChromaDB with custom IDs
        if all_chunks:
            logger.info(f"\nAdding {len(all_chunks)} total chunks to ChromaDB...")

            # Generate custom IDs for each chunk
            chunk_ids = [
                f"{chunk['metadata']['content_id']}_chunk_{chunk['metadata']['chunk_index']}"
                for chunk in all_chunks
            ]

            self.chroma.add_documents_with_ids(all_chunks, chunk_ids)
            self.tracker.update_course_sync(course_id)
        else:
            logger.info("No new content to add")

        logger.info("\n" + "="*70)
        logger.info(f"Course {course_id} ingestion complete!")
        logger.info(f"Total chunks: {len(all_chunks)}")
        for handler, count in stats.items():
            logger.info(f"  - {handler}: {count}")
        logger.info("="*70)

        return stats

    def _filter_incremental(self, chunks: list) -> list:
        """
        Filter chunks for incremental update.

        Args:
            chunks: List of all chunks

        Returns:
            Filtered list of chunks that need processing
        """
        if not chunks:
            return []

        filtered = []
        processed_ids = set()  # Track which content IDs we've marked as processed

        for chunk in chunks:
            content_id = chunk['metadata']['content_id']
            updated_at = chunk['metadata'].get('updated_at', '')

            if self.tracker.should_process_item(content_id, updated_at):
                filtered.append(chunk)

                # Mark as processed (only once per content item)
                if content_id not in processed_ids:
                    self.tracker.mark_item_processed(
                        content_id,
                        chunk['metadata']['content_type'],
                        updated_at,
                        chunk['metadata']['total_chunks']
                    )
                    processed_ids.add(content_id)

        return filtered

    def ingest_all_courses(self, content_types: list = None):
        """
        Ingest all configured courses.

        Args:
            content_types: List of content types to ingest (default: all)

        Returns:
            Overall stats dict
        """
        overall_stats = {}

        for course_id in CANVAS_COURSE_IDS:
            if not course_id or not course_id.strip():
                continue

            try:
                stats = self.ingest_course(course_id, content_types)
                overall_stats[course_id] = stats
            except Exception as e:
                logger.error(f"Error ingesting course {course_id}: {e}", exc_info=True)
                continue

        return overall_stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ingest Canvas LMS data into RAG pipeline')
    parser.add_argument('--full', action='store_true',
                       help='Full sync (re-process everything)')
    parser.add_argument('--incremental', action='store_true', default=True,
                       help='Incremental sync (only new/updated, default)')
    parser.add_argument('--course', type=str,
                       help='Specific course ID to ingest')
    parser.add_argument('--content-type', type=str, nargs='+',
                       help='Specific content types to ingest (e.g., page assignment)')
    parser.add_argument('--reset', action='store_true',
                       help='Reset ChromaDB before ingestion')

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    logger.info("="*70)
    logger.info("CANVAS DATA INGESTION")
    logger.info("="*70)
    logger.info(f"Canvas Base URL: {CANVAS_BASE_URL}")
    logger.info(f"Configured Courses: {', '.join(CANVAS_COURSE_IDS)}")
    logger.info(f"Mode: {'Full' if args.full else 'Incremental'}")
    logger.info("="*70)

    # Initialize pipeline
    pipeline = CanvasIngestionPipeline(incremental=not args.full)

    # Reset if requested
    if args.reset:
        logger.warning("Resetting ChromaDB collection...")
        pipeline.chroma.reset_collection()
        pipeline.tracker.reset()
        logger.info("Reset complete")

    # Run ingestion
    try:
        if args.course:
            logger.info(f"Ingesting single course: {args.course}")
            pipeline.ingest_course(args.course, args.content_type)
        else:
            logger.info("Ingesting all configured courses")
            pipeline.ingest_all_courses(args.content_type)

        # Show final stats
        tracker_stats = pipeline.tracker.get_stats()
        chroma_stats = pipeline.chroma.get_collection_stats()

        logger.info("\n" + "="*70)
        logger.info("INGESTION COMPLETE")
        logger.info("="*70)
        logger.info(f"Total documents in ChromaDB: {chroma_stats['count']}")
        logger.info(f"Total content items tracked: {tracker_stats['total_items']}")
        logger.info(f"Active items: {tracker_stats['active_items']}")
        logger.info(f"Last full sync: {tracker_stats['last_full_sync'] or 'Never'}")
        logger.info("\nBy content type:")
        for content_type, count in tracker_stats.get('by_type', {}).items():
            logger.info(f"  - {content_type}: {count}")
        logger.info("="*70)

    except KeyboardInterrupt:
        logger.info("\n\nIngestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nFatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
