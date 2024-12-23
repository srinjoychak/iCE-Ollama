import json
import requests
from utilities import ollama_request, validate_json
import logging
from logging.config import dictConfig
from logging_file import LOGGING

dictConfig(LOGGING)
logger = logging.getLogger("dev_logger")


def generate_combined_string(data_dict):
    try:
        combined_strings = []

        if isinstance(data_dict, str):
            return data_dict

        logger.info("Data Dict is : %s", data_dict)

        for key, values in data_dict.items():
            if values is None or values == [None]:
                continue

            strs = ""
            for i in values:
                try:
                    issue_key = i.get("key", "N/A")
                    comments = i.get("comments", "No comments available")
                    strs += (
                        "\n"
                        + f"**Issue_Key** : [{issue_key}]({issue_key})"
                        + "\n"
                        + f"**Comments** : {comments}"
                    )
                except Exception as e:
                    logger.error("Error processing item: %s", e)
                    continue

            str2 = f"**{key}**" + "\n" + strs
            combined_strings.append(str2)

        user_message = f"""
        You are a seasoned Scrum Master and Jira specialist. Your task involves producing a report from the project data given below.
        The report should be segmented into a Blockers section. For the Blockers, clearly identify the blockers and use bullet points to highlight any dependency or blocker for a story's progress.
        {combined_strings}
        """

        response = ollama_request(user_message)
        return response

    except Exception as e:
        logger.error("An error occurred: %s", e)
        return "An error occurred while generating the report. Please check the logs for more details."
