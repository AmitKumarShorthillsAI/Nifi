# update_indexes_qdrant.py
from qdrant_client import QdrantClient, models
from urllib.parse import urlparse
import os

# --- Setup ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "secure_photos")

parsed = urlparse(QDRANT_HOST)
client = QdrantClient(host=parsed.hostname or "localhost", port=parsed.port or 6333)

# --- Fields to update ---
fields_to_update = [
    "title",
    "deviceType",
    "appName",
    "localFolderName",
    "image_path",
]

def recreate_index(field_name: str):
    try:
        print(f"🚫 Deleting existing index for field: {field_name}")
        client.delete_payload_index(collection_name=COLLECTION_NAME, field_name=field_name, wait=True)
    except Exception as e:
        print(f"⚠️ Couldn't delete index for {field_name}: {e}")

    try:
        print(f"🛠️ Creating text index for field: {field_name}")
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=models.TextIndexParams(
                type="text",
                tokenizer=models.TokenizerType.WORD,
                min_token_len=2,
                lowercase=True
            ),
            wait=True
        )
        print(f"✅ Updated index for: {field_name}")
    except Exception as e:
        print(f"❌ Failed to create text index for {field_name}: {e}")

if __name__ == "__main__":
    for field in fields_to_update:
        recreate_index(field)
