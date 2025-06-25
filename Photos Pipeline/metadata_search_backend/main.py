from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from metadata_extractor import extract_fields_from_query
from qdrant_search import search_by_metadata
from models import MetadataFields, SearchResponse, ImageResult

load_dotenv()

app = FastAPI(title="SecurePhotos Metadata Search API")

class QueryInput(BaseModel):
    query: str

@app.post("/metadata-query", response_model=SearchResponse)
async def metadata_search(input: QueryInput):
    user_query = input.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        extracted_dict = await extract_fields_from_query(user_query)
        metadata = MetadataFields(**extracted_dict)

        if not any(metadata.dict().values()):
            return SearchResponse(query=user_query, matched_images=[])

        results = search_by_metadata(metadata, limit=5)
        return SearchResponse(query=user_query, matched_images=results)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
