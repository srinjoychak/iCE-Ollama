import json
import requests
import os

from dotenv import load_dotenv
import logging
from logging.config import dictConfig
from logging_file import LOGGING
from utilities import validate_json, ollama_request
from jira_project_registration import project_registartion
dictConfig(LOGGING)
logger = logging.getLogger("dev_logger")
load_dotenv()
email = os.getenv("EMAIL")
token = os.getenv("JIRA_API_TOKEN")
SERVER_IP = os.getenv("SERVER")
mongo_db = os.getenv("MONGODB_SERVER")
PORT = os.getenv("PORT")
SPRINT_REPORT_PROMPTS = {
    "set_profile": "You are a seasoned Scrum Master and Jira specialist.",
    "detailed_summary": "Your task involves provide a succinct overview of the project's progress. This section should include bullet points detailing key progress information, followed by a brief paragraph summarizing the same information.",
    "user_progress": "Create a single line summary of each user story. Only include Comments, Worklog Comments, Worklog Duration. Reply as '<Issue_ID> [<Assignee>] || Status: <Status> \n - Comments: <Comment or Worklog Comment> \n - Time Spent: <Worklog Duration>'. Please refrain from using bullet points in this section.",
    "user_prog_summarization": "From the provided dataset, generate a concise summary report that consists of two distinct sections:\n1. Summary of Issue_IDs with Valid Comments: For each issue with a valid comment, provide a single-line summary that includes the Issue_ID, the Assignee (if available), the Status, and a highlighted excerpt or paraphrase of the valid comment. Ensure that the comment provided adds substantial information or reflects progress related to the issue.\n2. Provide a list of Issue_IDs that have no valid comments. The invalid comments are 'No comments found.'. Ensure that the list is concise and easy to read.",
    "risks_blockers": "From the following data please analyze the Comments or Worklog Comments for each issue and identify any Blockers or Risks mentioned there. Reply as JSON, with the following format: {'issue_key': ['Risk':'risks', 'Dependency':'dependencies', 'Blocker':'blockers']}",
    "risk_blocker_summarization": "From the shared data, generate very brief summary of the risks, dependencies, blocker in single line per issue including the assignee. Exclude issues which has no risks, dependencies, and blockers. Please refrain from using bullet points.",
}


def generate_user_prog_chunk(user_prog_data):
    """This will take a large JSON of user progress data and split it into chunks of 10"""
    user_prog_chunk = []
    sublist = []
    for i, data in enumerate(user_prog_data):
        sublist.append(data)
        if (i + 1) % 10 == 0:
            user_prog_chunk.append(sublist)
            sublist = []
    if sublist:
        user_prog_chunk.append(sublist)
    return user_prog_chunk


def generate_sprint_report_with_gai(data):
    """Generate the Jira Sprint Report"""
    final_report = []
    blocker_risks_summary = []
    gen_summary_prompt = (
        SPRINT_REPORT_PROMPTS["set_profile"]
        + SPRINT_REPORT_PROMPTS["detailed_summary"]
        + "\n"
        + str(data["summary"])
    )
    gen_summary_resp = ollama_request(gen_summary_prompt)
    gen_summary_resp = (
        "\n\n**Generate the Sprint Summary Report**\n\n " + gen_summary_resp + "\n\n"
    )
    final_report.append(gen_summary_resp)
    user_prog_data = data["users_progress"]
    user_prog_chunks = generate_user_prog_chunk(user_prog_data)
    user_progress_summary = []
    for item in user_prog_chunks:
        gen_user_prog_prompt = (
            SPRINT_REPORT_PROMPTS["set_profile"]
            + SPRINT_REPORT_PROMPTS["user_progress"]
            + "\n"
            + str(item)
        )
        gen_user_prog_resp = ollama_request(gen_user_prog_prompt)
        user_progress_summary.append(gen_user_prog_resp)

    usr_prog_summarization_prompt = (
        SPRINT_REPORT_PROMPTS["set_profile"]
        + SPRINT_REPORT_PROMPTS["user_prog_summarization"]
        + "\n"
        + str(user_progress_summary)
    )
    usr_prog_summarization_resp = ollama_request(usr_prog_summarization_prompt)
    usr_prog_summarization_resp = (
        "\n\n**User Progress Report**\n\n" + usr_prog_summarization_resp + "\n\n"
    )
    final_report.append(usr_prog_summarization_resp)

    for item in user_prog_chunks:
        gen_risks_blockers_prompt = (
            SPRINT_REPORT_PROMPTS["set_profile"]
            + SPRINT_REPORT_PROMPTS["risks_blockers"]
            + "\n"
            + str(item)
        )
        gen_risks_blockers_resp = ollama_request(gen_risks_blockers_prompt)
        blocker_risks_summary.append(gen_risks_blockers_resp)

    risk_blocker_summarization_prompt = (
        SPRINT_REPORT_PROMPTS["set_profile"]
        + SPRINT_REPORT_PROMPTS["risk_blocker_summarization"]
        + "\n"
        + str(blocker_risks_summary)
    )
    risk_blocker_summarization_resp = ollama_request(risk_blocker_summarization_prompt)
    risk_blocker_summarization_resp = (
        "\n\n**Risks and Blockers Report**\n\n"
        + risk_blocker_summarization_resp
        + "\n\n"
    )
    final_report.append(risk_blocker_summarization_resp)
    return final_report


def sprint_report(jira_data):
    if validate_json(jira_data):
        final_report = generate_sprint_report_with_gai(jira_data)
        return final_report
    else:
        return "data is not in json format"
