from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Union, Optional

class DataAgentContextRequest(BaseModel):
    email_context: Dict[str, Any] # Email context for the request
    global_context: Dict[str, Any] # Shared context preopulated for all agents
    agent_context: Dict[str, Any] # Context populated for each agent upon completion {agent_name: agent_context}
    responses: List[str] # Responses from all agents {agent_name: response} 
    info: Dict[str, Any] # Potential logging information or other metadata
    job_id: str

class DataAgentResponse(BaseModel):
    html_response: str
    table_id: str
    sheet_id: str
    n_rows: str
    data: Optional [Dict[str,Any]] = {}


class ConfluenceTable(BaseModel):
    resource_name: str
    overview: str
    key_fields: Optional[Dict] = None
    sample_query: Optional[str] = None
    usage_instructions: Optional[str] = None
    notes: Optional[str] = None
    dependencies: Optional[List[str]] = None
    additional_details: Optional[str] = None


class EmailContext(BaseModel):
    task_prompt: str

class Dataset(BaseModel):
    model_config = ConfigDict(extra='allow')
    dataset: str
    table: str




#======== LLM Structured Input/Response Schema ========
#===== LLM Response Schema =====
class FilterAgentResponse(BaseModel):
    datasets: List[Dataset]

class ConfluenceAgentResponse(BaseModel):
    datasets: List[ConfluenceTable]

#===== Confluence Agent ===============================
class ConfluenceAgentRequest(BaseModel):
    datasets: List[Dataset]

class ConfluenceAgentResponse(BaseModel):
    datasets: List[ConfluenceTable]

#===== Filter Agent ===================================
class FilterAgentRequest(BaseModel):
    prompt: str
    bq_tables: List[str]

class FilterAgentResponse(BaseModel):
    datasets: List[Dataset]


#===== SQLExec Agent ==================================
class SQLExecAgentRequest(BaseModel):
    sql: str

class SQLExectAgentResponse(BaseModel):
    sql: str

#===== SQLGen Agent ===================================
class SQLGenAgentResponse(BaseModel):
    sql: str

class SQLGenAgentRequest(BaseModel):
    sql: str
#=========================================================