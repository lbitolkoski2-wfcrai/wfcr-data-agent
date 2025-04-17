import os
from schemas.data_agent_schema import SQLGenAgentRequest, SQLGenAgentResponse
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm



import toml

"""
Generate SQL queries based on the context provided by the user.
"""
sql_gen_agent = LlmAgent(
    name="sql_gen_agent",
    model=LiteLlm(model=os.getenv("LLM_DEPLOYMENT_NAME","")),
    description="Generate SQL queries based on the context provided by the user.",
    input_schema= SQLGenAgentRequest,
    output_schema=SQLGenAgentResponse,
    
)