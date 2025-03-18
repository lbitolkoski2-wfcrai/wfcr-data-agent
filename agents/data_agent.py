import connectors.confluence_connector as confluence_connector
import connectors.bq_connector as bq_connector
import connectors.openai_connector as openai_connector
from collections import defaultdict

import toml, json
import logging
from langgraph.graph import StateGraph
from pydantic import ValidationError
from agents.components.assistant import Assistant
from agents.components.confluence_parser import ConfluenceParser
import schemas.data_agent_schema as data_agent_schema

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataAgent:
    """
    Data Agent: pull data from various sources and generate SQL queries
    """
    def __init__(self):
        self.config = toml.load("config/bundled.toml") # Move to GCS
        self.load_connectors()
        self.global_agent_context = {} # Shared Context across all requests to the data agent
        self.assistant = Assistant(self.openai_connector, self.config)

    def load_connectors(self):
        self.bq_connector = bq_connector.BigQueryConnector(self.config)
        self.confluence_connector = confluence_connector.ConfluenceConnector(self.config)
        self.openai_connector = openai_connector.OpenAIConnector(self.config)
        
    def load_local_context(self, ctx, agent_name): # Load LLM Responses from disk for testing purposes
        with open(f'./output/llm/{agent_name}.json', 'r') as f:
            llm_result = json.load(f)
        ctx.agent_context[agent_name] = {"response":{"response_msg":llm_result}}
        ctx.responses[agent_name] = agent_name
        logging.info(f"Node: {agent_name} - Loaded Local Context")
        return ctx
    
    def node_global_context(self, ctx): # Load the global context | TODO - Cache this
        logging.info("Node: load_global_context - Loading...")
        ctx.global_context['gcp_tables_schema'] = self.bq_connector.project_tables() 
        ctx.global_context['gcp_confluence_mappings'] = self.confluence_connector.get_gcp_mapping()
        logging.info("Node: load_global_context - Global Context loaded")
        return ctx
    
    def node_filter_tables(self, ctx):
        gcp_table_context = ctx.global_context['gcp_tables_schema']
        return self.assistant.run_assistant(
            ctx,
            "filter_tables",
            data_agent_schema.FilterAgentResponse,
            additional_context={"gcp_table_context": gcp_table_context}
        )

    def node_confluence_context(self, ctx):
        filtered_tables = ctx.agent_context['filter_tables']['response']['response_msg']
        pages_to_retrieve = [t["table"] for t in filtered_tables["datasets"]]
        raw_table_context = self.confluence_connector.get_pages_from_qualified_names(pages_to_retrieve)
        raw_table_context = ConfluenceParser.parse_confluence_context(raw_table_context)
        return self.assistant.run_assistant(
            ctx,
            "confluence_context",
            data_agent_schema.ConfluenceAgentResponse,
            additional_context={"raw_table_context": raw_table_context}
        )
    
    def node_sql_gen(self, ctx):
        confluence_context = ctx.agent_context['confluence_context']['response']['response_msg']
        return self.assistant.run_assistant(
            ctx,
            "sql_gen",
            data_agent_schema.SQLGenAgentResponse,
            additional_context={"table_context": confluence_context}
        )
   
    def compile_execution_graph(self):
        schema = data_agent_schema.DataAgentContext
        graph_builder = StateGraph(schema)
        #========= Node Definitions ==========
        graph_builder.add_node("start", lambda ctx: ctx) 
        graph_builder.add_node("load_global_context", lambda ctx: self.node_global_context(ctx))  # Load shared context from cache
        
        graph_builder.add_node("filter_tables", lambda ctx: self.load_local_context(ctx, "filter_tables"))  # Filter the tables based on user request
        # graph_builder.add_node("confluence_context", lambda ctx: self.load_local_context(ctx, "confluence_context"))  # Load the confluence context
        # graph_builder.add_node("sql_gen", lambda ctx: self.load_local_context(ctx, "sql_gen"))  # Generate SQL based on user request

        # graph_builder.add_node("filter_tables", lambda ctx: self.node_filter_tables(ctx)) # Filter the tables based on user request
        graph_builder.add_node("confluence_context", lambda ctx: self.node_confluence_context(ctx))  # Load the confluence context
        graph_builder.add_node("sql_gen", lambda ctx: self.node_sql_gen(ctx))# Generate SQL based on user request
        graph_builder.add_node("execute_sql", lambda ctx: ctx) # TBI
        graph_builder.add_node("post_processing", lambda ctx: ctx) # TBI

        #========= Edge Definitions ==========
        graph_builder.add_edge("start", "load_global_context")
        graph_builder.add_edge("load_global_context", "filter_tables")
        graph_builder.add_edge("filter_tables", "confluence_context")
        graph_builder.add_edge("confluence_context", "sql_gen")
        graph_builder.add_edge("sql_gen", "execute_sql")
        graph_builder.add_edge("execute_sql", "post_processing")

        #========= Compile ===================
        graph_builder.set_entry_point("start")
        app = graph_builder.compile()
        return app

data_agent = DataAgent()
data_agent_graph = data_agent.compile_execution_graph()

logging.info("Data Agent | processing job:")
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
