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
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

if not all([WEAVIATE_URL, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT,
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME]):
    raise ValueError("Missing one or more required environment variables.")

app = FastAPI(
    title="Image RAG Backend Service",
    description="Backend service for semantic image search and LLM response generation."
)

# --- Weaviate Client Setup (v3) ---
try:
    weaviate_client = weaviate.Client(WEAVIATE_URL)
    print(f"Connected to Weaviate at {WEAVIATE_URL}")
except Exception as e:
    print(f"Failed to connect to Weaviate: {e}")
    weaviate_client = None

# --- Azure OpenAI Setup ---
azure_openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)
print("Azure OpenAI clients initialized.")

class QueryInput(BaseModel):
    query: str

@app.post("/query")
async def process_query(input: QueryInput):
    user_query = input.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # 1. Embed the query
        embedding_response = azure_openai_client.embeddings.create(
            input=user_query,
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        )
        query_embedding = embedding_response.data[0].embedding
        print(f"Generated embedding for query '{user_query}'")

        # 2. Weaviate query using v3 client
        result = weaviate_client.query.get(
            "SecurePhotos",
            ["image_path", "summary", "google_metadata"]
        ).with_near_vector({
            "vector": query_embedding
        }).with_limit(5).do()

        objects = result.get("data", {}).get("Get", {}).get("SecurePhotos", [])
        print(f"Retrieved {len(objects)} objects from Weaviate")

        retrieved_contexts = []
        image_results = []

        for i, obj in enumerate(objects):
            summary = obj.get("summary")
            google_metadata_raw = obj.get("google_metadata")

            image_url = None
            if google_metadata_raw:
                try:
                    metadata_dict = json.loads(google_metadata_raw)
                    image_url = metadata_dict.get("url")
                except Exception as e:
                    print(f"Could not parse google_metadata: {e}")

            if image_url and summary:
                image_results.append({
                    "image_url": image_url,
                    "summary": summary
                })
                retrieved_contexts.append(f"Image {i+1} (URL: {image_url}) summary: {summary}")

        # 3. LLM Answer
        llm_answer = "No relevant information found."
        if retrieved_contexts:
            context_string = "\n".join(retrieved_contexts)
            prompt = (
                f"Based on the following image summaries and their associated URLs, answer the user's question. "
                f"User Question: {user_query}\n\n"
                f"Image Summaries with URLs:\n{context_string}\n\n"
                f"Answer:"
            )
            chat_completion = azure_openai_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions about images based on provided image summaries and their URLs."},
                    {"role": "user", "content": prompt}
                ],
                model=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                temperature=0.7,
                max_tokens=500
            )
            llm_answer = chat_completion.choices[0].message.content

        return {
            "query": user_query,
            "llm_answer": llm_answer,
            "image_results": image_results,
            "message": "Query processed successfully."
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/health")
async def health_check():
    weaviate_ok = openai_ok = False
    try:
        if weaviate_client.schema.get("SecurePhotos"):
            weaviate_ok = True
    except Exception:
        pass
    try:
        azure_openai_client.embeddings.create(
            input="test",
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
        )
        openai_ok = True
    except Exception:
        pass

    if weaviate_ok and openai_ok:
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=503, detail={
            "weaviate": "connected" if weaviate_ok else "disconnected",
            "azure_openai": "connected" if openai_ok else "disconnected"
        })
