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

dotenv.load_dotenv()
app = FastAPI()
data_agent = data_agent.DataAgent()
data_agent_graph = data_agent.compile_execution_graph()

@app.get("/dataRequest")
def dataRequest():
    """
    Entrypoint for email requests routed to the data-agent
    Kicks off autogen actors to process the request
    """
    # 1. Parse the request
    # 2. Kick off the data-agent
    # 3. Return the job id as the response
    job_id = str(uuid.uuid4())
    logging.info("Data Agent | processing job:" + job_id)
    inputs = {
        "email_context": {
            "task_prompt": "How many customers purchased our beef burger range in the past 6 months?"
        },
        "global_context": {},  
        "agent_context": {},  
        "responses": {}, 
        "info": {} 
    }

    app = data_agent_graph.invoke(inputs)

    from langchain_core.runnables.graph import MermaidDrawMethod
    with open('./output/llm/data_agent_graph.png', 'wb') as f:
        f.write(data_agent_graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API))
    with open(f'./output/llm/data_agent_output_{uuid.uuid4()}.json', 'w') as f:
        json.dump(app['agent_context'], f, indent=4)
    
    return {"status": "success", "job_id": job_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)