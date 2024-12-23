import requests
import os
import datetime
import time
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


def project_registartion(url, user_name):

    end_url = "http://{0}:{1}/jiraapi/project_registartion/".format(SERVER_IP, PORT)
    payload = {
        "user_name": user_name,
        "url": url,
        "github_url": "",
        "token": token,
        "username": username,
        "scrum_master": username,
        "email_address": email_address,
    }
    response = requests.request("POST", end_url, data=payload)
    data = response.json()
    message = data
    return message


def switch_project_to_other_project(user_name):
    try:
        data = db.ice_user_data.find(
            {"user_name": user_name},
            {"my_jira_projects": 1, "my_primary_projects": 1, "_id": 0},
        )

        projects_list = []
        primaryproject = None

        for i in data:
            projects_data = i.get("my_jira_projects", [])
            primaryproject = i.get("my_primary_projects", None)

            if not projects_data:
                raise ValueError("No Project Found")
            if not primaryproject:
                raise ValueError("No Project Found")

            for j in projects_data:
                for k in j.values():
                    projects_list.append(k)

        if len(projects_list) == 0:
            return "No Project Found"
        else:
            return [projects_list, primaryproject]

    except ValueError as ve:
        return str(ve)
    except Exception as e:
        return str(e)


def updating_primary_project(user_name, selected_project):
    db.ice_user_data.update_one(
        {"user_name": user_name},
        {"$set": {"my_primary_projects": selected_project}},
    )
    res = "Primary Project Changed To {} Successfully .".format(selected_project)
    return res


def insert_data_into_mongodb(user_name, email):
    username = user_name
    user_email = email
    username_data = db.ice_user_data.find(
        {"user_name": user_name}, {"user_name": 1, "_id": 0}
    )
    username_ref = list(username_data)
    if len(username_ref) == 0:
        db_insert = db.ice_user_data.insert_one(
            {
                "user_name": user_name,
                "username": username,
                "email": user_email,
                "iCE_cred_properties": {
                    "sso_auth": "",
                    "sonar_cube": "",
                    "git_token": "",
                    "k8s_config_file": "",
                    "jenkins_token": "",
                    "api_token": "",
                },
                "my_primary_projects": "",
                "my_jira_projects": [],
                "usercreated": datetime.datetime.today().strftime("%d-%m-%Y %I:%M %p"),
                "lastActivity": datetime.datetime.today().strftime("%d-%m-%Y %I:%M %p"),
            }
        )
    elif len(username_ref) != 0:
        username_room_db = username_ref[0]["user_name"]
        db.ice_user_data.update_one(
            {"user_name": username_room_db},
            {
                "$set": {
                    "lastActivity": datetime.datetime.today().strftime(
                        "%d-%m-%Y %I:%M %p"
                    )
                }
            },
        )


def filter_by_assignee(data, assignee_name):

    filtered_data = {
        key: value for key, value in data.items() if value["Assignee"] == assignee_name
    }
    return filtered_data


def get_issue_details(issue_key):
    data = db.ice_user_data.find(
            {"user_name": username}, {"my_primary_projects": 1, "_id": 0}
        )

        # Check if the user has any primary projects
    my_primary_project = None
    for record in data:
        if not record["my_primary_projects"]:
            return [None,"No primary project found Please Register a project first"]
        else:
            my_primary_project = record["my_primary_projects"]

    # If no primary project is found, return an error message
    if not my_primary_project:
        return [None,"No primary project found Please Register a project first"]
    end_url = "http://{0}:{1}/jiraapi/getissuedetails/".format(SERVER_IP, PORT)
    payload = {
        "project_key": my_primary_project,
        "username": username,
        "issue_key": issue_key,
    }
    response = requests.request("POST", end_url, data=payload)
    if response.json()["success"] == True:
        data = response.json()["data"]
        return data
    else:
        data = response.json()["data"]
        return data
