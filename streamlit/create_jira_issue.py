import requests
import os
import datetime
import time
import json
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
email_address = os.getenv("EMAIL")
token = os.getenv("JIRA_API_TOKEN")
SERVER_IP = os.getenv("SERVER")
PORT = os.getenv("PORT")
mongo_db = os.getenv("MONGODB_SERVER")
username = email_address.split("@")[0]
client = MongoClient(mongo_db)
db = client["ice"]


def get_epic(user_name):
    """
    Fetches epic issues for a given user from JIRA.

    Args:
        user_name (str): The username of the user.

    Returns:
        tuple: A tuple containing keys of the epic data and the epic data itself if successful.
        str: An error message if no primary project or epic is found, or if an error occurs.
    """
    try:
        # Construct the URL for the JIRA API request
        url = "http://{0}:{1}/jiraapi/getepicissues/".format(SERVER_IP, PORT)
        headers = {"Content-Type": "application/json"}

        # Query the database for the user's primary projects
        data = db.ice_user_data.find(
            {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
        )

        # Check if the user has any primary projects
        my_primary_project = None
        for record in data:
            if not record["my_primary_projects"]:
                return "No primary project found Please Register a project first"
            else:
                my_primary_project = record["my_primary_projects"]

        # If no primary project is found, return an error message
        if not my_primary_project:
            return [None,"No primary project found Please Register a project first"]

        # Prepare the payload for the API request
        payload = json.dumps(
            {"project_name": my_primary_project, "user_name": user_name}
        )

        # Make the API request to JIRA
        response = requests.post(url, headers=headers, data=payload)

        # Check if the response is successful
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get("success"):
                epic_data = response_json.get("data", {})
                keys_tuple = tuple(epic_data.keys())
                return keys_tuple, epic_data
            else:
                return [None, "No epic found"]
        else:
            return [
                None,
                f"Failed to fetch epic data, status code: {response.status_code}",
            ]

    except requests.RequestException as e:
        # Handle any request-related exceptions
        return [None, f"An error occurred while making the API request: {e}"]

    except Exception as e:
        # Handle any other exceptions
        return [None, f"An unexpected error occurred: {e}"]


def issue_creation_function(
    user_name,
    issue_summary,
    issue_desc,
    acceptance_criteria,
    issue_type,
    key,
):
    try:
        # Fetch user data
        data = db.ice_user_data.find(
            {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
        )

        my_primary_project = None
        for record in data:
            if not record["my_primary_projects"]:
                return "No primary project found Please Register a project first"
            else:
                my_primary_project = record["my_primary_projects"]

        if not my_primary_project:
            return "No primary project found Please Register a project first"

        # Prepare the payload
        payload = json.dumps(
            {
                "project_name": my_primary_project,
                "user_name": user_name,
                "summary": issue_summary,
                "description": issue_desc,
                "acceptance_criteria": acceptance_criteria,
                "issue_type": issue_type,
                "epic_key": key,
            }
        )

        # Set headers
        headers = {"Content-Type": "application/json"}

        # Make the request
        url = f"http://{SERVER_IP}:{PORT}/jiraapi/createissue/"
        response = requests.post(url, headers=headers, data=payload)

        # Check the response
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                issue_link = response_data.get("data")
                return issue_link
            else:
                return "Issue creation failed: " + response_data.get(
                    "message", "Unknown error"
                )
        else:
            return f"Issue creation failed with status code {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"
    except json.JSONDecodeError as e:
        return f"JSON decode error: {e}"
    except Exception as e:
        return f"An error occurred: {e}"
