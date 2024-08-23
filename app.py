import os
import logging
from flask import Flask, request, jsonify
import openai
import core_functions
import assistant
import hubspot
from hubspot.crm.owners import ApiException as OwnersApiException
from hubspot.crm.objects.tasks import SimplePublicObjectInputForCreate, ApiException as TasksApiException
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)

# OpenAI Initialization
# Check OpenAI version compatibility
core_functions.check_openai_version()

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found in environment variables")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize all available tools
tool_data = core_functions.load_tools_from_directory('tools')

# Create or load assistant
assistant_id = assistant.create_assistant(client, tool_data)

# HubSpot Initialization
HUBSPOT_ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
if not HUBSPOT_ACCESS_TOKEN:
    raise ValueError("No HubSpot access token found in environment variables")
client_hubspot = hubspot.Client.create(access_token=HUBSPOT_ACCESS_TOKEN)

def get_hubspot_owner_id(email):
    try:
        owners_page = client_hubspot.crm.owners.owners_api.get_page(limit=100, archived=False, email=email)
        if owners_page.results and len(owners_page.results) > 0:
            return owners_page.results[0].id
        else:
            return None
    except OwnersApiException as e:
        logging.error(f"Exception when calling owners_api->get_page: {e}")
        return None

def convert_date_to_timestamp(date_str):
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        return int(dt.timestamp() * 1000)
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%m/%d/%y")
            return int(dt.timestamp() * 1000)
        except ValueError as e:
            logging.error(f"Error parsing date: {e}")
            return None

# Routes
@app.route('/text', methods=['POST'])
def start_and_chat():
    core_functions.check_api_key()
    data = request.json
    user_input = data.get('message', '')

    if not user_input:
        logging.error("Error: Missing message")
        return jsonify({"error": "Missing message"}), 400

    logging.info("Starting a new conversation...")
    thread = client.beta.threads.create()
    logging.info(f"New thread created with ID: {thread.id}")

    thread_id = thread.id

    logging.info(f"Received message: {user_input} for thread ID: {thread_id}")
    client.beta.threads.messages.create(thread_id=thread_id,
                                        role="user",
                                        content=user_input)
    run = client.beta.threads.runs.create(thread_id=thread_id,
                                          assistant_id=assistant_id)

    core_functions.process_tool_calls(client, thread_id, run.id, tool_data)

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value
    logging.info(f"Assistant response: {response}")
    return jsonify({"response": response, "thread_id": thread_id})

@app.route('/create_hubspot_task', methods=['POST'])
def create_hubspot_task():
    data = request.json
    mail1 = data.get('mail1')
    mail2 = data.get('mail2')
    mail3 = data.get('mail3')
    hs_task_body = f"{mail1}\n\n{mail2}\n\n{mail3}"

    date_str = data.get('hs_timestamp')
    email = data.get('email')
    hs_task_subject = data.get('hs_task_subject')
    hs_task_priority = data.get('hs_task_priority')
    hs_task_type = data.get('hs_task_type', 'TODO')

    hs_timestamp = convert_date_to_timestamp(date_str)
    if hs_timestamp is None:
        return jsonify({"error": "Invalid date format"}), 400

    hubspot_owner_id = get_hubspot_owner_id(email)
    if hubspot_owner_id is None:
        return jsonify({"error": "No HubSpot owner found for the provided email"}), 400

    properties = {
        "hs_task_body": hs_task_body,
        "hs_timestamp": hs_timestamp,
        "hubspot_owner_id": hubspot_owner_id,
        "hs_task_subject": hs_task_subject,
        "hs_task_priority": hs_task_priority,
        "hs_task_type": hs_task_type
    }

    simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=properties)

    try:
        api_response = client_hubspot.crm.objects.tasks.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
        return jsonify(api_response.to_dict())
    except TasksApiException as e:
        logging.error(f"Exception when calling basic_api->create: {e}")
        return jsonify({"error": "Failed to create task in HubSpot"}), 500

@app.route('/get_hubspot_owners', methods=['GET'])
def get_hubspot_owners():
    try:
        owners_page = client_hubspot.crm.owners.owners_api.get_page(limit=100, archived=False)
        owners_list = []

        for owner in owners_page.results:
            owner_dict = {
                "id": owner.id,
                "email": owner.email
            }
            if hasattr(owner, 'firstName'):
                owner_dict['firstName'] = owner.firstName
            if hasattr(owner, 'lastName'):
                owner_dict['lastName'] = owner.lastName

            owners_list.append(owner_dict)

        return jsonify(owners_list)
    except OwnersApiException as e:
        logging.error(f"Exception when calling owners_api->get_page: {e}")
        return jsonify({"error": "Failed to retrieve HubSpot owners"}), 500

# Start the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
