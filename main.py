import os
import sys
import json
import logging
import urllib3
import requests
from datetime import datetime
from logging.config import fileConfig

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JobLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return msg, {"extra": {"job_id": self.extra.get("job_id", "-")}}

# initialize logger
fileConfig(fname=(os.path.join(sys.path[0], 'log.ini')), disable_existing_loggers=False) # get log configuration from file
logger = logging.getLogger(__name__)  # Name that will prefix all log entries

job_id = sys.argv[-1]
logger = JobLoggerAdapter(logger, {"job_id": job_id})
logger.info(f"Starting script for Job ID: {job_id}")

os.makedirs("results", exist_ok=True)

api_key = os.getenv("X360_TLS_KEY_PATH")
api_pem = os.getenv("X360_TLS_CERT_PATH")
api_host = os.getenv("X360_HOST")
api_port = os.getenv("X360_PORT")
api_ext = os.getenv("X360_API_PATH") or ''

query_file = sys.argv[1]
folder_name = sys.argv[2]

PROJECT_LIST_ENDPOINT = 'https://{}:{}/xacta/api/project/list'                                      # Project list endpoint. HOST and PORT are variables
ADVANCED_QUERY_ENDPOINT = 'https://{}:{}/xacta/api/project/{}/vocab/advancedQuery'                  # Advance query endpoint

start_date = datetime.now()
logger.info("***********************************************")
logger.info(f"Report Started @: {start_date}")
logger.info("***********************************************")

## Get Query file from arguments and open query file into an object
logger.info("Converting query file to object")
with open(query_file, 'r') as file:
    advance_query = file.read().replace('\n', '')

if not advance_query:
    logger.error("Query not available. Please try again.")
    sys.exit(1)

# This section of code will access the Xacta API, run the advance query and return the
# results as a json response.  It will also format the json response and save it to a file.

try:
    response = requests.get(PROJECT_LIST_ENDPOINT.format(api_host, api_port),
                            cert=(api_pem, api_key), verify=False)
    logger.info(f"Response {response.status_code} from {PROJECT_LIST_ENDPOINT.format(api_host, api_port)}")
except Exception as e:
    logger.error(f"Error: {e}")
    sys.exit(1)

try:
    project_list = response.json()
except Exception as e:
    logger.error(f"Error: {e}")
    sys.exit(1)

project_list = [entry for entry in project_list if entry['folderName'] == folder_name]       # Filter the list and only keep projects in the specified folder

with open('results/projectList.json', 'w') as outfile:                                                        # Open the file in write more
    outfile.write(json.dumps(project_list, indent=4, sort_keys=False, separators=(',', ':')))

# The number of project that will be processed
total_projects = len(project_list)
logger.info(f"Total projects==>: {total_projects}")

project_count = 0
json_data = []
for item in project_list:
    folder = item['folderName']
    project_count += 1
    uuid = item['uuid']
    project_name = item['name']

    logger.info(f"API Endpoint is: {ADVANCED_QUERY_ENDPOINT.format(api_host, api_port, uuid)}")

    response = requests.post(ADVANCED_QUERY_ENDPOINT.format(api_host, api_port, uuid ),
                             cert=(api_pem, api_key), headers={'Content-Type': 'application/json'},
                             data=advance_query, verify=False)
    logger.info(f"Response {response.status_code} from {ADVANCED_QUERY_ENDPOINT.format(api_host, api_port, uuid)}")

    # If the status code is not 200, then the data returned from
    # the response is not usable.  See log for skipped projects.

    logger.info(f"Completed Processing Project: {project_count} of {total_projects} - Code: "
                f"[{response.status_code}] - Project: {item['name']} UUID: {item['uuid']}")

    if response.status_code != 200:
        logger.info(f"SKIPPING PROJECT: {folder} / {project_name}")
        logger.info(f"{response.text}")
        continue

    project_obj = response.json()       # Object to be used for processing each project
    json_data.extend(project_obj)       # create a growing list of all json response

# All projects have been processed so lets save the JSON responses to a
# file for use by external reporting tool such as Tableau or Power BI
with open("results/results.json", 'w') as outfile:                 # Open the file in write more
    outfile.write(json.dumps(json_data, indent=4, sort_keys=False, separators=(',', ':')))

logger.info("***********************************************")
logger.info(f"Report Finished @: {datetime.now()}")
end_date = datetime.now()
logger.info(f"Total Run time: {end_date - start_date}")
logger.info("***********************************************")