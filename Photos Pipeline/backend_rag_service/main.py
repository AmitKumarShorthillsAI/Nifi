from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import numpy as np # Only used for np.isfinite in debug, can remove if debug is gone

# Qdrant Client imports
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams

from openai import AzureOpenAI

load_dotenv()

# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
COLLECTION_NAME = "secure_photos"

# Validate essential environment variables
if not all([QDRANT_HOST, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME]):
    raise ValueError("Missing one or more required environment variables (QDRANT_HOST, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME).")

# --- FastAPI App Initialization ---
app = FastAPI(title="Image Search Backend (Qdrant)", description="Search image metadata via semantic similarity using Qdrant.")

# --- Azure OpenAI Embedding Client Initialization ---
azure_openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-12-01-preview", # Check if this API version is still current
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# --- Qdrant Client Initialization ---
# Initializing Qdrant Client globally for reuse across requests.
# For production async FastAPI, consider using `qdrant_client.AsyncQdrantClient`
# and managing its lifecycle (e.g., in app startup/shutdown events).
qdrant_client_lib = QdrantClient(host="localhost", port=6333)

# --- Pydantic Models ---
class QueryInput(BaseModel):
    query: str

# --- API Endpoints ---
@app.post("/query")
async def process_query(input: QueryInput):
    user_query = input.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # 1. Get embedding for the user query
        embedding_response = azure_openai_client.embeddings.create(
            input=user_query,
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        )
        # Convert embedding to a list of native Python floats
        query_embedding = [float(x) for x in embedding_response.data[0].embedding]

        # 2. Perform semantic search in Qdrant
        search_result = qdrant_client_lib.search(
            collection_name=COLLECTION_NAME,
            # Use dictionary format for named vector search as found to be working with 1.14.3
            query_vector={"name": "summary_embedding", "vector": query_embedding},
            limit=5, # Retrieve top 5 results
            with_payload=True, # Include payload in results
        )

        # 3. Process search results
        image_results = []
        for point in search_result: # Iterate directly over the list of points returned by search_result
            # Points are Pydantic models; use .payload to access attributes
            payload = point.payload
            # Ensure payload and its attributes exist before accessing
            if payload:
                summary = payload.get("summary")
                image_url = payload.get("url")
                if summary and image_url:
                    image_results.append({"image_url": image_url, "summary": summary})

        return {
            "query": user_query,
            "image_results": image_results,
            "message": "Top-k matched images retrieved successfully."
        }

    except Exception as e:
        # Log the full traceback for debugging purposes
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")