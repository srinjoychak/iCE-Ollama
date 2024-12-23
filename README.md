# Steps to use the code
## Prerequisites

- Docker
- Docker Compose

**System Requirements:**

   A GPU Machine is needed.

1. **Clone the Repository:**

   git clone https://wwwin-github.cisco.com/iCE/iCE_ScrumBot_Ollama
   cd iCE_ScrumBot_Ollama

2. **Update the .env File:** 

   Populate the .env file with the required parameters
   Update the user: EMAIL
   Update the Jira access token: JIRA_API_TOKEN
   Update the Jenkins access token: JENKINS_TOKEN
   Update the Jenkins User name : JENKINS_USERNAME
   Update the GIT url : GIT_URL
   Update the GIT Token: GIT_TOKEN
   Update the Model name: MODEL_NAME **I have found Mistral Instruct model to be the most suitable open source model for using tools.**


3. **Start All Services:**

   Run the set_up_ollama.sh script to start all the services
   sh set_up_ollama.sh

4.**Access the Streamlit Chat Bot:**

   Open your browser and navigate to the following URL to use the Streamlit chat bot:
   <server_ip>:5006







