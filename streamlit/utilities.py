import json
import requests
import logging
import re
import os
from logging.config import dictConfig
from logging_file import LOGGING
from dotenv import load_dotenv

load_dotenv()
email = os.getenv("EMAIL")
user_name = email.split("@")[0]
token = os.getenv("JIRA_API_TOKEN")
SERVER_IP = os.getenv("SERVER")
mongo_db = os.getenv("MONGODB_SERVER")
dictConfig(LOGGING)
logger = logging.getLogger("dev_logger")
ollama_service = f"http://{SERVER_IP}:11436"


# Validate the json data
def validate_json(data):
    try:
        json.dumps(data)
        return True
    except Exception as e:
        return False


def ollama_request(prompt):
    # """Generate llama2 response"""
    url = f"{ollama_service}/v1/chat/completions"
    payload = json.dumps(
        {
            "model": "mistral:instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        }
    )
    headers = {"Content-Type": "application/json"}
    max_retries = 3
    retry_delay = 3
    for retry in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()

            if "Invalid response object from API" in response.text:
                return "Invalid response object from API. Retrying after 3 seconds..."
                time.sleep(retry_delay)
                continue
            else:
                data = response.json()
                res = data["choices"][0]["message"]["content"]
                return res

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return f"HTTP error occurred: {http_err}"
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred: {conn_err}")
            return f"Connection error occurred: {conn_err}"
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Timeout error occurred: {timeout_err}")
            return f"Timeout error occurred: {timeout_err}"
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception occurred: {req_err}")
            return f"Request exception occurred: {req_err}"
        except ValueError as json_err:
            logger.error(f"JSON decoding failed: {json_err}")
            return f"JSON decoding failed: {json_err}"
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return f"An error occurred: {e}"
    return None


def time_to_seconds(time):
    try:
        total_seconds = 0
        # Define a dictionary to map time units to seconds
        unit_mapping = {"w": 5 * 8 * 60 * 60, "d": 8 * 60 * 60, "h": 60 * 60, "m": 60}

        # Use regex to extract time components
        matches = re.findall(r"(\d+)([wdhm]?)", time)

        if not matches:
            raise ValueError("Invalid time format")

        for value, unit in matches:
            total_seconds += int(value) * unit_mapping.get(unit, 1)

        return total_seconds

    except ValueError as ve:
        return None
    except Exception as e:
        return None
