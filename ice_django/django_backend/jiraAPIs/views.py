import json
import requests
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
import pandas as pd
import pymongo
from requests.auth import HTTPBasicAuth
from django_backend.settings import mongo_conn
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("dev_logger")
db = mongo_conn()
SERVER_IP = os.getenv("SERVER")
PORT = os.getenv("PORT")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
# Create your views here.
from .jira_functions import (
    JiraInstances,
    JiraUpdater,
    JiraProjectRegistration,
    JiraQuery,
    sprint_json_data,
    get_active_sprint_issues,
    time_conversion,
    compare_date_with_today,
    check_ice_inventory,
    add_project_to_primaryproject,
    get_board_name,
    JQL_QUERY,
    convert_seconds,
)


headers = {"Content-Type": "application/json"}


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class PageNotFound(Exception):
    pass


class UpdateJiraIssues(View):
    """
    API which recieves a POST request and update the jira issues


    Parameter:
    project_name
    user_name
    issue_key
    comment
    worklog_comment
    worklog_duration


    Returns:
    - The Json Response object returned by the API endpoint.
    """

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            project_name = request.POST.get("project_name")
            user_name = request.POST.get("user_name")
            issue_key = request.POST.get("issue_key")
            comment = request.POST.get("comment")
            worklog_comment = request.POST.get("worklog_comment")
            worklog_duration = request.POST.get("worklog_duration")
            # creating an object instance
            jira_instance = JiraUpdater(project_name, user_name)
            # calling get_cluster_info method
            result = jira_instance.update_worklogs(
                issue_key, worklog_comment, comment, worklog_duration
            )
            logger.info(f"Result: {result}")
            return JsonResponse({"success": True, "data": result})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


class GenerateSprintReport(View):
    """
    API which recieves a POST request and update the jira issues


    Parameter:
    project_name
    user_name
    Returns:
    - The Json Response object returned by the API endpoint.
    """

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            project_name = request.POST.get("project_name")
            user_name = request.POST.get("user_name")
            # creating an object instance
            sprint_data = SprintReport(project_name, user_name)
            # calling get_cluster_info method
            data = sprint_data.categorie_issue_types()
            result = {
                "closed_story": data[0],
                "closed_bug": data[1],
                "closed_task": data[2],
                "closed_story_points": data[3],
                "story": data[4],
                "bug": data[5],
                "task": data[6],
                "story_points": data[7],
                "sprintname": data[8],
                "sprintid": data[9],
            }
            return JsonResponse({"success": True, "data": result})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


class SprintInfoView(View):
    """
    API with GET method to return Sprint Info as Jsonresponse

    Input Parameter:
    1. rapidViewId
    2. sprintId

    Output:
    Jsonresponse with keys : status, timeRemaining, issueMetrics, sprintMetrics
    """

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            basicauth_1 = data["basicauth_1"]
            board_name = data["board_name"]
            host_url = data["host_url"]
            jira_type = data["jira_type"]
            username = data["username"]
            board_id = data["board_id"]
            sprint_issues = get_active_sprint_issues(
                host_url, basicauth_1, board_name, jira_type, username, board_id
            )
            logger.info(f"Sprint Issues: {sprint_issues}")
            if sprint_issues[0] == None:
                return JsonResponse(
                    {
                        "Status": f"You do not have to access the requested resource because of this {sprint_issues[1]}"
                    }
                )
            else:
                sprintId = sprint_issues[0]
                rapidViewId = sprint_issues[1]
                sprint_name = sprint_issues[2]
                sprint_startdate = sprint_issues[3]
                sprint_enddate = sprint_issues[4]
                if jira_type == "server":
                    url = f"{host_url}/rest/greenhopper/1.0/gadgets/sprints/health?rapidViewId={rapidViewId}&sprintId={sprintId}"
                    headers = {"Authorization": basicauth_1}
                    response = requests.get(url, headers=headers)
                    data = response.json()
                    res = {
                        "sprint_name": sprint_name,
                        "sprint_startdate": sprint_startdate,
                        "sprint_enddate": sprint_enddate,
                        "remaining_days": data["timeRemaining"]["days"],
                        **{j["key"]: j["value"] for j in data["sprintMetrics"]},
                        **{k["name"]: k["value"] for k in data["progress"]["columns"]},
                    }
                    return JsonResponse(res)
                else:
                    headers = {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    }

                    # Construct the API endpoint URL
                    endpoint_url = f"{host_url}/rest/greenhopper/1.0/gadgets/sprints/health?rapidViewId={rapidViewId}&sprintId={sprintId}"
                    logger.info(f"Endpoint URL: {endpoint_url}")
                    # Make the GET request
                    response = requests.get(
                        endpoint_url, headers=headers, auth=(username, basicauth_1)
                    )
                    data = response.json()
                    res = {
                        "sprint_name": sprint_name,
                        "sprint_startdate": sprint_startdate,
                        "sprint_enddate": sprint_enddate,
                        "remaining_days": data["timeRemaining"]["days"],
                        **{j["key"]: j["value"] for j in data["sprintMetrics"]},
                        **{k["name"]: k["value"] for k in data["progress"]["columns"]},
                    }
                    return JsonResponse(res)
        except Exception as e:
            return JsonResponse({"Status": f"Failed with exception {e}"})


class JiraProjectRegistrationView(View):
    """
    API which recieves a POST request and update the projetc details.


    Parameter:
    project_key
    user_name
    host_url
    board_name
    github_url
    scrum_master
    Returns:
    - The Json Response object returned by the API endpoint.
    """

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            user_name = request.POST.get("user_name")
            url = request.POST.get("url")
            github_url = request.POST.get("github_url")
            scrum_master = request.POST.get("scrum_master")
            username = request.POST.get("username")
            token = request.POST.get("token")
            email_address = request.POST.get("email_address")
            # creating an object instance
            project_data = JiraProjectRegistration()
            jira_info = project_data.extract_jira_info(url)
            logger.info(f"Jira Info: {jira_info}")
            if jira_info == None:
                return JsonResponse(
                    {
                        "success": False,
                        "data": "Invalid Jira URL",
                    }
                )
            else:
                project_key = jira_info[0]
                host_url = jira_info[1]
                board_id = int(jira_info[2])
                board_name = get_board_name(host_url, email_address, token, board_id)
                logger.info(f"Board Name: {board_name}")
            if board_name[0] == None:
                return JsonResponse(
                    {
                        "success": False,
                        "data": board_name[1],
                    }
                )
            server_type = "cloud"
            # calling jira verification and registration method
            if server_type == "server":
                data = project_data.verify_project_key(
                    user_name,
                    project_key,
                    host_url,
                    board_name,
                    github_url,
                    scrum_master,
                    server_type,
                    board_id,
                )
                return JsonResponse({"success": True, "data": data})
            else:
                db.ice_user_data.update_one(
                    {"user_name": user_name},
                    {"$set": {"iCE_cred_properties.api_token": token}},
                )
                data = project_data.verify_board_name(
                    user_name,
                    board_name[0],
                    host_url,
                    project_key,
                    github_url,
                    scrum_master,
                    server_type,
                    board_id,
                )
                logger.info(f"Data: {data}")
                if data[0] == True and data[1] == "Board Name Already Exists":
                    data = check_ice_inventory(board_name[0], user_name)
                    if data != None:
                        return JsonResponse({"success": True, "data": data})
                    else:
                        return JsonResponse(
                            {"success": True, "data": "Project Registration Successful"}
                        )
                elif data[0] == False:
                    return JsonResponse({"success": False, "data": data[1]})
                else:
                    add_project_to_primaryproject(board_name[0], user_name)
                return JsonResponse({"success": True, "data": data[1]})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class JiraReports(View):
    """
    API which recieves a POST request and update the projetc details.


    Parameter:
    project_key
    user_name
    host_url
    board_name
    github_url
    scrum_master
    Returns:
    - The Json Response object returned by the API endpoint.
    """

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            # project_key = request.POST.get("project_key")
            # user_name = request.POST.get("user_name")
            data = json.loads(request.body)
            project_key = data["project_key"]
            user_name = data["user_name"]
            # creating an object instance
            project_data = JiraQuery(project_key, user_name)
            # calling jira verification and registration method
            data = project_data.get_active_sprint_info()
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class GetKanbanIssues(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            host_url = project_details[1]
            basicauth_1 = project_details[2]
            project_name = project_details[6]
            board_name = project_details[3]
            user_name = project_details[4]
            url = f"{host_url}/rest/api/2/search?"
            jql = f'project = {project_name} AND status = "In Progress" '
            try:
                query_params = {"jql": jql, "startAt": 0}
                response = requests.get(
                    url,
                    headers=headers,
                    auth=(user_name, basicauth_1),
                    params=query_params,
                )
                data = response.json()
                issue_data = []
                for issue in data["issues"]:
                    issue_key = issue["key"]
                    summary = issue["fields"]["summary"]
                    description = issue["fields"]["description"]
                    priority = issue["fields"]["priority"]["name"]
                    assignee = issue["fields"]["assignee"]["displayName"]
                    reporter = issue["fields"]["reporter"]["displayName"]
                    comments = issue["fields"]["customfield_10034"]
                    spl_handling = issue["fields"]["customfield_10122"]
                    notes = issue["fields"]["customfield_10040"]
                    portfolio_epic = issue["fields"]["customfield_12841"]
                    qtrly_plan = issue["fields"]["customfield_10275"]
                    acceptance_criteria = issue["fields"]["customfield_10038"]
                    duedate = issue["fields"]["duedate"]
                    timespent = issue["fields"]["timespent"]
                    timeoriginalestimate = issue["fields"]["timeoriginalestimate"]

                    issue_data.append(
                        {
                            "Issue Key": issue_key,
                            "Summary": summary,
                            "Description": description,
                            "Priority": priority,
                            "Assignee": assignee,
                            "Reporter": reporter,
                            "Comments": comments,
                            "Special Handling": spl_handling,
                            "Notes": notes,
                            "Portfolio Epic": portfolio_epic,
                            "Quarterly Plan": qtrly_plan,
                            "Acceptance Criteria": acceptance_criteria,
                            "duedate": duedate,
                            "timespent": timespent,
                            "timeoriginalestimate": timeoriginalestimate,
                        }
                    )
                return JsonResponse({"success": True, "data": issue_data})
            except Exception as e:
                return JsonResponse({"success": False, "data": str(e)})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class ReportDataSprint(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_key = data["project_key"]
            user_name = data["user_name"]
            jira_data = JiraInstances(project_key, user_name)
            try:
                project_details = jira_data.get_jira_instances()
                if project_details[0] == None:
                    return JsonResponse(
                        {
                            "status": False,
                            "data": "Issue with empty primary project name. Please Add primary project again.",
                        }
                    )
                else:
                    host_url = project_details[1]
                    basicauth_1 = project_details[2]
                    board_name = project_details[3]
                    username = project_details[4]
                    jira_type = project_details[7]
                    board_id = project_details[8]
                    dict_data = {}
                    url = "http://{0}:{1}/jiraapi/sprint_data/".format(SERVER_IP, PORT)
                    payload = json.dumps(
                        {
                            "basicauth_1": basicauth_1,
                            "board_name": board_name,
                            "host_url": host_url,
                            "jira_type": jira_type,
                            "username": username,
                            "board_id": board_id,
                        }
                    )
                    logger.info(f"Payload: {payload}")
                    logger.info(f"url: {url}")
                    response = requests.request(
                        "POST", url, headers=headers, data=payload
                    )
                    if response.status_code == 401:
                        # Handle invalid credentials
                        raise AuthenticationError("Invalid username or password.")
                    elif response.status_code == 403:
                        # Handle insufficient permissions
                        raise AuthorizationError(
                            "You do not have permission to access the requested resource."
                        )
                    elif response.status_code == 200:
                        try:
                            gadgets_data = response.json()
                            dict_data.update({"summary": gadgets_data})
                        except:
                            data = response.json()
                            return JsonResponse(
                                {"success": False, "data": data["status"]}
                            )
                    else:
                        raise Exception("Failed to get sprint data")
                    url = "http://{0}:{1}/jiraapi/jiraReports/".format(SERVER_IP, PORT)
                    payload = json.dumps(
                        {"project_key": project_key, "user_name": user_name}
                    )
                    response = requests.request(
                        "POST", url, headers=headers, data=payload
                    )
                    if response.status_code == 200:
                        try:
                            issue_data = response.json()["data"]
                            df = pd.json_normalize(issue_data, sep="_")
                            json_data = sprint_json_data(df)
                            json_data = json.loads(json_data)
                            dict_data.update({"users_progress": json_data})
                            logger.info(f"Dict Data: {dict_data}")
                            return JsonResponse({"status": True, "data": dict_data})
                        except:
                            issue_data = response.json()["data"]
                            return JsonResponse({"status": False, "data": issue_data})
                    else:
                        raise Exception("Failed to get sprint data")
            except Exception as e:
                return JsonResponse(
                    {
                        "status": False,
                        "data": "You do not have permission to access the requested resource.",
                    }
                )
        except Exception as e:
            return JsonResponse({"status": False, "data": str(e)})


class CreateIssue(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            summary = data["summary"]
            description = data["description"]
            acceptance_criteria = data["acceptance_criteria"]
            issue_type = data["issue_type"]
            epic_key = data["epic_key"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            host_url = project_details[1]
            basicauth_1 = project_details[2]
            board_name = project_details[3]
            username = project_details[4]
            project_key = project_details[6]
            url = f"{host_url}/rest/api/2/issue"
            payload = json.dumps(
                {
                    "fields": {
                        "project": {"key": project_key},
                        "summary": summary,
                        "description": description,
                        "issuetype": {"name": issue_type},
                        "parent": {"key": epic_key},
                        "customfield_10035": {"value": board_name},
                        "customfield_10038": acceptance_criteria,
                    }
                }
            )
            response = requests.post(
                url, headers=headers, data=payload, auth=(username, basicauth_1)
            )
            if response.status_code == 400:
                payload = json.dumps(
                    {
                        "fields": {
                            "project": {"key": project_key},
                            "summary": summary,
                            "description": description,
                            "issuetype": {"name": issue_type},
                        }
                    }
                )
                response = requests.post(
                    url, headers=headers, data=payload, auth=(username, basicauth_1)
                )
            issue_key = response.json()["key"]
            issue_link = f"{host_url}/browse/{issue_key}"
            return JsonResponse({"success": True, "data": issue_link})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class ScrumReport(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            # creating an object instance
            project_data = JiraQuery(project_name, user_name)
            # calling jira verification and registration method
            data = project_data.get_scrum_report_data()
            logger.info(f"Data: {data}")
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class VelocityReport(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            host_url = project_details[1]
            basicauth_1 = project_details[2]
            username = project_details[4]
            board_id = project_details[8]
            velocity_url = f"{host_url}/rest/greenhopper/1.0/rapid/charts/velocity?rapidViewId={board_id}"
            response = requests.get(
                velocity_url, auth=HTTPBasicAuth(username, basicauth_1)
            )
            if response.status_code == 200:
                velocity_dict = {}
                velocity_data = response.json()
                for sprint_data in velocity_data["sprints"]:
                    sprint_id = str(sprint_data["id"])
                    sprint_name = sprint_data["name"]
                    sprint_goal = sprint_data["goal"]
                    completedIssues = velocity_data["velocityStatEntries"][sprint_id][
                        "completed"
                    ]["value"]
                    estimated = velocity_data["velocityStatEntries"][sprint_id][
                        "estimated"
                    ]["value"]
                    Issues_in_sprint = velocity_data["velocityStatEntries"][sprint_id][
                        "allConsideredIssueKeys"
                    ]
                    velocity_dict[sprint_name] = {
                        "Sprint_Goal": sprint_goal,
                        "Completed_Issues_Story_Points": completedIssues,
                        "Estimated_Story_Points": estimated,
                        "Issues in Sprint": Issues_in_sprint,
                    }
                return JsonResponse({"success": True, "data": velocity_dict})
            else:
                return JsonResponse({"data": "Authnication Failed"})
        except Exception as e:
            logger.error(f"Error in VelocityReport: {e}")
            return JsonResponse({"success": False, "data": "No Velocity Data Found"})


class BurnDownReport(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            project_key = project_details[6]
            jira_type = project_details[7]
            jira_host = project_details[1]
            basic_auth = project_details[2]
            board_anme = project_details[3]
            user_name = project_details[4]
            board_id = project_details[8]
            sprint_data = get_active_sprint_issues(
                jira_host, basic_auth, board_anme, jira_type, user_name, board_id
            )
            logger.info(f"Sprint Data: {sprint_data}")
            if sprint_data[0] != None:
                sprintId = sprint_data[0]
                sprint_name = sprint_data[2]
                startDate = sprint_data[3]
                endDate = sprint_data[4]
                report_url = f"{jira_host}jira/software/c/projects/{project_key}/boards/{board_id}/reports/burndown-chart?sprint={sprintId}"
                url = f"{jira_host}/rest/api/2/search?"
                logger.info(f"URL: {url}")
                jql = f"project = {project_key} AND sprint = {sprintId}"
                logger.info(f"JQL: {jql}")
                fields = [
                    "id",
                    "key",
                    "assignee",
                    "summary",
                    "description",
                    "updated",
                    "worklog",
                    "comment",
                    "status",
                    "issuetype",
                    "customfield_10002",
                    "customfield_10032",
                    "priority",
                ]
                query_params = {"jql": jql, "startAt": 0, "fields": fields}
                response = requests.get(
                    url,
                    headers=headers,
                    auth=(user_name, basic_auth),
                    params=query_params,
                )
                data = response.json()
                if response.status_code == 200:
                    data = response.json()
                    burndown_data = {}
                    for issue in data["issues"]:
                        issue_key = issue["key"]
                        issue_summary = issue["fields"]["summary"]
                        story_points = issue["fields"]["customfield_10032"]
                        worklogs = issue["fields"]["worklog"]["worklogs"]
                        update_dict = {}
                        for i in worklogs:
                            update_dict[i["updated"]] = i["timeSpent"]
                        detail_list = [
                            {"issue_summary": issue_summary},
                            {"updated_date": update_dict},
                            {"story_points": story_points},
                        ]
                        burndown_data[issue_key] = detail_list
                    burndown_data["sprint_name"] = sprint_name
                    burndown_data["startDate"] = startDate
                    burndown_data["endDate"] = endDate
                    return JsonResponse(
                        {
                            "success": True,
                            "data": burndown_data,
                            "report_url": report_url,
                        }
                    )
                elif response.status_code == 401:
                    return JsonResponse({"data": "Authnication Failed"})
                elif response.status_code == 403:
                    return JsonResponse({"data": "Authnication Failed"})
                elif response.status_code == 400:
                    return JsonResponse({"data": "Bad Request"})
            else:
                return JsonResponse({"data": "Authnication Failed"})
        except Exception as e:
            logger.error(f"Error in Burn Down Report: {e}")
            return JsonResponse({"success": False, "data": "No Burn down Data Found"})


class BurnUpReport(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            project_key = project_details[6]
            jira_type = project_details[7]
            jira_host = project_details[1]
            basic_auth = project_details[2]
            board_anme = project_details[3]
            user_name = project_details[4]
            board_id = project_details[8]
            logger.info(f"Project Details: {project_details}")
            sprint_data = get_active_sprint_issues(
                jira_host, basic_auth, board_anme, jira_type, user_name, board_id
            )
            logger.info(f"Sprint Data: {sprint_data}")
            if sprint_data[0] != None:
                sprintId = sprint_data[0]
                sprint_name = sprint_data[2]
                startDate = sprint_data[3]
                endDate = sprint_data[4]
                report_url = f"{jira_host}jira/software/c/projects/{project_key}/boards/{board_id}/reports/burnup-chart?sprint={sprintId}"
                url = f"{jira_host}/rest/api/2/search?"
                logger.info(f"URL: {url}")
                jql = f"project = {project_key} AND sprint = {sprintId}"
                logger.info(f"JQL: {jql}")
                fields = [
                    "id",
                    "key",
                    "assignee",
                    "summary",
                    "description",
                    "updated",
                    "worklog",
                    "comment",
                    "status",
                    "issuetype",
                    "customfield_10002",
                    "customfield_10032",
                    "priority",
                ]
                query_params = {"jql": jql, "startAt": 0, "fields": fields}
                response = requests.get(
                    url,
                    headers=headers,
                    auth=(user_name, basic_auth),
                    params=query_params,
                )
                data = response.json()
                logger.info(f"Response: {data}")
                if response.status_code == 200:
                    data = response.json()
                    burnup_data = {}
                    for issue in data["issues"]:
                        issue_key = issue["key"]
                        issue_summary = issue["fields"]["summary"]
                        status = issue["fields"]["status"]["name"]
                        if status == "Done":
                            updated_date = issue["fields"]["updated"]
                        else:
                            updated_date = None
                        story_points = issue["fields"]["customfield_10032"]
                        detail_list = [
                            {"issue_summary": issue_summary},
                            {"closed_date": updated_date},
                            {"story_points": story_points},
                        ]
                        burnup_data[issue_key] = detail_list
                    burnup_data["sprint_name"] = sprint_name
                    burnup_data["startDate"] = startDate
                    burnup_data["endDate"] = endDate
                    return JsonResponse(
                        {
                            "success": True,
                            "data": burnup_data,
                            "report_url": report_url,
                        }
                    )
                elif response.status_code == 401:
                    return JsonResponse({"data": "Authnication Failed"})
                elif response.status_code == 403:
                    return JsonResponse({"data": "Authnication Failed"})
                elif response.status_code == 400:
                    return JsonResponse({"data": "Bad Request"})
            else:
                return JsonResponse({"data": "Authnication Failed"})
        except Exception as e:
            logger.error(f"Error in Burn Down Report: {e}")
            return JsonResponse(
                {"success": False, "data": "No Burn burn up Data Found"}
            )


class GetIssuesDetails(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            issue_key = data["issue_key"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            if project_details[0] != None:
                host_url = project_details[1]
                basicauth_1 = project_details[2]
                username = project_details[4]
                url = f"{host_url}/rest/api/3/issue/{issue_key}"
                response = requests.get(
                    url, headers=headers, auth=(username, basicauth_1)
                )
                if response.status_code == 200:
                    issue_details = {}
                    issue_data = response.json()
                    summary = issue_data["fields"].get("summary", {})
                    if None == issue_data["fields"].get("description", None):
                        description = "No Description"
                    else:
                        description = (
                            issue_data["fields"]
                            .get("description", {})
                            .get("content", {})[0]
                            .get("content", {})[0]
                            .get("text", {})
                        )
                    status = issue_data["fields"]["status"]["name"]
                    assignee = issue_data["fields"].get("assignee", {})
                    comments = issue_data["fields"]["comment"]["comments"]
                    status = issue_data["fields"]["status"]["name"]
                    updated_date = issue_data["fields"]["updated"]
                    story_points = issue_data["fields"].get("customfield_10032")
                    dict_comments = {}
                    for i, item in enumerate(comments):
                        dict_comments[i] = item["body"]["content"][0]["content"][0][
                            "text"
                        ]

                    worklogs = issue_data["fields"]["worklog"]["worklogs"]
                    time_count = 0
                    for i in worklogs:
                        time_count += i["timeSpentSeconds"]
                    time_spend = convert_seconds(time_count)
                    issue_details.update({"comments": dict_comments})
                    issue_details.update({"time_spend": time_spend})
                    issue_details.update({"status": status})
                    issue_details.update({"story_points": story_points})
                    issue_details.update({"updated_date": updated_date})
                    issue_details.update({"assignee": assignee})
                    issue_details.update({"description": description})
                    issue_details.update({"summary": summary})
                    return JsonResponse({"success": True, "data": issue_details})
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid username or password.")
                elif response.status_code == 403:
                    raise AuthorizationError(
                        "You do not have permission to access the requested resource."
                    )
            else:
                logger.error(f"Error in GetIssuesDetails: {project_details[1]}")
                return JsonResponse({"success": False, "data": project_details[1]})
        except AuthorizationError as e:
            logger.error(f"Error in GetIssuesDetails: {e}")
            return JsonResponse({"success": False, "data": str(e)})


class GetEpicIssues(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
            project_name = data["project_name"]
            user_name = data["user_name"]
            jira_data = JiraInstances(project_name, user_name)
            project_details = jira_data.get_jira_instances()
            if project_details[0] != None:
                host_url = project_details[1]
                basicauth_1 = project_details[2]
                username = project_details[4]
                board_id = project_details[8]
                url = f"{host_url}/rest/agile/1.0/board/{board_id}/epic"
                response = requests.get(
                    url, headers=headers, auth=(username, basicauth_1)
                )
                if response.status_code == 200:
                    data = json.loads(response.text)
                    epics = data["values"]
                    epic_dict = {}
                    for epic in epics:
                        summary = epic["summary"]
                        key = epic["key"]
                        epic_dict[summary] = key
                    return JsonResponse({"success": True, "data": epic_dict})
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid username or password.")
                elif response.status_code == 403:
                    raise AuthorizationError(
                        "You do not have permission to access the requested resource."
                    )
            else:
                logger.error(f"Error in GetEpicIssues: {project_details[1]}")
                return JsonResponse({"success": False, "data": project_details[1]})
        except AuthorizationError as e:
            logger.error(f"Error in GetEpicIssues: {e}")
            return JsonResponse({"success": False, "data": str(e)})
        except AuthenticationError as e:
            logger.error(f"Error in GetEpicIssues: {e}")
            return JsonResponse({"success": False, "data": str(e)})
        except Exception as e:
            logger.error(f"Error in GetEpicIssues: {e}")
            return JsonResponse({"success": False, "data": "No Epic Issues Found"})


class DailyStatusReport(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = json.loads(request.body)
        project_name = data["project_name"]
        user_name = data["user_name"]
        jira_data = JiraInstances(project_name, user_name)
        try:
            project_details = jira_data.get_jira_instances()
            logger.info(f"Project Details: {project_details}")
            if project_details[0] == None:
                return JsonResponse(
                    {
                        "success": False,
                        "data": project_details[1],
                    }
                )
            else:
                host_url = project_details[1]
                basicauth_1 = project_details[2]
                project_name = project_details[6]
                board_name = project_details[3]
                username = project_details[4]
                jira_type = project_details[7]
                board_id = project_details[8]
                sprint_issues = get_active_sprint_issues(
                    host_url, basicauth_1, board_name, jira_type, username, board_id
                )
                logger.info(f"Sprint Issues: {sprint_issues}")
                if sprint_issues[0] == None:
                    return JsonResponse(
                        {
                            "data": f"You do not have to access the requested resource because of this {sprint_issues[1]}"
                        }
                    )
                else:
                    sprintId = sprint_issues[0]
                    url = f"{host_url}/rest/api/2/search?"
                    jql = f'project = {project_name}  AND sprint = {sprintId} AND status = "In Progress" '
                    fields = JQL_QUERY.get("fields")
                    query_params = {
                        "jql": jql,
                        "startAt": 0,
                        "maxResults": 100,
                        "fields": fields,
                    }
                    response = requests.get(
                        url,
                        headers=headers,
                        auth=(username, basicauth_1),
                        params=query_params,
                    )
                    data = response.json()
                    logger.info(f"Data: {response.status_code}")
                    if response.status_code == 401:
                        # Handle invalid credentials
                        raise AuthenticationError("Invalid username or password.")
                    elif response.status_code == 403:
                        # Handle insufficient permissions
                        raise AuthorizationError(
                            "You do not have permission to access the requested resource."
                        )
                    elif response.status_code == 400:
                        raise PageNotFound(" Bad Request")

                    elif response.status_code == 200:
                        data = response.json()
                        dict_data = {}
                        for issue in data["issues"]:
                            issue_key = issue["key"]
                            try:
                                comments = issue["fields"]["comment"]["comments"][-1][
                                    "body"
                                ]
                            except:
                                comments = "No Comments"
                            last_updates = issue["fields"].get("updated")
                            last_updates = time_conversion(last_updates)
                            assignee = issue["fields"]["assignee"]["displayName"]
                            if compare_date_with_today(last_updates):
                                if assignee in dict_data:
                                    data_dict = {"comments": comments, "key": issue_key}
                                    dict_data[assignee].append(data_dict)
                                else:
                                    data_dict = {"comments": comments, "key": issue_key}
                                    dict_data[assignee] = [data_dict]
                            else:
                                pass
                        return JsonResponse({"success": True, "data": dict_data})
        except AuthorizationError as e:
            return JsonResponse({"success": False, "data": str(e)})
        except AuthenticationError as e:
            return JsonResponse({"success": False, "data": str(e)})
        except PageNotFound as e:
            return JsonResponse({"success": False, "data": str(e)})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class ViewBacklogs(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = json.loads(request.body)
        project_name = data["project_name"]
        user_name = data["user_name"]
        jira_data = JiraInstances(project_name, user_name)
        try:
            project_details = jira_data.get_jira_instances()
            logger.info(f"Project Details: {project_details}")
            if project_details[0] == None:
                return JsonResponse(
                    {
                        "success": False,
                        "data": project_details[1],
                    }
                )
            else:
                host_url = project_details[1]
                basicauth_1 = project_details[2]
                project_name = project_details[6]
                board_name = project_details[3]
                username = project_details[4]
                jira_type = project_details[7]
                board_id = project_details[8]
                # Prepare authentication headers
                url = "{1}/rest/agile/1.0/board/{0}/backlog".format(board_id, host_url)
                auth = (username, basicauth_1)
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
                response = requests.get(url, headers=headers, auth=auth)
                if response.status_code == 200:
                    res = response.json()
                    data_issues = res["issues"]
                    backlog = {}
                    for i in range(len(data_issues)):
                        backlog[data_issues[i]["key"]] = data_issues[i]["fields"][
                            "summary"
                        ]
                    return JsonResponse({"success": True, "data": backlog})
                else:
                    return JsonResponse(
                        {"success": False, "data": "Failed to get Backlogs"}
                    )
        except AuthorizationError as e:
            return JsonResponse({"success": False, "data": str(e)})
        except AuthenticationError as e:
            return JsonResponse({"success": False, "data": str(e)})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})


class GetIssue(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        data = json.loads(request.body)
        project_name = data["project_name"]
        user_name = data["user_name"]
        logger.info(f"Data: {data}")
        jira_data = JiraInstances(project_name, user_name)
        try:
            project_details = jira_data.get_jira_instances()
            logger.info(f"Project Details: {project_details}")
            if project_details[0] == None:
                return JsonResponse(
                    {
                        "success": False,
                        "data": project_details[1],
                    }
                )
            else:
                host_url = project_details[1]
                basicauth_1 = project_details[2]
                project_name = project_details[6]
                board_name = project_details[3]
                username = project_details[4]
                jira_type = project_details[7]
                board_id = project_details[8]
                sprint_issues = get_active_sprint_issues(
                    host_url, basicauth_1, board_name, jira_type, username, board_id
                )
                logger.info(f"Sprint Issues: {sprint_issues}")
                if sprint_issues[0] == None:
                    return JsonResponse(
                        {
                            "data": f"You do not have to access the requested resource because of this {sprint_issues[1]}"
                        }
                    )
                else:
                    sprintId = sprint_issues[0]
                    url = f"{host_url}/rest/api/2/search?"
                    jql = f"project = {project_name} AND sprint = {sprintId}"
                    query_params = {"jql": jql, "startAt": 0}
                    response = requests.get(
                        url,
                        headers=headers,
                        auth=(username, basicauth_1),
                        params=query_params,
                    )
                    data = response.json()
                    logger.info(f"Data: {data}")
                    if response.status_code == 401:
                        # Handle invalid credentials
                        raise AuthenticationError("Invalid username or password.")
                    elif response.status_code == 403:
                        # Handle insufficient permissions
                        raise AuthorizationError(
                            "You do not have permission to access the requested resource."
                        )
                    elif response.status_code == 400:
                        raise PageNotFound(" Bad Request")
                    elif response.status_code == 200:
                        data = response.json()
                        dict_data = {}
                        for issue in data["issues"]:
                            issue_key = issue["key"]
                            summary = issue["fields"]["summary"]
                            description = issue["fields"]["description"]
                            issue_type = issue["fields"]["issuetype"]["name"]
                            assignee = issue["fields"]["assignee"]["emailAddress"]
                            dict_data.update(
                                {
                                    issue_key: {
                                        "Summary": summary,
                                        "Description": description,
                                        "Assignee": assignee,
                                        "Issue_Type": issue_type,
                                    }
                                }
                            )
                        return JsonResponse({"success": True, "data": dict_data})
        except AuthorizationError as e:
            return JsonResponse({"success": False, "data": str(e)})
        except AuthenticationError as e:
            return JsonResponse({"success": False, "data": str(e)})
        except PageNotFound as e:
            return JsonResponse({"success": False, "data": str(e)})
        except Exception as e:
            return JsonResponse({"success": False, "data": str(e)})
