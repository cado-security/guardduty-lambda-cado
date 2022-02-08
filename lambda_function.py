""" Copyright 2022 Cado Security Ltd. All rights reserved """

import urllib3
import requests
import datetime
import random
import string
import logging
import os

# The hostname of the Cado Response platform
CADO_IP = os.getenv("CADO_IP")
# The region we are running in
CADO_REGION = os.getenv("CADO_REGION")
# The API key for cado response
CADO_API_KEY = os.getenv("CADO_API_KEY")
# The S3 bucket to collect the volume to prior to processing
CADO_BUCKET = os.getenv("CADO_BUCKET")

def lambda_handler(event: dict, context):
    """The Lambda function handler
    It parses a GuardDuty event and calls Cado Response

    Args:
        event (dict): The GuardDuty event
        context (any): Additional information from Lambda

    Returns:
        None
    """

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.info(f"Lambda called with: {str(event)}")
    instance_id = event.get('detail', {}).get('resource', {}).get('instanceDetails', {}).get('instanceId')
    if not instance_id:
        logging.info("No instance ID in message, skipping event")
        return

    # Create new project:
    project_date = datetime.date.today()
    project_random = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    api_url = f"https://{CADO_IP}/api/v2"
    logging.info("Creating a new project...")
    projects_url = api_url + "/projects"
    logging.info(f"Sending POST request to: {projects_url}")
    new_project_name = f"scan-{str(project_random)}-{str(project_date)}"
    logging.info("New project name: " + new_project_name)
    body_params = {"caseName": new_project_name}
    project_result = requests.post(
        projects_url,
        json=body_params,
        headers={"Authorization": "Bearer " + CADO_API_KEY},
        verify=False,
    )
    project_id = project_result.json()["id"]


    # Now Import the instance
    get_ec2_instances_url = f"{projects_url}/{project_id}/imports/ec2"
    logging.info(f"About to import instance: {str(instance_id)}")
    body_params = {
        "bucket": CADO_BUCKET,
        "instance_id": instance_id,
        "include_screenshot": "true",
        "include_logs": "true",
        "compress": "true",
        "include_disks": "true",
        "region": CADO_REGION,
    }
    result = requests.post(
        get_ec2_instances_url,
        json=body_params,
        headers={"Authorization": "Bearer " + CADO_API_KEY},
        verify=False,
    )
    report = (f"About to import instance: {instance_id} into project name: {new_project_name} ")

    return {"statusCode": 200, "body": report}
