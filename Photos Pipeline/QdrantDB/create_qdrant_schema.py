import requests
import json
import time

QDRANT_HOST = "http://localhost:6333"
COLLECTION_NAME = "secure_photos"

# Step 1: Delete existing collection
delete_url = f"{QDRANT_HOST}/collections/{COLLECTION_NAME}"
del_resp = requests.delete(delete_url)
if del_resp.ok:
    print(f"🗑️ Deleted existing collection '{COLLECTION_NAME}'.")
else:
    print(f"⚠️ Could not delete collection (maybe doesn't exist): {del_resp.text}")

# Step 2: Create new collection with named vector
create_url = f"{QDRANT_HOST}/collections/{COLLECTION_NAME}"
create_payload = {
    "vectors": {
        "summary_embedding": {
            "size": 1536,
            "distance": "Cosine"
        }
    }
}

create_resp = requests.put(create_url, json=create_payload)
if create_resp.ok:
    print(f"✅ Created collection '{COLLECTION_NAME}'.")
    time.sleep(1)  # Let Qdrant stabilize
else:
    print(f"❌ Failed to create collection: {create_resp.text}")
    exit(1)

# Step 3: Index metadata fields for filtering and querying
fields_to_index = {
    "image_path": "keyword", # "text" is analyzed for full-text search, allowing for tokenization and stemming, while "keyword" is used for exact matches without analysis.
    "summary": "text",
    "title": "keyword",
    "description": "text",
    "imageViews": "keyword",
    "timestamp": "integer",
    "formatted_time": "text",
    "url": "keyword",
    "latitude": "float",
    "longitude": "float",
    "altitude": "float",
    "appName": "keyword",
    "deviceType": "keyword",
    "localFolderName": "keyword",
    "persons": "text"
}

index_url = f"{QDRANT_HOST}/collections/{COLLECTION_NAME}/index"

for field, field_type in fields_to_index.items():
    index_payload = {
        "field_name": field,
        "field_schema": field_type
    }
    index_resp = requests.put(index_url, json=index_payload)
    if index_resp.ok:
        print(f"✅ Indexed field '{field}' as '{field_type}'")
    else:
        print(f"❌ Failed to index field '{field}': {index_resp.status_code} - {index_resp.text}")
