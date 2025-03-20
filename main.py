"""
Cloud Run Entry Point WebServer for the data-agent
Responsible for initializing the FastAPI server and defining the endpoints for the data-agent
Initializes the required DataAdapters and Actors for processing the requests
"""

import agents.data_agent as data_agent
from fastapi import FastAPI, Request as fastapi_request
import dotenv
import json
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
dotenv.load_dotenv()

app = FastAPI()
data_agent = data_agent.DataAgent()
data_agent_graph = data_agent.compile_execution_graph()

@app.get("/dataRequest")
def dataRequest():
    """
    Entrypoint for email requests routed to the data-agent"
    """
    email_context = {} # Pull email context from request
    job_id = str(uuid.uuid4())

    logging.info("Data Agent | processing job:" + job_id)
    
    inputs = {
        "email_context": email_context,
        "global_context": {},  
        "agent_context": {},  
        "responses": [], 
        "info": {},
        "job_id": job_id 
    }

    app = data_agent_graph.invoke(inputs)
    result = app['agent_context']['sql_gen']['response']['response_msg']['sql']
    return {
        "sql": result,
        "job_id": app['job_id']
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)