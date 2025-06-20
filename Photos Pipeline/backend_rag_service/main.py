# --- Step 1: Clean FastAPI Backend (no LLM) ---

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import weaviate
from openai import AzureOpenAI

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

if not all([WEAVIATE_URL, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME]):
    raise ValueError("Missing one or more required environment variables.")

app = FastAPI(title="Image RAG Backend", description="Search image metadata using semantic similarity.")

# Weaviate v3 client setup
try:
    weaviate_client = weaviate.Client(WEAVIATE_URL)
    print(f"Connected to Weaviate at {WEAVIATE_URL}")
except Exception as e:
    print(f"Failed to connect to Weaviate: {e}")
    weaviate_client = None

# Azure OpenAI Client
azure_openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

class QueryInput(BaseModel):
    query: str

@app.post("/query")
async def process_query(input: QueryInput):
    user_query = input.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        embedding_response = azure_openai_client.embeddings.create(
            input=user_query,
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        )
        query_embedding = embedding_response.data[0].embedding

        result = weaviate_client.query.get(
            "SecurePhotos",
            ["image_path", "summary", "google_metadata"]
        ).with_near_vector({"vector": query_embedding}).with_limit(5).do()

        objects = result.get("data", {}).get("Get", {}).get("SecurePhotos", [])

        image_results = []
        for obj in objects:
            summary = obj.get("summary")
            metadata_raw = obj.get("google_metadata")
            image_url = None
            if metadata_raw:
                try:
                    metadata_dict = json.loads(metadata_raw)
                    image_url = metadata_dict.get("url")
                except:
                    continue
            if image_url and summary:
                image_results.append({"image_url": image_url, "summary": summary})

        return {
            "query": user_query,
            "image_results": image_results,
            "message": "Top-k matched images retrieved successfully."
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")