
# Flask App with OpenAI and HubSpot Integration

This Flask application integrates OpenAI for conversational AI and HubSpot for task management. The app provides several routes to interact with these APIs, handling tasks such as creating conversations and tasks in HubSpot.

## Features
- **Server Status Check:** Simple endpoint to check if the server is running.
- **Text Conversations:** Start a conversation with an AI assistant using OpenAI's API.
- **HubSpot Task Creation:** Automatically create tasks in HubSpot CRM with specified parameters.
- **HubSpot Owner Retrieval:** Retrieve HubSpot owner information.

## Requirements

### Environment Variables
You must configure the following environment variables before running the app:
- `OPENAI_API_KEY`: Your OpenAI API key.
- `HUBSPOT_ACCESS_TOKEN`: Your HubSpot API access token.
- `VALID_API_KEYS`: A comma-separated list of valid API keys for authentication.

### Dependencies
Install the required dependencies by running:

```bash
pip install -r requirements.txt
```

### Python Libraries
- `Flask`
- `openai`
- `hubspot`
- `logging`

## Usage

### Running the App

1. Set up the required environment variables.
2. Start the Flask application:

```bash
python app.py
```

By default, the app will run on `0.0.0.0:8000`.

### Endpoints

#### 1. `GET /`
Check if the server is running.

#### 2. `POST /text`
Start a conversation with OpenAI.

**Request Body Example:**
```json
{
  "message": "Hello, what's the weather like today?"
}
```

**Headers:**
- `X-API-KEY`: Your valid API key.

**Response Example:**
```json
{
  "response": "It's sunny in your area.",
  "thread_id": "12345"
}
```

#### 3. `POST /create_hubspot_task`
Create a task in HubSpot CRM.

**Request Body Example:**
```json
{
  "mail1": "First email body",
  "mail2": "Second email body",
  "mail3": "Third email body",
  "hs_timestamp": "09/22/2024",
  "email": "owner@example.com",
  "hs_task_subject": "Follow up on leads",
  "hs_task_priority": "High",
  "hs_task_type": "TODO"
}
```

**Headers:**
- `X-API-KEY`: Your valid API key.

**Response Example:**
```json
{
  "id": "12345678",
  "properties": {
    "hs_task_body": "First email body\n\nSecond email body\n\nThird email body",
    "hs_timestamp": "1721635200000",
    "hubspot_owner_id": "98765",
    "hs_task_subject": "Follow up on leads",
    "hs_task_priority": "High",
    "hs_task_type": "TODO"
  }
}
```

#### 4. `GET /get_hubspot_owners`
Retrieve all HubSpot owners.

**Headers:**
- `X-API-KEY`: Your valid API key.

**Response Example:**
```json
[
  {
    "id": "12345",
    "email": "owner1@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  {
    "id": "67890",
    "email": "owner2@example.com",
    "firstName": "Jane",
    "lastName": "Smith"
  }
]
```

### Error Handling

The app returns appropriate HTTP status codes and error messages in case of invalid API keys, missing parameters, or internal API failures.

### Logging

The application logs important events, such as successful or failed API calls, into the `app.log` file as well as to the console.

## Deployment

To deploy the Flask app, ensure your environment variables are set and the required dependencies are installed. The app can run in Docker, DigitalOcean, or other services supporting Flask apps.

## License
This project is licensed under the MIT License.
