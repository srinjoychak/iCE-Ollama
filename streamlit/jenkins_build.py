import pymongo
import base64
import requests
import logging
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
from requests.auth import HTTPBasicAuth
from pymongo import MongoClient
from utilities import ollama_request, validate_json

mongo_db = os.getenv("MONGODB_SERVER")
client = MongoClient(mongo_db)
db = client["ice"]
SERVER_IP = os.getenv("SERVER")
email = os.getenv("EMAIL")
user_name = email.split("@")[0]
token = os.getenv("JIRA_API_TOKEN")
PORT = os.getenv("PORT")
jenkins_username = os.getenv("JENKINS_USERNAME")
jenkins_api_token = os.getenv("JENKINS_TOKEN")
logger = logging.getLogger("dev_logger")
JENKINS_ANALYSIS_PROMPTS = {
    "Objective": "You are a Jenkins expert. You have been asked to analyze the Jenkins console logs for a specific pipeline. The logs are provided below.",
    "Instructions": "Give a very very brief single line summary of the supplied logs. Highlight any issues from the supplied logs.",
    # "Instructions" : "Identify any issues from the supplied logs. If an issue is identified write a single line summary. Keep your analysis very very brief and to the point. If no issues found reply 'None'.",
    "Summarize": "Summarize this content in very very brief and to the point. Share no more than 2-3 lines. Keep your focus on the final outcome of the supplied data",
}


# myclient = pymongo.MongoClient("mongodb://192.168.0.34:27017/")
# db = myclient["ice"]
class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


def jenkins_register(pipeline_name, jenkins_url, project_name):

    try:
        db.ice_webex_jira_project_data.update_one(
            {"project_name": project_name},
            {
                "$push": {
                    "jenkins_config": {
                        "url": jenkins_url,
                        "service_name": pipeline_name,
                    }
                }
            },
        )
        return {"data": "Jenkins Registration Process Successful"}
    except Exception as e:
        return {"data": f"Jenkins Registration Process Failed.due to {str(e)}"}


def get_jenkins_build_parameters(user_name, service_name):
    try:
        # Fetch user data from the database
        username_obj = db.ice_user_data.find(
            {"user_name": user_name},
            {
                "username": 1,
                "my_primary_projects": 1,
                "_id": 0,
            },
        )

        # Extract username and primary project
        user_data = next(username_obj, None)
        if not user_data:
            raise ValueError("User not found in the database.")

        username = user_data["username"]
        primary_project = user_data["my_primary_projects"]

        # Generate authentication token
        auth_token = generate_basic_token(jenkins_username, jenkins_api_token)

        # Fetch project data from the database
        project_obj = db.ice_webex_jira_project_data.find(
            {"project_name": primary_project}, {"jenkins_config": 1, "_id": 0}
        )

        # Extract Jenkins configuration
        project_data = next(project_obj, None)
        if not project_data:
            raise ValueError("Project not found in the database.")

        for jenkins_data in project_data["jenkins_config"]:
            if jenkins_data["service_name"] == service_name:
                url = jenkins_data["url"]
                break
        else:
            raise ValueError("Service name not found in Jenkins configuration.")

        # Remove parameters from URL
        build_url = remove_parameters_from_url(url)

        logger.info(f"Jenkins URL: {url}")
        return [auth_token, url, build_url]

    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        return [None, str(ve)]
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return [None, "An error occurred while fetching Jenkins build parameters."]


def get_jenkins_build_name(user_name):
    try:
        data = db.ice_user_data.find(
            {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
        )
        for i in data:
            primaryproject = i["my_primary_projects"]
        service_name_list = []
        service_name = db.ice_webex_jira_project_data.find(
            {"project_name": primaryproject}, {"jenkins_config": 1, "_id": 0}
        )
        for i in service_name:
            for j in i["jenkins_config"]:
                service_name = j["service_name"]
                service_name_list.append(service_name)
        return service_name_list
    except Exception as e:
        logger.error(f"Error in fetching service_name_list {str(e)}")
        return None


def generate_basic_token(username, token):
    # Concatenate the username and token with a colon separator
    credentials = f"{username}:{token}"
    # Encode the credentials using base64
    encoded_credentials = base64.b64encode(credentials.encode("utf-8"))
    # Convert the encoded credentials to a string
    basic_token = encoded_credentials.decode("utf-8")

    return "Basic" + " " + basic_token


def remove_parameters_from_url(input_url):
    # Check if the input URL contains "buildWithParameters?token="
    if "build?token=" in input_url:
        # Find the starting index of the "buildWithParameters?token=" substring
        start_index = input_url.find("build?token=")
        # Extract the portion of the URL before the "buildWithParameters?token=" substring
        output_url = input_url[:start_index]
        # Return the output URL
        return output_url
    # If the input URL doesn't contain "buildWithParameters?token=" return the original URL
    return input_url


def jenkins_api_exec(url):
    try:
        resp = requests.get(
            url,
            auth=HTTPBasicAuth(jenkins_username, jenkins_api_token),
        )
        data = resp.text
        if resp.status_code == 200:
            return {"msg": data}
        elif resp.status_code == 401:
            raise AuthenticationError("Invalid username or password.")
        elif resp.status_code == 403:
            raise AuthorizationError("Access to the requested resource was forbidden.")
        else:
            raise Exception(f"An error occurred: {resp.status_code}")
    except AuthenticationError:
        return {"msg": "Invalid username or password."}
    except AuthorizationError:
        return {"msg": "Access to the requested resource was forbidden."}
    except Exception as e:
        return {"msg": f"An error occurred: {str(e)}"}


def ai_analysis(log_output):
    gen_ai_analysis_output = []
    log_output_chunks = [
        log_output[i : i + 50000] for i in range(0, len(log_output), 50000)
    ]
    logger.info(len(log_output_chunks))
    for log_chunk in log_output_chunks:
        gen_ai_prompt = (
            "**Objective:**\n"
            + JENKINS_ANALYSIS_PROMPTS["Objective"]
            + "\n**Instructions:**\n"
            + JENKINS_ANALYSIS_PROMPTS["Instructions"]
            + "\n**Jenkins Consle Logs:**\n"
            + log_chunk
        )
        gen_ai_analysis = ollama_request(gen_ai_prompt)
        gen_ai_analysis_output.append(gen_ai_analysis)
    # summarize_result_prompt = "Summarize this content in very very brief and to the point. Ignore anywhere it says 'Issue: None'. Share no more than 2-3 lines. Keep your focus on the final outcome of the supplied"+ "\n" + " ".join(gen_ai_analysis_output)
    summarize_result_prompt = (
        JENKINS_ANALYSIS_PROMPTS["Summarize"] + "\n" + " ".join(gen_ai_analysis_output)
    )
    summarize_result = ollama_request(summarize_result_prompt)
    return summarize_result


def jenkins_log_analysis_results(log_output):

    if log_output:
        log_output_refined = log_output.replace("[Pipeline]", "")

        if "Finished: SUCCESS" in log_output_refined:
            return "The pipeline has finished successfully"
        else:
            summarize_result = ai_analysis(log_output_refined)
            return summarize_result


def jenkins_build_ai_analysis(barnch, service_name, user_name):
    try:
        build_parameter = get_jenkins_build_parameters(user_name, service_name)
        logger.info(f"Build Parameter: {build_parameter}")
        if build_parameter[0] == None:
            return {"log": None, "data": build_parameter[1]}
        else:
            if len(build_parameter) != 0:
                auth_token = build_parameter[0]
                url = build_parameter[1]
                build_url = build_parameter[2]
                headers = {"Authorization": auth_token}
                param_map = {}
                param_map["git_branch"] = barnch
                if param_map:
                    for name, value in param_map.items():
                        url += f"&{name}={value}"
                logger.info(f"Jenkins URL: {url}")
                response = requests.post(url, headers=headers)
                if response.status_code == 401:
                    # Handle invalid credentials
                    return {"log": None, "data": "Invalid username or password."}
                elif response.status_code == 403:
                    # Handle unauthorized access
                    return {
                        "log": None,
                        "data": "Access to the requested resource was forbidden.",
                    }
                elif response.status_code == 201:
                    get_build_no_url = f"{build_url}/lastBuild/buildNumber"
                    time.sleep(15)
                    logger.info(f"build url{build_url}")
                    res = requests.get(get_build_no_url, headers=headers)
                    build_no = res.json()
                    logger.info(f"res{build_no}")
                    build_console_link = f"{build_url}/{build_no}/console"
                    log_out = f"{build_url}/{build_no}/logText/progressiveText"
                    time.sleep(30)
                    jenkins_outlog = jenkins_api_exec(log_out)
                    logdata = jenkins_outlog["msg"]
                    log_result = jenkins_log_analysis_results(logdata)
                    return {
                        "log": log_result,
                        "data": build_console_link,
                    }
            else:
                return {"log": None, "data": "Add jenkins Token"}
    except Exception as e:
        return {"log": None, "data": f"Jenkins build failed with exception as {str(e)}"}


def add_comment(comment, issue_key):
    """Get the Jira Velocity Report"""
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/addcomment/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            logger.error("No primary project found Please Register a project first")
            return "No primary project found Please Register a project first"

        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
            "comment": comment,
            "issue_key": issue_key,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response)
    if response.status_code == 200:
        return "Comment added successfully"
    else:
        return "Failed to add comment"
