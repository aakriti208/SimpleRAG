#!/usr/bin/env python3
"""
Verify Canvas Data in ChromaDB

Shows what Canvas content has been ingested and provides statistics.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vectorstore.chroma_manager import ChromaManager
from src.ingestion.metadata_tracker import MetadataTracker
from collections import Counter


def main():
    print("="*80)
    print("CANVAS DATA VERIFICATION")
    print("="*80)

    # Initialize
    chroma = ChromaManager()
    tracker = MetadataTracker()

    # Get stats
    chroma_stats = chroma.get_collection_stats()
    tracker_stats = tracker.get_stats()

    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total documents in ChromaDB: {chroma_stats['count']}")
    print(f"  Total content items tracked: {tracker_stats['total_items']}")
    print(f"  Active items: {tracker_stats['active_items']}")
    print(f"  Deleted items: {tracker_stats['deleted_items']}")

    # Get all documents
    print(f"\n🔍 Querying all documents...")
    all_docs = chroma.collection.get()

    # Analyze by source
    sources = Counter()
    content_types = Counter()
    courses = Counter()

    for metadata in all_docs['metadatas']:
        sources[metadata.get('source', 'Unknown')] += 1
        content_types[metadata.get('content_type', 'unknown')] += 1
        course = metadata.get('course_name', 'N/A')
        if course != 'N/A':
            courses[course] += 1

    print(f"\n📚 BY SOURCE:")
    for source, count in sources.most_common():
        print(f"  {source}: {count} documents")

    print(f"\n📝 BY CONTENT TYPE:")
    for ctype, count in content_types.most_common():
        print(f"  {ctype}: {count} documents")

    if courses:
        print(f"\n🎓 BY COURSE:")
        for course, count in courses.most_common():
            print(f"  {course}: {count} documents")

    # Show sample Canvas content
    print(f"\n📄 SAMPLE CANVAS CONTENT:")
    print("="*80)

    canvas_docs = [(doc, meta) for doc, meta in zip(all_docs['documents'], all_docs['metadatas'])
                   if meta.get('source') == 'Canvas LMS']

    if canvas_docs:
        for i, (doc, meta) in enumerate(canvas_docs[:5], 1):
            print(f"\n[{i}] {meta.get('title', 'Untitled')}")
            print(f"    Type: {meta.get('content_type', 'unknown')}")
            print(f"    Course: {meta.get('course_name', 'N/A')}")
            print(f"    Content preview: {doc[:150]}...")
    else:
        print("  ⚠️  No Canvas content found!")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if chroma_stats['count'] < 20:
        print("  ⚠️  You have very few documents. Consider:")
        print("     - Run full ingestion: python scripts/ingest_data.py --full")
        print("     - This will fetch ALL content types (modules, assignments, etc.)")

    if 'Canvas LMS' not in sources:
        print("  ⚠️  No Canvas content detected! Run:")
        print("     python scripts/ingest_data.py --full")
    elif sources['Canvas LMS'] < 10:
        print("  ⚠️  Limited Canvas content. You may want to:")
        print("     - Ingest more content types beyond just pages")
        print("     - Check if your courses have more content available")

    if len(content_types) == 1 and 'page' in content_types:
        print("  ℹ️  You only have pages. To get complete course data:")
        print("     python scripts/ingest_data.py --full")
        print("     This will fetch: modules, assignments, announcements, discussions, files")

    print("\n" + "="*80)
    print("✓ Verification complete!")
    print("="*80)


if __name__ == "__main__":
    main()
