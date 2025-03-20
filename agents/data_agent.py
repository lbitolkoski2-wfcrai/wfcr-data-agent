import connectors.confluence_connector as confluence_connector
import connectors.bq_connector as bq_connector
import connectors.openai_connector as openai_connector
from collections import defaultdict

import toml, json, os
import logging
from langgraph.graph import StateGraph
from agents.components.assistant import Assistant
from agents.components.confluence_parser import ConfluenceParser
import schemas.data_agent_schema as data_agent_schema
import asyncio

logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

class DataAgent:
    """
    Data Agent: pull data from various sources and generate SQL queries
    """
    def __init__(self):
        self.config = toml.load("config/bundled.toml") # Move to GCS
        self.load_connectors()
        self.global_agent_context = {}
        self.assistant = Assistant(self.openai_connector, self.config)

    def load_connectors(self):
        self.bq_connector = bq_connector.BigQueryConnector(self.config)
        self.confluence_connector = confluence_connector.ConfluenceConnector(self.config)
        self.openai_connector = openai_connector.OpenAIConnector(self.config)
        
    def node_global_context(self, ctx): 
        logging.info("Node: load_global_context - Loading...")
        ctx.global_context['gcp_tables_schema'] = self.bq_connector.project_tables() 
        ctx.global_context['gcp_confluence_mappings'] = self.confluence_connector.get_gcp_mapping()
        ctx.global_context['gcp_columns_schema'] = self.bq_connector.project_columns()
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
        pages_to_retrieve = [f"{t["dataset"]}.{t["table"]}" for t in filtered_tables["datasets"]]
        logging.info(f"Node: confluence_context - Pages to retrieve: {pages_to_retrieve}")
        raw_table_context = self.confluence_connector.get_pages_from_qualified_names(pages_to_retrieve)
        raw_table_context = ConfluenceParser.parse_confluence_context(raw_table_context)
        result = self.assistant.run_assistant(
            ctx,
            "confluence_context",
            data_agent_schema.ConfluenceAgentResponse,
            additional_context={"raw_table_context": raw_table_context}
        )
        return result
    
    def node_sql_gen(self, ctx):
        confluence_context = ctx.agent_context['confluence_context']['response']['response_msg']
        filtered_tables = [f"{k['dataset']}.{k['table']}" for k in ctx.agent_context['filter_tables']['response']['response_msg']['datasets']]
        gcp_context = [k for k in ctx.global_context['gcp_columns_schema'] if k["qualified_name"] in filtered_tables]
        return self.assistant.run_assistant(
            ctx,
            "sql_gen",
            data_agent_schema.SQLGenAgentResponse,
            additional_context={
                "confluence_context": confluence_context, 
                "gcp_schema_context": gcp_context}
        )
    
    async def node_execute_sql(self, ctx):
        is_valid_bq_sql = self.bq_connector.validate_query(ctx.agent_context['sql_gen']['response']['response_msg']['sql'])
        ctx.agent_context['sql_gen']['response']['response_msg']['valid'] = is_valid_bq_sql
        if not is_valid_bq_sql:
            logging.error(f"Node: execute_sql - Invalid SQL: {ctx.agent_context['sql_gen']['response']['response_msg']['sql']}")
            return ctx
        if is_valid_bq_sql:
            destination_tbl = f"gcp-wow-food-fco-auto-dev.xwfcrauto.{ctx.job_id}" #TODO| Move to config
            bq_job = self.bq_connector.async_execute_query(
                ctx.agent_context['sql_gen']['response']['response_msg']['sql'],
                destination=destination_tbl,
                write_disposition="WRITE_TRUNCATE",
                job_timeout_ms=1000*60*3,
                labels={"job_id": ctx.job_id, "agent": "data_agent"}
            )
            await bq_job.result()
            logging.info(f"Node: execute_sql - Job {ctx.job_id} completed")
            ctx.agent_context['sql_gen']['bq_job'] = bq_job
        return ctx

    def compile_execution_graph(self):
        schema = data_agent_schema.DataAgentContext
        graph_builder = StateGraph(schema)
        #========= Node Definitions ==========
        graph_builder.add_node("start", lambda ctx: ctx) 
        graph_builder.add_node("load_global_context", lambda ctx: self.node_global_context(ctx))  # Load shared context from cache
        graph_builder.add_node("filter_tables", lambda ctx: self.node_filter_tables(ctx)) # Filter the tables based on user request
        graph_builder.add_node("confluence_context", lambda ctx: self.node_confluence_context(ctx))  # Load the confluence context
        graph_builder.add_node("sql_gen", lambda ctx: self.node_sql_gen(ctx))# Generate SQL based on user request
        graph_builder.add_node("execute_sql", lambda ctx: self.node_execute_sql(ctx)) # TBI
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

### Test ###
test_task_prompt = "Hi - please pull me data for all own brand products over past 6m"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

data_agent = DataAgent()
data_agent_graph = data_agent.compile_execution_graph()
import uuid
inputs = {
        "email_context": {
            "task_prompt": f"{test_task_prompt}"
        },
        "global_context": {},  
        "agent_context": {},  
        "responses": [], 
        "info": {},
        "job_id": f"{str(uuid.uuid4())}"
    }
app = data_agent_graph.invoke(inputs)

result = app['agent_context']['sql_gen']['response']['response_msg']['sql']
print(result)

with open(f'./output/llm/data_agent_output_transient.json', 'w') as f:
    json.dump(app['agent_context'], f, indent=4)
