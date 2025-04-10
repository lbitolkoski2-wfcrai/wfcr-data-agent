"""
Cloud Run Entry Point WebServer for the data-agent
Responsible for initializing the FastAPI server and defining the endpoints for the data-agent
Initializes the required DataAdapters and Actors for processing the requests
"""
import uvicorn

import agent.data_agent as data_agent
from fastapi import FastAPI, Request as fastapi_request
import dotenv
import json
import uuid
import logging

dotenv.load_dotenv()
app = FastAPI()
data_agent = data_agent.DataAgent()
data_agent_graph = data_agent.compile_execution_graph()

@app.post("/process_data_request")
async def data_request(request: fastapi_request):
    """
    Entrypoint for email requests routed to the data-agent
    """
    request_json = await request.json()  # Pull email context from request {email_context: {task_prompt: "prompt"}}
    email_context = request_json.get('email_context', {})
    if email_context.get('task_prompt', None) is None:
        return {"error": "email_context or email_context.task_prompt not found in request"}
    if email_context.get('request_id', None) is None:
        email_context['request_id'] = str(uuid.uuid4()) # testing purposes, remove when request_id is added to the email context

    graph_inputs = data_agent.build_graph_inputs(email_context=email_context)
    logging.info("Data Agent | processing job:" + graph_inputs['job_id'])
    data_agent_result = await data_agent_graph.ainvoke(graph_inputs) 
    return data_agent_result['agent_context']

@app.get("/")
def health_check():
    return {"status": "Okay!"}

import os
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000,  log_level="info")