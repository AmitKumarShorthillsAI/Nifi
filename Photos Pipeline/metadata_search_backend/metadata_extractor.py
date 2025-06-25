import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
import re

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# This function will be imported in `main.py`
async def extract_fields_from_query(query: str) -> dict:
    metadata_fields = {
        "title": "title of the image file",
        "description": "description of the image",
        "imageViews": "number of times image was viewed",
        "timestamp": "UNIX timestamp when the photo was taken",
        "formatted_time": "formatted human-readable date-time",
        "latitude": "latitude where the photo was taken",
        "longitude": "longitude where the photo was taken",
        "altitude": "altitude where the photo was taken",
        "appName": "application used to upload the photo",
        "deviceType": "type of device (e.g., ANDROID_PHONE, IPHONE)",
        "localFolderName": "folder name on device where photo was stored",
        "persons": "full name of a person recognized in the image (e.g., 'john doe')",
    }

    prompt = (
        f"You are an assistant that extracts structured metadata filters from a user query "
        f"about photos. Return only a JSON object with keys from this schema if present:\n"
        f"{json.dumps(metadata_fields, indent=2)}\n\n"
        f"User Query: {query}\n\n"
        f"Only return valid JSON. Do not include markdown formatting or explanations."
    )

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You extract metadata filters from user queries about photos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=500
    )

    content = response.choices[0].message.content.strip()
    print("🔍 Raw LLM output:\n", content)

    # --- New: Clean up markdown wrapping ---
    if content.startswith("```json") or content.startswith("```"):
        content = re.sub(r"^```[a-z]*\n", "", content.strip())  # remove starting ```json
        content = re.sub(r"\n```$", "", content.strip())         # remove ending ```
        print("🧹 Cleaned content:\n", content)

    try:
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        raise ValueError(f"LLM did not return valid JSON. Cleaned content:\n{content}")