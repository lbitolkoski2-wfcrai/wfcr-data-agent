import logging
from agent_utils.logging_utils import observe_with_tags
from langfuse.decorators import observe, langfuse_context

class GlobalContextNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
        self.bq_connector = agent.bq_connector
        self.confluence_connector = agent.confluence_connector
        pass

    @observe(name="bigquery context", capture_input=False)
    def run(self, ctx): 
        logging.info("Node: load_global_context - Loading...")
        ctx.global_context['gcp_tables_schema'] = self.bq_connector.project_tables() 
        ctx.global_context['gcp_columns_schema'] = self.bq_connector.project_columns()
        logging.info("Node: load_global_context - Global Context loaded")
        langfuse_context.update_current_trace(ctx.global_context)
        return ctx