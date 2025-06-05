import requests
import csv
import json
from io import StringIO

def main(csv_url: str) -> dict:
    """
    Fetches a CSV from a URL, processes it, calculates sums,
    and returns a structured JSON string within a dictionary for the LLM.
    """
    if "remote_url" in csv_url or "upload.dify.ai" not in csv_url:
        return {"llm_input_json": json.dumps({"status": "error", "message": "Invalid CSV URL provided."})}

    try:
        response = requests.get(csv_url, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        return {"llm_input_json": json.dumps({"status": "error", "message": f"Failed to fetch CSV: {e}", "type": "fetch_error"})}

    records = []
    has_parsing_errors = False

    try:
        csv_text = response.text
        # Ensure the CSV content is valid UTF-8, handle potential BOM
        if csv_text.startswith('\ufeff'): # Handle UTF-8 BOM
            csv_text = csv_text[1:]
            
        reader = csv.DictReader(StringIO(csv_text))
        
        # Check if expected headers are present
        expected_headers = ['id', 'value1', 'value2']
        if not all(header in reader.fieldnames for header in expected_headers):
            return {"llm_input_json": json.dumps({"status": "error", "message": f"Missing required CSV headers. Expected: {expected_headers}, Found: {reader.fieldnames}", "type": "header_error"})}

        for row_num, row in enumerate(reader, start=1):
            try:
                record = {
                    "id": int(row["id"]),
                    "value1": int(row["value1"]),
                    "value2": int(row["value2"]),
                    "sum": int(row["value1"]) + int(row["value2"])
                }
                records.append(record)
            except ValueError as e:
                has_parsing_errors = True
                records.append({
                    "status": "error",
                    "message": f"Data conversion error in row {row_num}: {e}",
                    "original_row": row,
                    "type": "row_parse_error"
                })
            except KeyError as e:
                has_parsing_errors = True
                records.append({
                    "status": "error",
                    "message": f"Missing column in row {row_num}: {e}",
                    "original_row": row,
                    "type": "missing_column_error"
                })
            except Exception as e:
                has_parsing_errors = True
                records.append({
                    "status": "error",
                    "message": f"Unexpected error in row {row_num}: {e}",
                    "original_row": row,
                    "type": "unexpected_row_error"
                })

        if has_parsing_errors:
            return {"llm_input_json": json.dumps({
                "status": "partial_success_with_errors",
                "message": "Some rows failed to parse. Check individual records for errors.",
                "records": records # Include all records, even the error ones
            })}
        else:
            return {"llm_input_json": json.dumps({"status": "success", "records": records})}

    except Exception as e:
        return {"llm_input_json": json.dumps({"status": "error", "message": f"CSV processing failed unexpectedly: {e}", "type": "global_processing_error"})}