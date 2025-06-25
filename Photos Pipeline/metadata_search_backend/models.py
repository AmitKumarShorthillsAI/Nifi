from pydantic import BaseModel, Field
from typing import Optional, List

class MetadataFields(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    person: Optional[str] = None  # Will match against 'persons' list in Qdrant
    deviceType: Optional[str] = None
    appName: Optional[str] = None
    localFolderName: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None

    timestamp: Optional[int] = None
    timestamp_before: Optional[int] = None
    timestamp_after: Optional[int] = None

class ImageResult(BaseModel):
    image_url: str
    summary: str

class QueryRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    query: str
    matched_images: List[ImageResult] = Field(..., example=[
        {
            "image_url": "https://photos.google.com/photo/abc123",
            "summary": "A lion roaring in the wild"
        }
    ])
