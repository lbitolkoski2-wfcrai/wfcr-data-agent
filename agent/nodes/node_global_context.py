import logging

class GlobalContextNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
        self.bq_connector = agent.bq_connector
        self.confluence_connector = agent.confluence_connector
        pass

    def run(self, ctx): 
        logging.info("Node: load_global_context - Loading...")
        ctx.global_context['gcp_tables_schema'] = self.bq_connector.project_tables() 
        ctx.global_context['gcp_confluence_mappings'] = self.confluence_connector.get_gcp_mapping()
        ctx.global_context['gcp_columns_schema'] = self.bq_connector.project_columns()
        logging.info("Node: load_global_context - Global Context loaded")
        return ctx