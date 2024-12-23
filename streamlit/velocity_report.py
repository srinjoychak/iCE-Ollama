from utilities import validate_json, ollama_request

VELOCITY_ANALYSIS_PROMPTS = {
    "set_profile": "You are a seasoned Scrum Master and Jira specialist.",
    "Instructions": "Analyse the following JSON data, and generate a velocity report for each quarter. Please Include the following metrics:\n1. Total number of completed issues\n2. Total points completed\n3. Average velocity per sprint\n4. Team capacity utilization\n5. At the end, include a table quarterly per sprint with Completed v/s Assigned Story Points. \n Give me the report directlywith headers in ** **, do not provide any analysis or other information",
    # "Instructions" : "Analyze the following JSON data and generate a velocity report for each quarter. Please include the following metrics:\n1. Total number of completed issues\n2. Total points completed\n3. Average velocity per sprint\n4. Team capacity utilization\n5. Include individual bullets with info for Completed v/s Assigned Story Points.\nGive me the report directly.",
}


def velocity_report(velocity_data):
    # Call the send_message function with the ice_url variable
    if validate_json(velocity_data):
        final_report_prompt = (
            VELOCITY_ANALYSIS_PROMPTS["set_profile"]
            + "\n"
            + VELOCITY_ANALYSIS_PROMPTS["Instructions"]
            + "\n"
            + str(velocity_data)
        )
        final_report = ollama_request(final_report_prompt)
        return final_report
    else:
        return "Invalid JSON format"
