# Data Agent

The Data Agent is designed to handle generic requests for data.
retrieve organizational and data context.
construct queries and execute them.

## Schemas

Responses and Context for every node in the graph and every LLM API call is defined by a pydantic model.

Shared Context through each node in the agent is defined by the DataAgentContext Schema. 
i.e every node has the type signature:  DataAgentContext -> DataAgentContext

LLM Assistants will always return structured JSON with the response defined by a pydantic model.

## Config

All configuration file outside of sensitive information resides in ./config
- shared.toml: basic configuration of the data agent
- prompts/
    - ensure prompt/filename.toml is unique eg. prompt/sql_gen.toml
    - [prompts.filename.instructions] : System Prompt
    - [prompts.filename.task]         : User Prompt

Run `make bundle` to create `bundled.toml` which is the single configuration file consumed by the agent.

## Deployment

The Data agent is deployed as a FastAPI HTTP Server with the endpoint

### API Documentation
Endpoint: `/process_data_request`
Method: `POST`

Description:
This endpoint serves as the entry point for email requests routed to the data-agent. It processes the email context provided in the request and returns the result as a JSON after invoking the data agent's execution graph.

Request Body:
The request body should be a JSON object containing the `email_context` field. The `email_context` should include a `task_prompt` which is necessary for processing the request.

```json
{
  "email_context": {
    "task_prompt": "Your task prompt here"
  }
}
```

Request Response:
Example response JSON
```json
{
  "agent_context": {
    "confluence_context": // Confluence LLM Response Schema
  }
}
```