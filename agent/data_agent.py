from agent_utils.connectors import ConfluenceConnector, BigQueryConnector, LLMConnector, GoogleCloudStorageConnector
from agent_utils.components.assistant import Assistant

from agent.nodes.node_confluence_context import ConfluenceContextNode
from agent.nodes.node_filter_tables import FilterTablesNode
from agent.nodes.node_global_context import GlobalContextNode
from agent.nodes.node_sql_gen import SQLGenNode

from langfuse import Langfuse

import uuid
import toml, json, os
import logging
from langgraph.graph import StateGraph
import dotenv

import schemas.data_agent_schema as data_agent_schema
import asyncio

from agent_utils.logging_utils import langfuse_wrap_node
class DataAgent:
    """
    Data Agent: pull data from various sources and generate SQL queries
    """
    def __init__(self):
        dotenv.load_dotenv()
        self.load_connectors()
        self.global_agent_context = {}
        self.assistant = Assistant(self.llm_connector, self.config)
        self.set_logging()

    def load_connectors(self):
        self.gcs_connector = GoogleCloudStorageConnector()
        self.config = self.gcs_connector.load_toml()        
        self.bq_connector = BigQueryConnector(self.config)
        self.confluence_connector = ConfluenceConnector(self.config)
        self.llm_connector = LLMConnector(self.config, "openai") #TODO: Add support for Gemini

    def set_logging(self):
        logging_config = self.config["logging"]
        logging.basicConfig(level=logging_config['level'], format='%(asctime)s - %(levelname)s - %(message)s')
        if (logging_config.get('hide_http_logs', False)):
            logging.getLogger("openai").setLevel(logging.ERROR) 
            logging.getLogger("httpx").setLevel(logging.ERROR)
  
    def compile_execution_graph(self):
        schema = data_agent_schema.DataAgentContext
        graph_builder = StateGraph(schema)
        #========= Node Definitions =============
        nodes = {
            "load_global_context": GlobalContextNode(self),
            "filter_tables": FilterTablesNode(self),
            "confluence_context": ConfluenceContextNode(self),
            "sql_gen": SQLGenNode(self)
        }
        graph_builder.add_node("start", lambda ctx: ctx)
        for name, node in nodes.items():
            graph_builder.add_node(name, langfuse_wrap_node(node.run,name)) # Node must have a run method

        #========= Edge Definitions ==========
        graph_builder.add_edge("start", "load_global_context")
        graph_builder.add_edge("load_global_context", "filter_tables")
        graph_builder.add_edge("filter_tables", "confluence_context")
        graph_builder.add_edge("confluence_context", "sql_gen")
        # graph_builder.add_edge("sql_gen", "execute_sql")
        # graph_builder.add_edge("execute_sql", "post_processing")
        #========= Compile ===================
        graph_builder.set_entry_point("start")
        app = graph_builder.compile()
        return app
    
    def build_graph_inputs(self, **kwargs):
        inputs = {
            "email_context": kwargs.get('email_context', {}),
            "global_context": self.global_agent_context,
            "agent_context": {},
            "responses": [],
            "info": {},
            "job_id": kwargs.get('job_id', str(uuid.uuid4()))
        }
        return inputs
