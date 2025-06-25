from urllib.parse import urlparse
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, Range
from typing import List
from models import MetadataFields
import os

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "secure_photos")

# ✅ Parse host and port correctly
parsed = urlparse(QDRANT_HOST)
host = parsed.hostname or "localhost"
port = parsed.port or 6333

# ✅ Initialize client safely
qdrant = QdrantClient(host=host, port=port)

def build_filter_from_metadata(metadata: MetadataFields) -> Filter:
    must_conditions = []

    # Match fields
    for field in ["title", "description", "deviceType", "appName", "localFolderName"]:
        value = getattr(metadata, field)
        if value:
            must_conditions.append(
                FieldCondition(key=field, match=MatchValue(value=value))
            )

    # Person (matched against "persons" list)
    if metadata.person:
        must_conditions.append(
            FieldCondition(key="persons", match=MatchValue(value=metadata.person.lower()))
        )

    # Geo fields
    for field in ["latitude", "longitude", "altitude"]:
        value = getattr(metadata, field)
        if value is not None:
            must_conditions.append(
                FieldCondition(key=field, match=MatchValue(value=value))
            )

    # Timestamp
    if metadata.timestamp:
        must_conditions.append(FieldCondition(
            key="timestamp", match=MatchValue(value=metadata.timestamp)
        ))
    elif metadata.timestamp_before or metadata.timestamp_after:
        time_range = {}
        if metadata.timestamp_after:
            time_range["gte"] = metadata.timestamp_after
        if metadata.timestamp_before:
            time_range["lte"] = metadata.timestamp_before
        must_conditions.append(FieldCondition(key="timestamp", range=Range(**time_range)))

    if not must_conditions:
        raise ValueError("No valid metadata fields to filter.")

    return Filter(must=must_conditions)

def search_by_metadata(metadata: MetadataFields, limit: int = 5) -> List[dict]:
    try:
        filters = build_filter_from_metadata(metadata)

        results, _ = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=filters,
            limit=limit,
            with_payload=True
        )

        matched = []
        for point in results:
            payload = point.payload
            if payload.get("url") and payload.get("summary"):
                matched.append({
                    "image_url": payload["url"],
                    "summary": payload["summary"]
                })

        return matched

    except Exception as e:
        print(f"❌ Error during metadata search: {e}")
        return []
