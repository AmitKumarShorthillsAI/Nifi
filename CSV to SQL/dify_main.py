from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import mysql.connector
from dotenv import load_dotenv
import os
import logging

# Load .env variables
load_dotenv()

app = FastAPI()

# Read DB config from .env
db_config = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DB"),
    "port": int(os.getenv("MYSQL_PORT", 3306))  # Default MySQL port is 3306
}

# Define input schema
class Record(BaseModel):
    id: int
    value1: int
    value2: int
    sum: int

class Payload(BaseModel):
    result: List[Record]

# @app.post("/upload")
# async def upload_data(request: Request):
#     try:
#         raw_body = await request.body()
#         text_body = raw_body.decode('utf-8', errors='replace')
#         logging.info(f"Raw request body:\n{text_body}")
        
#         data = await request.json()
#         logging.info(f"Parsed JSON data: {data}")
        
#         return {"received": data}
#     except Exception as e:
#         logging.error(f"JSON decode error: {str(e)}\nRaw body:\n{text_body}")
#         return {"error is": str(e)}



@app.post("/upload")
async def upload_data(records: List[Record]):
    # records = payload.result
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for row in records:
            cursor.execute("""
                INSERT INTO processed_data_dify (id, value1, value2, sum)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    value1 = VALUES(value1),
                    value2 = VALUES(value2),
                    sum = VALUES(sum)
            """, (row.id, row.value1, row.value2, row.sum))

        conn.commit()
        return {"status": "success", "inserted": len(records)}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
