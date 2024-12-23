import streamlit as st
import json
import requests
import os
from pathlib import Path
import time
import sys
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.tools import tool
from langchain.tools.render import render_text_description
from langchain_core.output_parsers import JsonOutputParser
from pydantic.v1 import BaseModel, Field, ValidationError
from daily_scrum_report import generate_combined_string
from sprint_report import sprint_report
from velocity_report import velocity_report
from operator import itemgetter
from dotenv import load_dotenv
import logging
from logging.config import dictConfig
from logging_file import LOGGING
from pymongo import MongoClient
from jira_project_registration import (
    project_registartion,
    switch_project_to_other_project,
    insert_data_into_mongodb,
    updating_primary_project,
    filter_by_assignee,
    get_issue_details,
)
from create_jira_issue import issue_creation_function, get_epic
from utilities import time_to_seconds
from jenkins_build import (
    jenkins_register,
    get_jenkins_build_name,
    jenkins_build_ai_analysis,
    add_comment,
)

import datetime
import pandas as pd
import plotly.express as px
from git_hub_code_search import search_code_in_github

# Define icons for user and bot
user_icon = '<i class="fas fa-user user-icon"></i>'  # FontAwesome user icon (white)
bot_icon = "🤖"  # bot icon (for the bot's response)
dictConfig(LOGGING)
logger = logging.getLogger("dev_logger")
load_dotenv()
email = os.getenv("EMAIL")
user_name = email.split("@")[0]
token = os.getenv("JIRA_API_TOKEN")
SERVER_IP = os.getenv("SERVER")
mongo_db = os.getenv("MONGODB_SERVER")
PORT = os.getenv("PORT")
model_name = os.getenv("MODEL_NAME")
client = MongoClient(mongo_db)
from pymongo import MongoClient

st.markdown(
    """
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <style>
        .user-icon {
            color: #2879ff;
            padding-right: 6px;
        }
        # .bot-icon {
        #     color: #f39c12;  /* Yellow-orange for the bot icon */
        # }
        .chat-container {
            width: 100%;
            overflow: hidden;
        }
        .title {
            white-space: nowrap;
            font-size: 38px;
            font-weight: 600;
        }
        .user-message-container {
            display: flex;
            justify-content: flex-end; /* Aligns the entire message container to the right */
            align-items: center; /* Vertically centers the icon with the message */
        }
        .bot-message-container {
            display: flex;
            justify-content: flex-start; /* Aligns the bot message and icon to the left */
            align-items: flex-start; /* Vertically centers the icon with the message */
        }
        .user-message {
            background-color: #f0f0f0;    /* Light gray background for user messages */
            color: #000000;               /* Black text */
            border-radius: 20px;          /* Rounded corners */
            padding: 10px 15px;           /* Padding inside the bubble */
            margin: 10px 0;               /* Space between messages */
            max-width: 60%;               /* Limit the width of the message bubble */
            word-wrap: break-word;        /* Break long words */
            text-align: right;            /* Align text inside the bubble to the right */
            clear: both;                  /* Clear floats to prevent overlap */
            float: none;
        }
       .bot-message {
            background-color: #fff9c4;    /* Light yellow background for bot messages */
            color: #000000;               /* Black text */
            border-radius: 20px;          /* Rounded corners */
            padding: 10px 15px;           /* Padding inside the bubble */
            margin: 10px 0;               /* Space between messages */
            max-width: 60%;               /* Limit the width of the message bubble */
            word-wrap: break-word;        /* Break long words */
            text-align: left;             /* Align text inside the bubble to the left */
            clear: both;                  /* Clear floats */
        }
        .clearfix {
            clear: both;                  /* Ensure no overlap between floats */
        }
        .timestamp {
            font-size: 0.8em;
            color: #999999;
            margin-top: 5px;
            display: block;
        }
        /* Optional: Add some padding to the whole chat area */
        .chat-wrapper {
            padding: 20px;
        }
       
    </style>
    """,
    unsafe_allow_html=True,
)

db = client["ice"]
ollama_service = f"http://{SERVER_IP}:11436"

# Set up the LLM which will power our application.
model = Ollama(base_url=ollama_service, model=model_name)


def restart_session():
    """Restart the session state"""
    st.session_state.clear()
    st.experimental_rerun()
    return "Session restarted"


# Get Sprint Report
# def get_sprint_report() -> str:
#     """Get the Jira Sprint Report"""
#     data = db.ice_user_data.find(
#         {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
#     )
#     for record in data:
#         logger.info(f"Record: {record}")
#         if not record["my_primary_projects"]:
#             logger.error("No primary project found Please Register a project first")
#             return "No primary project found Please Register a project first Please Register a project first"
#         else:
#             my_primary_project = record["my_primary_projects"]
#     url = f"http://{SERVER_IP}:{PORT}/jiraapi/datasprint/"
#     payload = json.dumps(
#         {
#             "project_key": my_primary_project,
#             "user_name": user_name,
#         }
#     )
#     headers = {"Content-Type": "application/json"}
#     response = requests.request("POST", url, headers=headers, data=payload)
#     if response.status_code == 200 and response.json()["status"] == True:
#         project_metadata = response.json()["data"]
#         data = sprint_report(project_metadata)
#         strs = ""
#         for i in data:
#             strs += i
#         return strs
#     else:
#         return "No data found"

# Get Sprint Report
# def get_sprint_report() -> str:
#     """Get the Jira Sprint Report"""
#     data = db.ice_user_data.find(
#         {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
#     )
#     for record in data:
#         logger.info(f"Record: {record}")
#         if not record["my_primary_projects"]:
#             logger.error("No primary project found Please Register a project first")
#             return "No primary project found Please Register a project first Please Register a project first"
#         else:
#             my_primary_project = record["my_primary_projects"]
#     url = f"http://{SERVER_IP}:{PORT}/jiraapi/datasprint/"
#     payload = json.dumps(
#         {
#             "project_key": my_primary_project,
#             "user_name": user_name,
#         }
#     )
#     headers = {"Content-Type": "application/json"}
#     response = requests.request("POST", url, headers=headers, data=payload)
#     if response.status_code == 200 and response.json()["status"] == True:
#         project_metadata = response.json()["data"]
#         summary = project_metadata['summary']
#         users_progress = project_metadata['users_progress']
#         logger.info("summary data in the sprint file")
#         logger.info(summary)

#         # Display Sprint Summary
#         st.title(f"Sprint Summary Report: {summary['sprint_name']}")
#         st.subheader("Sprint Metrics")

#         # Create a dataframe for the sprint metrics
#         sprint_metrics = pd.DataFrame({
#             'Metrics': ['Duration Completion %', 'Work Completion %', 'Scope Change %'],
#             'Values': [summary['duration_completion_percentage'], summary['work_completion_percentage'], summary['scope_change_percentage']]
#         })

#         fig = px.bar(sprint_metrics, x='Metrics', y='Values', title='Sprint Progress Metrics', text='Values', color='Metrics')
#         st.plotly_chart(fig)

#         # Work Status Distribution
#         st.subheader("Work Status Distribution")
#         work_status_df = pd.DataFrame({
#             'Status': ['Not Started', 'In Progress', 'Done'],
#             'Percentage': [summary['Not Started'], summary['In Progress'], summary['Done']]
#         })

#         fig2 = px.pie(work_status_df, names='Status', values='Percentage', title="Work Items Status")
#         st.plotly_chart(fig2)

#         # User Progress Report as Table
#         st.subheader("User Progress Report")
#         users_progress_df = pd.DataFrame(users_progress)
#         st.dataframe(users_progress_df)

#         # Total Worklog Effort Visualization
#         st.subheader("Worklog Effort Comparison")
#         users_progress_df['Total Worklog Effort (hours)'] = users_progress_df['Total Worklog Effort (hours)'].replace('50h 0m', 50).astype(float)
#         fig3 = px.bar(users_progress_df, x='Key', y='Total Worklog Effort (hours)', title='Worklog Effort per Issue', text='Total Worklog Effort (hours)', color='Key')
#         st.plotly_chart(fig3)
#         return summary
#     else:
#         return "No data found"


def get_sprint_report() -> str:
    """Get the Jira Sprint Report"""
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )

    my_primary_project = None
    for record in data:
        logger.info(f"Record: {record}")
        my_primary_project = record.get("my_primary_projects")
        if not my_primary_project:
            logger.error("No primary project found. Please register a project first.")
            return "No primary project found. Please register a project first."

    if not my_primary_project:
        return "No primary project found. Please register a project first."

    url = f"http://{SERVER_IP}:{PORT}/jiraapi/datasprint/"
    payload = json.dumps(
        {
            "project_key": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"API Request failed: {e}")
        return "Failed to fetch the sprint report. Please try again later."

    response_data = response.json()
    if response.status_code == 200 and response_data.get("status") == True:
        project_metadata = response_data.get("data", {})

        summary = project_metadata.get("summary")
        users_progress = project_metadata.get("users_progress", [])

        if not summary:
            logger.error("No summary data found.")
            return "No summary data found in the sprint report."

        # Display Sprint Summary
        st.title(
            f"Sprint Summary Report: {summary.get('sprint_name', 'Unknown Sprint')}"
        )
        st.subheader("Sprint Metrics")

        # Create a dataframe for sprint metrics
        sprint_metrics = pd.DataFrame(
            {
                "Metrics": [
                    "Duration Completion %",
                    "Work Completion %",
                    "Scope Change %",
                ],
                "Values": [
                    summary.get("duration_completion_percentage", 0),
                    summary.get("work_completion_percentage", 0),
                    summary.get("scope_change_percentage", 0),
                ],
            }
        )

        fig = px.bar(
            sprint_metrics,
            x="Metrics",
            y="Values",
            title="Sprint Progress Metrics",
            text="Values",
            color="Metrics",
        )
        st.plotly_chart(fig)

        # Work Status Distribution
        st.subheader("Work Status Distribution")
        work_status_df = pd.DataFrame(
            {
                "Status": ["Not Started", "In Progress", "Done"],
                "Percentage": [
                    summary.get("Not Started", 0),
                    summary.get("In Progress", 0),
                    summary.get("Done", 0),
                ],
            }
        )

        fig2 = px.pie(
            work_status_df,
            names="Status",
            values="Percentage",
            title="Work Items Status",
        )
        st.plotly_chart(fig2)

        # User Progress Report as Table
        st.subheader("User Progress Report")
        users_progress_df = pd.DataFrame(users_progress)
        users_progress_df.index = users_progress_df.index + 1
        st.dataframe(users_progress_df)
        # Total Worklog Effort Visualization
        st.subheader("Worklog Effort Comparison")
        def convert_to_hours(time_str):
            if 'h' in time_str:
                hours, minutes = time_str.split('h')
                hours = int(hours.strip())
                minutes = int(minutes.strip().replace('m', ''))
                return hours + minutes / 60
            return 0
        users_progress_df["Total Worklog Effort (hours)"] = users_progress_df["Total Worklog Effort (hours)"].apply(convert_to_hours)  
        fig3 = px.bar(
            users_progress_df,
            x="Key",
            y="Total Worklog Effort (hours)",
            title="Worklog Effort per Issue",
            text="Total Worklog Effort (hours)",
            color="Key",
        )
        st.plotly_chart(fig3)

        return "Sprint report generated successfully."
    else:
        error_message = response_data.get("message", "No data found.")
        logger.error(f"API Response Error: {error_message}")
        return error_message


# Function to transform the JSON data into a DataFrame
def process_velocity_data(data):
    rows = []
    for sprint, details in data.items():
        rows.append(
            {
                "Sprint": sprint,
                "Completed_Story_Points": details["Completed_Issues_Story_Points"],
                "Estimated_Story_Points": details["Estimated_Story_Points"],
                "Issues_Count": len(details["Issues in Sprint"]),
            }
        )
    df = pd.DataFrame(rows)

    # Set the index to start from 1
    df.index = df.index + 1

    return df


# Get Velocity Report
def get_velocity_report():
    """Get the Jira Velocity Report"""
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/velocityreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return "No primary project found Please Register a project first"
            logger.error("No primary project found Please Register a project first")
        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.json()["data"] != "Authnication Failed":
        velocity_data = response.json()["data"]
        velocity_df = process_velocity_data(velocitySampleData)

        # Display the data as a table
        st.dataframe(velocity_df)
        logger.error(f"Response from velocity data:======{velocitySampleData}")
        # data = velocity_report(velocity_data)
        # Create the bar chart using Plotly
        fig = px.bar(
            velocity_df,
            x="Sprint",
            y=["Completed_Story_Points", "Estimated_Story_Points"],
            title="Sprint Velocity (Completed vs Estimated Story Points)",
            labels={"value": "Story Points", "Sprint": "Sprint"},
            barmode="group",
        )

        # Display the chart
        st.plotly_chart(fig)
        # return velocity_data

        # logger.info(f"velocity data======+++++++++++++++++++++++++++++++++++{data}")
        return velocity_data
    else:
        return "Authentication Failed"


def get_burn_down_report():
    """Get the burn down Report"""

    url = f"http://{SERVER_IP}:{PORT}/jiraapi/burndownreport/"
    logger.info(f"URL: {url}")
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
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    report_data = response.json()
    if report_data["success"]:
        data = report_data.json()["data"]

        # Display the report URL
        st.markdown(
            f"[View Full Report]({report_data['report_url']})", unsafe_allow_html=True
        )

        # Generate and display the burndown chart
        df = generate_burndown_data(data)
        fig = px.line(
            df,
            x="Date",
            y=["Ideal Burndown", "Actual Burndown"],
            title=f"Burndown Chart for {data['sprint_name']}",
            markers=True,
            labels={"value": "Story Points", "Date": "Sprint Day"},
        )
        st.plotly_chart(fig)

        # Create a DataFrame for the issues table
        issues = []
        for key, value in data.items():
            if isinstance(value, list):
                issue_summary = value[0]["issue_summary"]
                story_points = value[2]["story_points"]
                issues.append(
                    {
                        "Issue Key": key,
                        "Summary": issue_summary,
                        "Story Points": story_points,
                    }
                )

        issues_df = pd.DataFrame(issues)
        st.table(issues_df)
        return report_data
    else:
        st.error("Failed to fetch the burndown report data.")

    # if response.json().get("success") == True and response.json().get("data"):
    #     burn_down_data = response.json()["data"]
    #     report_url = response.json()["report_url"]
    #     logger.info("===burndown report123========", burn_down_data)
    #     logger.info("===burndown report123 link========", report_url)
    #     return burn_down_data, report_url
    # else:
    #     return "Authentication Failed"


# Function to generate burndown data
def generate_burndown_data(data):
    start_date = datetime.datetime.strptime(data["startDate"], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(data["endDate"], "%Y-%m-%d")
    total_days = (end_date - start_date).days

    total_story_points = sum(
        issue[2]["story_points"]
        for issue in data.values()
        if isinstance(issue, list) and issue[2]["story_points"] is not None
    )

    # Ideal burndown calculation
    ideal_burndown = [
        total_story_points - (i * (total_story_points / total_days))
        for i in range(total_days + 1)
    ]
    actual_burndown = [total_story_points]  # Start with total story points

    # Simulate actual burndown
    completed_points = 0
    for issue_key, issue_details in data.items():
        if isinstance(issue_details, list) and issue_details[1]["updated_date"]:
            for date_str, hours in issue_details[1]["updated_date"].items():
                date = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d")
                days_since_start = (date - start_date).days
                if days_since_start <= total_days:
                    completed_points += hours_to_story_points(
                        hours
                    )  # Custom function to map hours to story points
                    actual_burndown.append(total_story_points - completed_points)

    # Fill the rest of the days in actual burndown
    actual_burndown += [actual_burndown[-1]] * (total_days + 1 - len(actual_burndown))
    dates = [start_date + datetime.timedelta(days=i) for i in range(total_days + 1)]

    # Create DataFrame
    df = pd.DataFrame(
        {
            "Date": dates,
            "Ideal Burndown": ideal_burndown,
            "Actual Burndown": actual_burndown,
        }
    )
    return df


# Function to map hours to story points (you may adjust the logic)
def hours_to_story_points(hours):
    if "h" in hours:
        return int(hours.replace("h", "")) / 8  # Assuming 8 hours per story point
    elif "d" in hours:
        return int(hours.replace("d", ""))
    return 0


def get_jira_burn_up_report():
    """Get the burn up Report"""

    url = f"http://{SERVER_IP}:{PORT}/jiraapi/burnupreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return "No primary project found Please Register a project first"
        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    logger.info("==burn up report=====", response.json())
    if response.json()["success"] == True or response.json()["data"] == "true":
        burn_up_data = response.json()["data"]
        report_url = response.json()["report_url"]
        logger.info(f"Response from burn up report: {burn_up_data}{report_url}")
        return burn_up_data, report_url
    else:
        return "Authentication Failed"


# def get_daily_scrum_report():
#     """Get the Jira Daily Scrum Report"""

#     data = db.ice_user_data.find(
#         {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
#     )
#     for record in data:
#         if not record["my_primary_projects"]:
#             return "No primary project found Please Register a project first"
#         else:
#             my_primary_project = record["my_primary_projects"]
#     url = f"http://{SERVER_IP}:{PORT}/jiraapi/dailystatusreport/"
#     payload = json.dumps({"project_name": my_primary_project, "user_name": user_name})
#     headers = {"Content-Type": "application/json"}
#     response = requests.request("POST", url, headers=headers, data=payload)
#     logger.info(f"Response from daily scrum report: {response.json()}")
#     if response.status_code == 200 and response.json()["success"] == True:
#         res = response.json()["data"]
#     # Check if data retrieval was successful
#     if res['success']:
#         st.title("Task Progress Report")

#         # Iterate through each user in the data
#         for user, tasks in data['data'].items():
#             st.subheader(f"Task Details for {user}")

#             # Convert user's tasks to a DataFrame
#             user_df = pd.DataFrame(tasks)

#             # Display the table of tasks
#             st.dataframe(user_df)

#             # Bar chart to show task distribution by 'key'
#             st.subheader(f"Task Distribution for {user}")
#             task_counts = user_df['key'].value_counts().reset_index()
#             task_counts.columns = ['Key', 'Task Count']

#             # Create bar chart
#             fig = px.bar(
#                 task_counts,
#                 x='Key',
#                 y='Task Count',
#                 text='Task Count',
#                 title=f'Tasks per Key for {user}',
#                 labels={'Key': 'Issue Key', 'Task Count': 'Number of Tasks'},
#                 color='Key'
#             )
#             st.plotly_chart(fig)
#     else:
#         st.error("No data available")


def get_daily_scrum_report():
    """Get the Jira Daily Scrum Report"""

    # Simulated MongoDB query logic for user's project
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    my_primary_project = None
    for record in data:
        if not record.get("my_primary_projects"):
            return st.error(
                "No primary project found. Please register a project first."
            )
        else:
            my_primary_project = record["my_primary_projects"]

    if not my_primary_project:
        return st.error("Primary project not found. Please register a project first.")

    # Simulated API payload and request (replace SERVER_IP/PORT appropriately)
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/dailystatusreport/"
    payload = json.dumps({"project_name": my_primary_project, "user_name": user_name})
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        return st.error(f"Failed to fetch data. Status code: {response.status_code}")

    response_data = response.json()
    logger.info(f"Response from daily scrum report: {response_data}")

    if not response_data.get("success"):
        return st.error("No data available")

    # Combine the data into a pandas DataFrame for tabular view
    all_tasks = []
    for user, tasks in response_data["data"].items():
        for task in tasks:
            task["User"] = user  # Add user column
            all_tasks.append(task)

    # Create the DataFrame
    overall_df = pd.DataFrame(all_tasks)

    # Check if the DataFrame is empty
    if overall_df.empty:
        return st.warning("No scrum data available to display.")

    # Display Tabular Data with Sequential Indexes for Each User
    for user in overall_df["User"].unique():
        user_specific_df = overall_df[overall_df["User"] == user].copy()
        user_specific_df.reset_index(drop=True, inplace=True)
        user_specific_df.index += 1  # Set index starting from 1 for each table
        user_specific_df.index.name = None  # Remove index column name

        st.subheader(f"Task Details for {user}")
        st.dataframe(user_specific_df)

    # Summary Section
    st.subheader("Summary")
    total_tasks = len(overall_df)
    tasks_per_user = overall_df["User"].value_counts()
    overall_df.index += 1
    overall_df.index.name = None
    summary_df = pd.DataFrame(
        {"User": tasks_per_user.index, "Total Tasks": tasks_per_user.values}
    )

    st.write(f"**Total Tasks:** {total_tasks}")
    st.table(summary_df)

    return "Scrum Report generated successfully"


# Usage (Assuming Streamlit app structure)
# user_name = "sampleUser"  # Simulate dynamic user input or session state
# get_daily_scrum_report(user_name)


def view_backlog():
    """View the Jira Backlog"""

    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return "No primary project found Please Register a project first"
        else:
            my_primary_project = record["my_primary_projects"]
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/viewbacklog/"
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    logger.info(f"Response from view backlog: {response.json()}")
    if response.status_code == 200 and response.json()["success"] == True:
        data = response.json()["data"]
        string = ""
        for k, v in data.items():
            string += f"{k} : {v}\n" + "\n"
        return string
    else:
        data = response.json()["data"]
        return data


def get_my_issues():
    """Get the Jira Issues"""
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/getissues/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return "No primary project found Please Register a project first"
        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    logger.info(f"Response from get my issues: {response}")
    if response.status_code == 200 and response.json()["success"] == True:
        data = response.json()["data"]
        return data
    else:
        data = response.json()["data"]
        logger.error(f"Response from get my issues: {data}")
        return data


class JiraSprintReportRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or generate a sprint report. No parameters should be extracted from the user input.",
    )


class SwitchJiraProjectRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to switch Jira projects. No parameters should be extracted from the user input",
    )


class JiraProjectRegistrationRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get the required details for jira project registration or to register a jira  project. No parameters should be extracted from the user input.",
    )


class JiraVelocityReportRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or generate a velocity report. No parameters should be extracted from the user input.",
    )


class JiraBurnDownReportRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or generate a burn down report. No parameters should be extracted from the user input.",
    )


class JiraBurnUpReportRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or generate a burn up report. No parameters should be extracted from the user input.",
    )


class JiraDailyScrumReport(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to generate or get a daily scrum report. No parameters should be extracted from the user input.",
    )


class GetMyIssues(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or view user issues. No parameters should be extracted from the user input.",
    )


class GetIssuesdetails(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or view user issues. No parameters should be extracted from the user input.",
    )


class SprintIssues(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get or view all sprint issues. No parameters should be extracted from the user input.",
    )


class CreateJiraIssueRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to get the required details for create a Jira issue. No parameters should be extracted from the user input.",
    )


class ViewBacklogRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to view backlog issues. No parameters should be extracted from the user input.",
    )


class JenkinsRegisterRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to Register Jenkins. No parameters should be extracted from the user input.",
    )


class RunJenkinsPipelineRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to Run Jenkins Pipeline. No parameters should be extracted from the user input.",
    )


class GitHubSearchRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to search for code in GitHub. No parameters should be extracted from the user input.",
    )


class RestartAppRequest(BaseModel):
    description: str = Field(
        default="N/A",
        description="This field should contain a request to restart the app. No parameters should be extracted from the user input.",
    )


@tool("restart_app", return_direct=True, args_schema=RestartAppRequest)
def tool_restart_app() -> str:
    """Restart the app with Restart command"""
    return restart_session()


@tool("sprint_report", return_direct=True, args_schema=JiraSprintReportRequest)
def tool_sprint_report() -> str:
    """Generate Sprint Report using User Input"""
    return


@tool(
    "register_project", return_direct=True, args_schema=JiraProjectRegistrationRequest
)
def tool_register_project() -> str:
    """Register Jira project using User Input"""
    return None


@tool("switch_jira_project", return_direct=True, args_schema=SwitchJiraProjectRequest)
def tool_switch_jira_project() -> str:
    """Switch Jira project using User Input"""
    return None


@tool(
    "scrum_report",
    return_direct=True,
    args_schema=JiraDailyScrumReport,
)
def tool_daily_scrum_report():
    """generate Daily Scrum  Report using User Input"""
    return


@tool(
    "velocity_report",
    return_direct=True,
    args_schema=JiraVelocityReportRequest,
)
def tool_velocity_report() -> str:
    """generate Velocity Report using User Input"""
    # return get_velocity_report()
    return


@tool(
    "burn_down_report",
    return_direct=True,
    args_schema=JiraBurnDownReportRequest,
)
def tool_burn_down_report():
    """generate Burn Down Report using User Input"""
    # return display_burndown_chart()
    return


@tool(
    "burn_up_report",
    return_direct=True,
    args_schema=JiraBurnUpReportRequest,
)
def tool_jira_burn_up_report():
    """generate Burn Up Report using User Input"""
    # return display_burnup_chart_and_table()
    return


@tool("get_issues_details", return_direct=True, args_schema=GetIssuesdetails)
def tool_get_issues_details() -> str:
    """Get Issues Details using User Input"""
    return None


@tool("create_jira_issue", return_direct=True, args_schema=CreateJiraIssueRequest)
def tool_create_jira_issue() -> str:
    """Create a Jira issue using User Input"""
    return None


@tool("view_backlog", return_direct=True, args_schema=ViewBacklogRequest)
def tool_view_backlog() -> str:
    """View Backlog Issues using User Input"""
    return view_backlog()


@tool("get_my_issues", return_direct=True, args_schema=GetMyIssues)
def tool_get_my_issues() -> str:
    """View User Jira Issues using User Input"""
    return None


@tool("Sprint_Issues", return_direct=True, args_schema=SprintIssues)
def tool_Sprint_Issues() -> str:
    """View Sprint Issues using User Input"""
    return None


@tool(
    "jenkins_pipeline_configuration",
    return_direct=True,
    args_schema=JenkinsRegisterRequest,
)
def tool_jenkins_pipeline_config() -> str:
    """Register Jenkins using User Input"""
    return None


@tool("run_jenkins_pipeline", return_direct=True, args_schema=RunJenkinsPipelineRequest)
def tool_run_jenkins_pipeline() -> str:
    """Run Jenkins Pipeline using User Input"""
    return None


@tool("github_code_search", return_direct=True, args_schema=GitHubSearchRequest)
def tool_github_code_search() -> str:
    """Search for code in GitHub using User Input"""
    return None


@tool
def converse(input: str) -> str:
    "Provide a natural language response using the user input."
    return model.invoke(input)


tools = [
    tool_sprint_report,
    tool_velocity_report,
    tool_daily_scrum_report,
    tool_register_project,
    tool_switch_jira_project,
    tool_create_jira_issue,
    tool_view_backlog,
    tool_get_my_issues,
    tool_Sprint_Issues,
    tool_jenkins_pipeline_config,
    tool_run_jenkins_pipeline,
    tool_github_code_search,
    tool_sprint_report,
    tool_restart_app,
    tool_jira_burn_up_report,
    tool_burn_down_report,
    tool_get_issues_details,
    converse,
]

# Configure the system prompts
rendered_tools = render_text_description(tools)

system_prompt = f"""You are an assistant that has access to the following set of tools.
Here are the names and descriptions for each tool:
{rendered_tools}
Given the user input, return the name and input of the tool to use.
Return your response as a JSON blob with 'name'.
The value associated with the 'arguments' key should be a dictionary of parameters."""

prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompt), ("user", "{input}")]
)


# Define a function which returns the chosen tool name based on user input.
def tool_get_tool_name(model_output):
    tool_map = {tool.name: tool for tool in tools}
    chosen_tool = tool_map.get(model_output.get("name"))
    return chosen_tool.name if chosen_tool else None


# Define a function which returns the chosen tool to be run as part of the chain.
def tool_chain(model_output):
    logger.info(f"Model output: {model_output}")
    tool_map = {tool.name: tool for tool in tools}
    chosen_tool = tool_map.get(model_output.get("name"))
    logger.info(f"Chosen tool: {chosen_tool}")
    return itemgetter("arguments") | chosen_tool if chosen_tool else None


# The main chain: an LLM with tools.
chain_tool_name = prompt | model | JsonOutputParser() | tool_get_tool_name


def display_switch_project_in_sidebar(user_name):

    if not st.session_state.form_submitted:
        with st.form(key="change_project_form"):
            project_data = switch_project_to_other_project(user_name)
            logger.info(f"Project data: {project_data}")
            if project_data == "No Project Found":
                st.session_state.messages.append(
                    {
                        "role": "bot",
                        "content": f"No project found. Please register a project first",
                    }
                )
                st.session_state.form_submitted = False
                st.session_state.show_dropdown = False
                st.experimental_rerun()  # Rerun to update the chat interface
            else:
                dropdown_values = project_data[0]
                logger.info(f"Dropdown values: {dropdown_values}")
                selected_value = st.selectbox("Select Project:", dropdown_values)

                logger.info(f"Selected value: {selected_value}")
                # if selected_value == project_data[1]:
                #     st.session_state.messages.append(
                #         {
                #             "role": "bot",
                #             "content": f"Selected project is already the primary project",
                #         }
                #     )
                #     st.session_state.form_submitted = False
                #     st.session_state.show_dropdown = False
                #     st.experimental_rerun()
                # else:
                submit_button = st.form_submit_button(label="Submit")
                if submit_button:
                    updating_primary_project(user_name, selected_value)
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": f"Updated Primary Project as {selected_value}",
                        }
                    )
                    st.session_state.form_submitted = False
                    st.session_state.show_dropdown = False
                    st.experimental_rerun()
                # else:
                #     st.session_state.form_submitted = False
                #     st.session_state.show_dropdown = False
                #     st.experimental_rerun()


def display_register_form():
    if not st.session_state.form_submitted:
        with st.form(key="register_jira_project_form"):
            project_url = st.text_input("Backlog URL")
            submit_button = st.form_submit_button(label="Submit")
            if submit_button:
                st.write("it will take some time to register the project Please wait!")
                res = project_registartion(project_url, user_name)
                logger.info(f"res{res}")
                if res["success"] == False or res["success"] == "False":
                    data_res = res["data"]
                    logger.info(f"data_res{data_res}")
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": data_res,
                        }
                    )
                    st.session_state.form_submitted = False
                    st.session_state.show_form = False
                    st.experimental_rerun()
                else:
                    st.write("Project Registered Successfully")
                    data_res = res["data"]
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": data_res,
                        }
                    )
                    # Reset form state
                    st.session_state.form_submitted = False
                    st.session_state.show_form = False
                    st.experimental_rerun()


def jenkins_register_form():
    if not st.session_state.form_submitted:
        with st.form(key="register_jenkins_pipeline_form"):
            pipeline_name = st.text_input("Pipeline name")
            jenkins_url = st.text_input("Jenkins URL")
            submit_button = st.form_submit_button(label="Submit")
            if submit_button:
                data = db.ice_user_data.find(
                    {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
                )
                for record in data:
                    if not record["my_primary_projects"]:
                        st.write(
                            "No primary project found Please Register a project first"
                        )
                    else:
                        my_primary_project = record["my_primary_projects"]
                    res = jenkins_register(
                        pipeline_name, jenkins_url, my_primary_project
                    )
                    logger.info(f"res{res}")
                    data_res = res["data"]
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": data_res,
                        }
                    )
                    # Reset form state
                    st.session_state.form_submitted = False
                    st.session_state.show_jenkins_form = False
                    st.experimental_rerun()


def code_search_form():
    if not st.session_state.form_submitted:
        with st.form(key="git_code_search_form"):
            key_word = st.text_input("enter key word to search")
            extendtion = st.text_input("enter extension to search eg. .py,.java")
            submit_button = st.form_submit_button(label="Submit")
            if submit_button:
                logger.info(f"key_word{key_word}")
                logger.info(f"extendtion{extendtion}")
                data = search_code_in_github(key_word, extendtion)
                logger.info(f"res{data}")
                if isinstance(data, str):
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": data,
                        }
                    )
                    # Reset form state
                    st.session_state.form_submitted = False
                    st.session_state.show_git_hub_form = False
                    st.experimental_rerun()
                else:
                    strs = f"Following are the results of {key_word} from git hub."
                    for i in data:
                        strs += i + "\n\n"
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": strs,
                        }
                    )
                    # Reset form state
                    st.session_state.form_submitted = False
                    st.session_state.show_git_hub_form = False
                    st.experimental_rerun()


def get_my_issue_form():
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            st.session_state.messages.append(
                {
                    "role": "bot",
                    "content": "No Primary Project found Please Register a Project First",
                }
            )
            st.session_state.form_submitted = False
            st.session_state.show_my_issue_form = False
            st.experimental_rerun()
        else:
            my_primary_project = record["my_primary_projects"]
    data = get_my_issues()
    fileter_data = filter_by_assignee(data, email)
    if len(fileter_data) == 0:
        if not st.session_state.form_submitted:
            with st.form(key="issue's update form"):
                logger.info("No User Stories Found")
                st.session_state.messages.append(
                    {
                        "role": "bot",
                        "content": "No User Stories Found",
                    }
                )
                st.session_state.form_submitted = False
                st.session_state.show_my_issue_form = False
                st.experimental_rerun()
    else:
        # Dictionaries to store user inputs
        comments = {}
        hours = {}
        if not st.session_state.form_submitted:
            with st.form(key="issue's update form"):
                st.write("My User Stories")
                # Display user stories and input fields
                for k, v in fileter_data.items():
                    st.markdown(
                        f"<span style='color: black;'>User Story ID: </span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: blue;'>{k}</span>", unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<span style='color: black;'>Issue Type: </span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: blue;'>{v['Issue_Type']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: black;'>User Story Summary: </span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: blue;'>{v['Summary']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.write("User Story Description : ")
                    st.markdown(
                        f"<span style='color: green;'>{v['Description']}</span>",
                        unsafe_allow_html=True,
                    )
                    comments[k] = st.text_input(
                        f"Worklog Comment for {k}", placeholder="Add Worklog Comment"
                    )
                    hours[k] = st.text_input(
                        f"Worklog Hours for {k}",
                        placeholder="Add Worklog Duration(e.g. 2h 30m)",
                    )
                    # Process inputs when the Submit button is clicked
                submit_button = st.form_submit_button(label="Submit")
                if submit_button:
                    combined_dict = {}
                    # Iterate through the keys of the first dictionary
                    for key in comments:
                        # Combine the values from both dictionaries
                        if comments[key] and hours[key]:
                            combined_value = comments[key] + ":" + hours[key]
                        else:
                            combined_value = comments[key] + hours[key]
                        # Add the combined value to the new dictionary
                        combined_dict[key] = combined_value
                    filtered_dict = {
                        key: value for key, value in combined_dict.items() if value
                    }
                    for k, v in filtered_dict.items():
                        issue_key = k
                        comment = v.split(":")[0]
                        Worklog_hour = v.split(":")[1]
                        Worklog_hour = time_to_seconds(Worklog_hour)
                        logger.info(f"issue_key{issue_key}")
                        logger.info(f"comment{comment}")
                        logger.info(f"Worklog_hour{Worklog_hour}")
                        url = "http://{0}:{1}/jiraapi/update_jira_issues/".format(
                            SERVER_IP, PORT
                        )
                        payload = {
                            "project_name": my_primary_project,
                            "user_name": user_name,
                            "issue_key": issue_key,
                            "comment": comment,
                            "worklog_comment": " ",
                            "worklog_duration": Worklog_hour,
                        }
                        response = requests.request("POST", url, data=payload)
                        logger.info(f"response from{response.text}")
                        data_dict = json.loads(response.text)
                        if (
                            data_dict["success"] == "true"
                            or data_dict["success"] == True
                        ):
                            st.session_state.messages.append(
                                {
                                    "role": "bot",
                                    "content": " {0} updated successfully".format(
                                        issue_key
                                    ),
                                }
                            )
                        else:
                            st.session_state.messages.append(
                                {
                                    "role": "bot",
                                    "content": " {0} Not updated successfully".format(
                                        issue_key
                                    ),
                                }
                            )
                        st.session_state.form_submitted = False
                        st.session_state.show_my_issue_form = False
                        st.experimental_rerun()
                # else:
                #     time.sleep(20)
                #     st.session_state.show_my_issue_form = False
                #     st.experimental_rerun()


def sprint_issue_form():
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            st.session_state.messages.append(
                {
                    "role": "bot",
                    "content": "No Primary Project found Please Register a Project First",
                }
            )
            st.session_state.form_submitted = False
            st.session_state.show_sprint_issues = False
            st.experimental_rerun()
        else:
            my_primary_project = record["my_primary_projects"]
    data = get_my_issues()
    if len(data) == 0:
        if not st.session_state.form_submitted:
            with st.form(key="sprint issue's update form"):
                st.session_state.messages.append(
                    {
                        "role": "bot",
                        "content": "No User Stories Found",
                    }
                )
                st.session_state.form_submitted = False
                st.session_state.show_sprint_issues = False
                st.experimental_rerun()
    else:
        # Dictionaries to store user inputs
        comments = {}
        hours = {}
        if not st.session_state.form_submitted:
            with st.form(key="sprint issues update form"):
                st.write("Sprint User Stories")
                # Display user stories and input fields
                for k, v in data.items():
                    st.markdown(
                        f"<span style='color: black;'>User Story ID: </span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: blue;'>{k}</span>", unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<span style='color: black;'>Issue Type: </span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: blue;'>{v['Issue_Type']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: black;'>User Story Summary: </span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color: blue;'>{v['Summary']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.write("User Story Description : ")
                    st.markdown(
                        f"<span style='color: green;'>{v['Description']}</span>",
                        unsafe_allow_html=True,
                    )
                    comments[k] = st.text_input(
                        f"Worklog Comment for {k}", placeholder="Add Worklog Comment"
                    )
                    hours[k] = st.text_input(
                        f"Worklog Hours for {k}",
                        placeholder="Add Worklog Duration(e.g. 2h 30m)",
                    )
                    # Process inputs when the Submit button is clicked
                submit_button = st.form_submit_button(label="Submit")
                if submit_button:
                    combined_dict = {}
                    # Iterate through the keys of the first dictionary
                    for key in comments:
                        # Combine the values from both dictionaries
                        if comments[key] and hours[key]:
                            combined_value = comments[key] + ":" + hours[key]
                        else:
                            combined_value = comments[key] + hours[key]
                        # Add the combined value to the new dictionary
                        combined_dict[key] = combined_value
                    filtered_dict = {
                        key: value for key, value in combined_dict.items() if value
                    }
                    for k, v in filtered_dict.items():
                        issue_key = k
                        comment = v.split(":")[0]
                        Worklog_hour = v.split(":")[1]
                        Worklog_hour = time_to_seconds(Worklog_hour)
                        logger.info(f"issue_key{issue_key}")
                        logger.info(f"comment{comment}")
                        logger.info(f"Worklog_hour{Worklog_hour}")
                        url = "http://{0}:{1}/jiraapi/update_jira_issues/".format(
                            SERVER_IP, PORT
                        )
                        payload = {
                            "project_name": my_primary_project,
                            "user_name": user_name,
                            "issue_key": issue_key,
                            "comment": comment,
                            "worklog_comment": " ",
                            "worklog_duration": Worklog_hour,
                        }
                        response = requests.request("POST", url, data=payload)
                        logger.info(f"response from{response.text}")
                        data_dict = json.loads(response.text)
                        if (
                            data_dict["success"] == "true"
                            or data_dict["success"] == True
                        ):
                            st.session_state.messages.append(
                                {
                                    "role": "bot",
                                    "content": " {0} updated successfully".format(
                                        issue_key
                                    ),
                                }
                            )
                        else:
                            st.session_state.messages.append(
                                {
                                    "role": "bot",
                                    "content": " {0} Not updated successfully".format(
                                        issue_key
                                    ),
                                }
                            )
                        st.session_state.form_submitted = False
                        st.session_state.show_sprint_issues = False
                        st.experimental_rerun()
                # else:
                #     time.sleep(20)
                #     st.session_state.form_submitted = False
                #     st.session_state.show_sprint_issues = False
                #     st.experimental_rerun()


def issue_creation_form():
    if not st.session_state.form_submitted:
        with st.form(key="create_jira_issue_form"):
            issue_summary = st.text_input("Issue Summary")
            issue_desc = st.text_area("Issue Description")
            acceptance_criteria = st.text_area("Acceptance Criteria")
            try:
                data = get_epic(user_name)
                if None in data:
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": data[1],
                        }
                    )
                    st.session_state.form_submitted = False
                    st.session_state.show_issue_form = False
                    st.experimental_rerun()
                else:
                    epic_key, epic_data = get_epic(user_name)
                    logger.info(f"epic_data{epic_data}")
                    logger.info(f"epic_key{epic_key}")
                    issue_type = st.selectbox(
                        "Issue Type",
                        ["Task", "Story", "Bug"],
                    )
                    if len(epic_data) == 0 and len(epic_key) == 0:
                        epic_key = st.selectbox(
                            "Epic Key",
                            ["No Epic Found", "No Epic Found"],
                        )
                    else:
                        epic_key = st.selectbox("Epic Key", epic_key)
                        epic_key = epic_data[epic_key]
                    submit_button = st.form_submit_button(label="Submit")
                    if submit_button:
                        logger.info(f"{epic_key}{issue_type}")
                        res = issue_creation_function(
                            user_name,
                            issue_summary,
                            issue_desc,
                            acceptance_criteria,
                            issue_type,
                            epic_key,
                        )
                        logger.info(f"res{res}")
                        st.session_state.messages.append(
                            {
                                "role": "bot",
                                "content": f"Issues created successfully find the link :{res}",
                            }
                        )
                        st.session_state.form_submitted = False
                        st.session_state.show_issue_form = False
                        # issue_creation_form()
                        st.experimental_rerun()

            except Exception as e:
                logger.error(f"Error in issue_creation_form: {e}")
                st.session_state.messages.append(
                    {
                        "role": "bot",
                        "content": "No Epic Found",
                    }
                )
                st.session_state.form_submitted = False
                st.session_state.show_issue_form = False
                st.experimental_rerun()


def run_jenkins_form():
    if not st.session_state.form_submitted:
        with st.form(key="run_jenkins_form"):
            branch = st.text_input("Git Branch")
            issue_id = st.text_input("Jira Issue")
            build_name = get_jenkins_build_name(user_name)
            if build_name == None:
                selected_build_name = st.selectbox(
                    "Pipeline name",
                    ["Register Jenkins Pipeline First"],
                )
            else:
                selected_build_name = st.selectbox("Pipeline name", build_name)
            submit_button = st.form_submit_button(label="Submit")
            if submit_button:
                logger.info(f"branch{branch}")
                logger.info(f"selected_build_name{selected_build_name}")
                res = jenkins_build_ai_analysis(branch, selected_build_name, user_name)
                logger.info(f"res{res}")
                if res["log"] == None:
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": res["data"],
                        }
                    )
                    st.session_state.form_submitted = False
                    st.session_state.show_run_jenkins_form = False
                    st.experimental_rerun()
                else:
                    if issue_id != None:
                        comment = res["log"]
                        issues_res = add_comment(comment, issue_id)
                        st.session_state.messages.append(
                            {
                                "role": "bot",
                                "content": "GenAI Result :"
                                + res["log"]
                                + "\n\n"
                                + issues_res
                                + "\n\n"
                                + "jenkins Console:"
                                + res["data"],
                            }
                        )
                        st.session_state.form_submitted = False
                        st.session_state.show_run_jenkins_form = False
                        st.experimental_rerun()
                    else:
                        st.session_state.messages.append(
                            {
                                "role": "bot",
                                "content": "GenAI Result :"
                                + res["log"]
                                + "\n\n"
                                + "jenkins Console:"
                                + res["data"],
                            }
                        )
                        st.session_state.form_submitted = False
                        st.session_state.show_run_jenkins_form = False
                        st.experimental_rerun()


_data = {
    "IT-6": [
        {"issue_summary": "Testing with drop downs"},
        {"updated_date": {}},
        {"story_points": None},
    ],
    "IT-5": [
        {"issue_summary": "Stream li form testing"},
        {"updated_date": {}},
        {"story_points": None},
    ],
    "IT-1": [
        {"issue_summary": "Testing Jira features"},
        {
            "updated_date": {
                "2024-09-17T13:16:48.985+0530": "2h",
                "2024-09-18T01:31:17.198+0530": "3h",
                "2024-09-18T09:52:10.297+0530": "2h",
                "2024-09-25T01:13:56.007+0530": "2h",
                "2024-09-26T00:50:04.807+0530": "2h",
                "2024-09-26T01:21:43.070+0530": "1h",
                "2024-09-29T21:37:34.621+0530": "1h",
                "2024-09-30T21:45:49.213+0530": "3d",
                "2024-10-01T13:37:21.271+0530": "2h",
                "2024-10-01T15:05:51.177+0530": "6h",
                "2024-10-01T16:05:27.566+0530": "3h",
            }
        },
        {"story_points": 2.0},
    ],
    "sprint_name": "IT Sprint 4",
    "startDate": "2024-10-27",
    "endDate": "2024-11-10",
}


def get_issue_details_form():
    if not st.session_state.form_submitted:
        with st.form(key="get_issue_details_form"):
            issue_key = st.text_input("Issue Key")
            submit_button = st.form_submit_button(label="Submit")
            if submit_button:
                res = get_issue_details(issue_key)
                if isinstance(res, list):
                    if res[0] == "None":
                        st.session_state.messages.append(
                            {
                                "role": "bot",
                                "content": res[1],
                            }
                        )
                        st.session_state.form_submitted = False
                        st.session_state.show_get_issue_details_form = False
                        st.experimental_rerun()
                elif isinstance(res, dict):
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": res,
                        }
                    )
                    st.session_state.form_submitted = False
                    st.session_state.show_get_issue_details_form = False
                    st.experimental_rerun()
                else:
                    st.session_state.messages.append(
                        {
                            "role": "bot",
                            "content": res,
                        }
                    )
                    st.session_state.form_submitted = False
                    st.session_state.show_get_issue_details_form = False
                    st.experimental_rerun()


chain_tool_name = prompt | model | JsonOutputParser() | tool_get_tool_name


# The main chain: an LLM with tools.
chain = prompt | model | JsonOutputParser() | tool_chain


def display_velocity_chart():
    logger.info("===================its going into the velocity data function====")
    """ Velcority Report Table View """
    velocity_data = get_velocity_report()
    if velocity_data:
        st.write("Velocity report generated successfully.")
    else:
        st.error("Failed to generate velocity report.")


velocitySampleData = {
    "IT Sprint 2": {
        "Sprint_Goal": "",
        "Completed_Issues_Story_Points": 3.0,
        "Estimated_Story_Points": 5.0,
        "Issues in Sprint": ["IT-5", "IT-6", "IT-1"],
    },
    "IT Sprint 1": {
        "Sprint_Goal": "",
        "Completed_Issues_Story_Points": 4.0,
        "Estimated_Story_Points": 6.0,
        "Issues in Sprint": ["IT-1"],
    },
}


def get_velocity_report():
    """Get the Jira Velocity Report"""
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/velocityreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return "No primary project found Please Register a project first"
            logger.error("No primary project found Please Register a project first")
        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.json()["data"] != "Authnication Failed":
        velocity_data = response.json()["data"]
        velocity_df = process_velocity_data(velocity_data)

        # Display the data as a table
        st.dataframe(velocity_df)
        # data = velocity_report(velocity_data)
        # Create the bar chart using Plotly
        fig = px.bar(
            velocity_df,
            x="Sprint",
            y=["Completed_Story_Points", "Estimated_Story_Points"],
            title="Sprint Velocity (Completed vs Estimated Story Points)",
            labels={"value": "Story Points", "Sprint": "Sprint"},
            barmode="group",
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        return velocity_data
        # logger.info(f"velocity data======+++++++++++++++++++++++++++++++++++{data}")
    else:
        return "Authentication Failed"


# def display_burndown_chart():
#     logger.info("=====coming in burndown=====")

#     url = f"http://{SERVER_IP}:{PORT}/jiraapi/burndownreport/"
#     data = db.ice_user_data.find(
#         {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
#     )
#     for record in data:
#         if not record["my_primary_projects"]:
#             logger.error("No primary project found Please Register a project first")
#             return "No primary project found Please Register a project first"
#         else:
#             my_primary_project = record["my_primary_projects"]
#     payload = json.dumps(
#         {
#             "project_name": my_primary_project,
#             "user_name": user_name,
#         }
#     )
#     headers = {"Content-Type": "application/json"}
#     response = requests.request("POST", url, headers=headers, data=payload)
#     report_data = response.json()
#     logger.info("=====full data=====", response.json())
#     logger.info("=====link data=====", report_data["report_url"])

#     if report_data["success"]:
#         data = report_data["data"]

#         # Display the chart
#         st.subheader(f"Burndown Chart - {data['sprint_name']}")

#         df = generate_burndown_data(data)
#         fig = px.line(
#             df,
#             x="Date",
#             y=["Ideal Burndown", "Actual Burndown"],
#             markers=True,
#             title="Burndown Chart",
#             labels={"value": "Story Points", "Date": "Sprint Day"},
#             template="plotly_dark",
#         )
#         st.plotly_chart(fig)
#         display_table_view(data)
#         # Display the report URL as a clickable link
#         report_url = report_data["report_url"]
#         st.markdown(f"[View Full Report Here]({report_url})", unsafe_allow_html=True)
#         st.write("Burndown report generated successfully.")
#         # return data
#     else:
#         st.error("Failed to fetch the burndown report data.")

# def generate_burndown_data(data):
#     start_date = datetime.datetime.fromisoformat(data["startDate"])
#     end_date = datetime.datetime.fromisoformat(data["endDate"])
#     total_days = (end_date - start_date).days

#     # Calculate total story points
#     total_story_points = sum(
#         issue[2]["story_points"]
#         for issue in data.values()
#         if isinstance(issue, list) and issue[2]["story_points"] is not None
#     )

#     # Generate ideal burndown points
#     ideal_burndown = [
#         total_story_points - (i * (total_story_points / total_days))
#         for i in range(total_days + 1)
#     ]

#     # Simulate actual burndown (for demonstration, using a simple linear drop)
#     actual_burndown = [
#         total_story_points - (i * (total_story_points / total_days * 0.9))
#         for i in range(total_days + 1)
#     ]

#     # Create a DataFrame for the chart
#     dates = [start_date + datetime.timedelta(days=i) for i in range(total_days + 1)]
#     df = pd.DataFrame(
#         {
#             "Date": dates,
#             "Ideal Burndown": ideal_burndown,
#             "Actual Burndown": actual_burndown,
#         }
#     )
#     return df


# def display_table_view(data):
#     # Display the table
#     st.subheader("Burndown Table View")
#     table_data = []
#     for key, value in data.items():
#         if isinstance(value, list):
#             issue_summary = value[0]["issue_summary"]

#             # Extract updated dates and format them with hours in brackets
#             updated_dates = value[1]["updated_date"]
#             if updated_dates:
#                 formatted_dates = ", ".join(
#                     [
#                         f"{datetime.datetime.fromisoformat(date.split('.')[0]).strftime('%Y-%m-%d')} ({hours})"
#                         for date, hours in updated_dates.items()
#                     ]
#                 )
#             else:
#                 formatted_dates = "N/A"

#             story_points = value[2]["story_points"]
#             table_data.append([key, issue_summary, formatted_dates, story_points])

#     # Create a DataFrame for the table
#     df_table = pd.DataFrame(
#         table_data,
#         columns=["Issue ID", "Issue Summary", "Updated Date", "Story Points"],
#     )
#     df_table.index = df_table.index + 1
#     st.table(df_table)


def display_burndown_chart_and_table():
    st.title("Burndown Chart")

    # Define URL and fetch user's primary project
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/burndownreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )

    my_primary_project = None
    for record in data:
        my_primary_project = record.get("my_primary_projects")
        if not my_primary_project:
            st.error("No primary project found. Please register a project first.")
            return

    # Prepare and send request
    payload = json.dumps({"project_name": my_primary_project, "user_name": user_name})
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        st.error("Failed to fetch the burndown report.")
        return

    try:
        burndown_data = response.json()
        logger.info("Burndown report data received: %s", burndown_data)
    except ValueError:
        st.error("Failed to decode the response.")
        return

    # Validate response data
    if not burndown_data.get("success"):
        st.error("Authentication failed or invalid response.")
        return

    data = burndown_data.get("data")
    report_url = burndown_data.get("report_url")

    if not data:
        st.error("No data available for the burndown report.")
        return

    # Display the chart
    st.subheader(f"Burndown Chart - {data['sprint_name']}")

    df = generate_burndown_data(data)
    fig = px.line(
        df,
        x="Date",
        y=["Ideal Burndown", "Actual Burndown"],
        markers=True,
        title=f"Burndown Chart - {data['sprint_name']}",
        labels={"value": "Story Points", "Date": "Sprint Day"},
        template="plotly_dark",
    )
    st.plotly_chart(fig)

    # Display the table
    st.subheader("Burndown Table View")
    table_data = []
    for key, value in data.items():
        if isinstance(value, list):
            issue_summary = value[0].get("issue_summary", "N/A")
            updated_date = value[1].get("updated_date", "N/A")
            story_points = value[2].get("story_points", "N/A")

            formatted_dates = (
                ", ".join(
                    [
                        f"{datetime.datetime.fromisoformat(date.split('.')[0]).strftime('%Y-%m-%d')} ({hours})"
                        for date, hours in updated_date.items()
                    ]
                )
                if updated_date != "N/A"
                else "N/A"
            )

            table_data.append([key, issue_summary, formatted_dates, story_points])

    df_table = pd.DataFrame(
        table_data,
        columns=["Issue ID", "Issue Summary", "Updated Date", "Story Points"],
    )
    df_table.index = df_table.index + 1
    st.table(df_table)

    # Display the report link
    if report_url:
        st.markdown(
            f"[View full burndown Report Here]({report_url})", unsafe_allow_html=True
        )


def generate_burnup_chart(data):
    start_date = datetime.datetime.strptime(data["startDate"], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(data["endDate"], "%Y-%m-%d")

    # Generate a date range for the sprint
    date_range = pd.date_range(start=start_date, end=end_date)

    # Calculate cumulative story points completed
    total_story_points = sum(
        item[2]["story_points"] or 0 for item in data.values() if isinstance(item, list)
    )
    completed_points = [0]  # Start with zero completed
    cumulative_points = 0

    for current_date in date_range:
        for key, value in data.items():
            if isinstance(value, list) and value[1]["closed_date"]:
                closed_date = datetime.datetime.strptime(
                    value[1]["closed_date"], "%Y-%m-%d"
                )
                if closed_date <= current_date:
                    cumulative_points += value[2]["story_points"] or 0
        completed_points.append(cumulative_points)

    # Total work scope is constant
    total_scope = [total_story_points] * len(date_range)

    # Burnup DataFrame
    df = pd.DataFrame(
        {
            "Date": date_range,
            "Work Completed": completed_points[:-1],  # Exclude extra point
            "Total Scope": total_scope,
        }
    )
    return df


def display_burnup_chart_and_table():
    st.title("Burnup Chart")

    # Define URL and fetch user's primary project
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/burnupreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )

    my_primary_project = None
    for record in data:
        my_primary_project = record.get("my_primary_projects")
        if not my_primary_project:
            st.error("No primary project found. Please register a project first.")
            return

    # Prepare and send request
    payload = json.dumps({"project_name": my_primary_project, "user_name": user_name})
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        st.error("Failed to fetch the burnup report.")
        return

    try:
        burn_up_data = response.json()
        logger.info("Burnup report data received: %s", burn_up_data)
    except ValueError:
        st.error("Failed to decode the response.")
        return

    # Validate response data
    if not burn_up_data.get("success"):
        st.error("Authentication failed or invalid response.")
        return

    data = burn_up_data.get("data")
    report_url = burn_up_data.get("report_url")

    if not data:
        st.error("No data available for the burnup report.")
        return

    # Display the chart
    st.subheader(f"Burnup Chart - {data['sprint_name']}")

    df = generate_burnup_chart(data)
    fig = px.line(
        df,
        x="Date",
        y=["Work Completed", "Total Scope"],
        markers=True,
        title=f"Burnup Chart - {data['sprint_name']}",
        labels={"value": "Story Points", "Date": "Sprint Day"},
        template="plotly_dark",
    )
    st.plotly_chart(fig)

    # Display the table
    st.subheader("Burnup Table View")
    table_data = []
    for key, value in data.items():
        if isinstance(value, list):
            issue_summary = value[0].get("issue_summary", "N/A")
            closed_date = value[1].get("closed_date", "N/A")
            story_points = value[2].get("story_points", "N/A")
            table_data.append([key, issue_summary, closed_date, story_points])

    df_table = pd.DataFrame(
        table_data, columns=["Issue ID", "Issue Summary", "Closed Date", "Story Points"]
    )
    df_table.index = df_table.index + 1
    st.table(df_table)

    # Display the report link
    if report_url:
        st.markdown(
            f"[View full burnup Report Here]({report_url})", unsafe_allow_html=True
        )

    # Display the report link
    # st.markdown(f"[View Full Report Here]({report_url})", unsafe_allow_html=True)


def main():
    st.markdown(
        '<h4 class="title">Welcome to iCE (intelligent Copilot Engine)</h4>',
        unsafe_allow_html=True,
    )
    # Initialize session state for chat history and form submission
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "project_name" not in st.session_state:
        st.session_state.project_name = ""
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "show_form" not in st.session_state:
        st.session_state.show_form = False
    if "first_message" not in st.session_state:
        st.session_state.first_message = True
    if "show_dropdown" not in st.session_state:
        st.session_state.show_dropdown = False
    if "dropdown_submitted" not in st.session_state:
        st.session_state.dropdown_submitted = False
    if "show_issue_form" not in st.session_state:
        st.session_state.show_issue_form = False
    if "show_my_issue_form" not in st.session_state:
        st.session_state.show_my_issue_form = False
    if "show_sprint_issues" not in st.session_state:
        st.session_state.show_sprint_issues = False
    if "show_jenkins_form" not in st.session_state:
        st.session_state.show_jenkins_form = False
    if "show_run_jenkins_form" not in st.session_state:
        st.session_state.show_run_jenkins_form = False
    if "show_git_hub_form" not in st.session_state:
        st.session_state.show_git_hub_form = False
    if "show_get_issue_details_form" not in st.session_state:
        st.session_state.show_get_issue_details_form = False

    # Display chat interface
    # st.subheader("Chat with iCE Bot")

    # Create a chat input for user input
    user_input = st.chat_input("Enter a prompt here")

    # Handle user input
    if user_input:
        handle_user_input(user_input, user_name, email)

    # BASE_DIR = Path(__file__).parent
    # image_url = str(BASE_DIR / "iconimg.png")
    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="user-message-container" style="display: flex; justify-content: flex-end;">
                    <p class="user-message">{msg["content"]}</p>
                    <span style="margin-left: 10px;">{user_icon}</span>
                </div>
                <div class="clearfix"></div>
                """,
                unsafe_allow_html=True,
            )
        else:
            if "Here is your velocity report." in msg["content"]:
                # Generate and display the velocity chart
                display_velocity_chart()
            if "Here is your burndown report." in msg["content"]:
                # Generate and display the burndown chart
                display_burndown_chart_and_table()
            if "Here is your burnup report." in msg["content"]:
                # Generate and display the burnup chart
                display_burnup_chart_and_table()
            if "Here is your sprint report." in msg["content"]:
                # Generate and display the sprint chart
                get_sprint_report()
            if "Here is your scrum report." in msg["content"]:
                # Generate and display the scrum chart
                get_daily_scrum_report()
            # Handle bot messages or other responses
            if isinstance(msg["content"], dict):
                formatted_content = str(msg["content"])
            elif isinstance(msg["content"], str):
                formatted_content = msg["content"].replace("\n", "<br>")
            else:
                formatted_content = ""
            if formatted_content.strip():
                st.markdown(
                    f"""
                    <div class="bot-message-container" style="display: flex; justify-content: flex-start;">
                        <span style="margin-right: 10px;">{bot_icon}</span>
                        <p class="bot-message">{formatted_content}</p>
                    </div>
                    <div class="clearfix"></div>
                    """,
                    unsafe_allow_html=True,
                )

    # Display form in sidebar if requested
    if st.session_state.show_form:
        display_register_form()

    # Display dropdown in sidebar if requested
    if st.session_state.show_dropdown:
        display_switch_project_in_sidebar(user_name)

    # Display issue creation form if requested
    if st.session_state.show_issue_form:
        issue_creation_form()

    # Display my issue form if requested
    if st.session_state.show_my_issue_form:
        get_my_issue_form()

    if st.session_state.show_sprint_issues:
        sprint_issue_form()

    if st.session_state.show_jenkins_form:
        jenkins_register_form()

    if st.session_state.show_run_jenkins_form:
        run_jenkins_form()
    if st.session_state.show_git_hub_form:
        code_search_form()
    if st.session_state.show_get_issue_details_form:
        get_issue_details_form()


def process_user_input(user_input):
    # Define responses and form types for each feature
    try:
        # Get the chosen tool name based on user input.
        choosen_tool = chain_tool_name.invoke({"input": user_input})
        logger.info(f"Chosen tool: {choosen_tool}")
        # The main chain: an LLM with tools.

        if choosen_tool == "register_project":
            return (
                "Please complete the form to register new Jira project.",
                "register_jira_project",
                False,
            )
        elif choosen_tool == "switch_jira_project":
            return (
                "Please select a project from the dropdown menu ",
                "change_project_form",
                False,
            )
        elif choosen_tool == "create_jira_issue":
            return (
                "Please complete the form to create a new Jira issue.",
                "create_jira_issue",
                False,
            )
        elif choosen_tool == "get_my_issues":
            return (
                "View User issues in the below form",
                "get_my_issues",
                False,
            )
        elif choosen_tool == "Sprint_Issues":
            return (
                "View all sprint issues in the below form",
                "Sprint_Issues",
                False,
            )
        elif choosen_tool == "jenkins_pipeline_configuration":
            return (
                "Please complete the form to register Jenkins",
                "jenkins_pipeline_configuration",
                False,
            )

        elif choosen_tool == "run_jenkins_pipeline":
            return (
                "Please complete the form to run Jenkins Pipeline",
                "run_jenkins_pipeline",
                False,
            )

        elif choosen_tool == "github_code_search":
            return (
                "Please complete the form to search code in GitHub",
                "github_code_search",
                False,
            )
        elif choosen_tool == "get_issues_details":
            return (
                "Please complete the form to get issue details",
                "get_issue_details",
                False,
            )

        elif choosen_tool == "velocity_report":
            return (
                "Here is your velocity report.",
                None,
                False,
            )
        elif choosen_tool == "burn_down_report":
            return (
                "Here is your burndown report.",
                None,
                False,
            )
        elif choosen_tool == "burn_up_report":
            return (
                "Here is your burnup report.",
                None,
                False,
            )
        elif choosen_tool == "sprint_report":
            return (
                "Here is your sprint report.",
                None,
                False,
            )
        elif choosen_tool == "scrum_report":
            return (
                "Here is your scrum report.",
                None,
                False,
            )
        else:
            # Invoke chain to get response.
            logger.info(f"input{user_input}")
            response = chain.invoke({"input": user_input})
            logger.info(f"response{response}")
            return response, None, False
    except Exception as e:
        logger.error(f"Error in process_user_input: {e}")
        return (
            "Sorry, I am unable to process your request. Please try again.",
            None,
            False,
        )


def display_basic_form():
    with st.form(key="basic_form"):
        user_name = st.text_input("Enter your name")
        user_email = st.text_input("Enter your email")
        issue_type = st.selectbox("Issue Type", ["Bug", "Feature Request", "Other"])
        issue_description = st.text_area("Describe the issue")

        # Submit button
        submit_button = st.form_submit_button(label="Submit")

    if submit_button:
        # Process the form submission
        st.write(f"Name: {user_name}")
        st.write(f"Email: {user_email}")
        st.write(f"Issue Type: {issue_type}")
        st.write(f"Issue Description: {issue_description}")
        st.success("Form submitted successfully!")


def handle_user_input(user_input, user_name, email):
    if st.session_state.first_message:
        insert_data_into_mongodb(user_name, email)
        st.session_state.first_message = False
    st.session_state.messages.append({"role": "user", "content": user_input})
    bot_response, form_type, show_dropdown = process_user_input(user_input)
    logger.info(f"bot response {bot_response}")
    st.session_state.messages.append(
        {
            "role": "bot",
            "content": bot_response,
        }
    )
    # Render the corresponding charts or tables for specific tools
    # if bot_response == "Here is your velocity report.":
    #     get_velocity_report()
    # elif bot_response == "Here is your burndown chart.":
    #     display_burndown_chart()
    # elif bot_response == "Here is your burnup chart and table.":
    #     display_burnup_chart_and_table()

    # Reset all form-related session state variables
    st.session_state.show_form = False
    st.session_state.show_issue_form = False
    st.session_state.show_my_issue_form = False
    st.session_state.show_sprint_issues = False
    st.session_state.show_dropdown = False
    st.session_state.show_jenkins_form = False
    st.session_state.show_run_jenkins_form = False
    st.session_state.show_git_hub_form = False
    st.session_state.show_get_issue_details_form = False

    if form_type == "register_jira_project":
        st.session_state.show_form = True
        # st.session_state.show_issue_form = False  # Ensure only one form is shown

    if form_type == "create_jira_issue":
        st.session_state.show_issue_form = True
        # st.session_state.show_form = False  # Ensure only one form is shown

    if form_type == "get_my_issues":
        st.session_state.show_my_issue_form = True

        # st.session_state.show_form = False  # Ensure only one form is shown
    if form_type == "Sprint_Issues":
        st.session_state.show_sprint_issues = True

        # st.session_state.show_form = False  # Ensure only one form is shown
    if form_type == "jenkins_pipeline_configuration":
        st.session_state.show_jenkins_form = True

    if form_type == "run_jenkins_pipeline":
        st.session_state.show_run_jenkins_form = True

    if form_type == "github_code_search":
        st.session_state.show_git_hub_form = True

    if form_type == "change_project_form":
        st.session_state.show_dropdown = True
    if form_type == "get_issue_details":
        st.session_state.show_get_issue_details_form = True

        # st.session_state.show_form = False  # Ensure only one form is shown
        # st.session_state.show_issue_form = False  # Ensure only one form is shown


if __name__ == "__main__":
    main()
