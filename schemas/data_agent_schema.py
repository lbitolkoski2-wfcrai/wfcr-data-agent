from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Union

class DataAgentContext(BaseModel):
    email_context: Dict[str, Any] # Email context for the request
    global_context: Dict[str, Any] # Shared context preopulated for all agents
    agent_context: Dict[str, Any] # Context populated for each agent upon completion {agent_name: agent_context}
    responses: List[str] # Responses from all agents {agent_name: response} 
    info: Dict[str, Any] # Potential logging information or other metadata
    job_id: str


class ConfluenceTable(BaseModel):
    table_name: str
    table_id: str
    limitations: List[str]

class EmailContext(BaseModel):
    task_prompt: str

class Dataset(BaseModel):
    model_config = ConfigDict(extra='allow')
    dataset: str
    table: str

#===== LLM Response Schema =====
class FilterAgentResponse(BaseModel):
    datasets: List[Dataset]

class ConfluenceAgentResponse(BaseModel):
    datasets: List[Dataset]

class SQLGenAgentResponse(BaseModel):
    sql: str

