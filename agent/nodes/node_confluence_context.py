import logging
import agent_utils.components.confluence_parser as confluence_parser
import agent_utils.schemas.data_agent_schema as data_agent_schema

class ConfluenceContextNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
        self.confluence_connector = agent.confluence_connector

    async def run(self, ctx):
        filtered_tables = ctx.agent_context['filter_tables']['response']['result']
        pages_to_retrieve = [f"{t["table"]}" for t in filtered_tables["datasets"]]
        logging.info(f"Node: confluence_context - Pages to retrieve: {pages_to_retrieve}")
        raw_table_context = self.confluence_connector.get_pages_from_qualified_names(pages_to_retrieve)
        raw_table_context = confluence_parser.ConfluenceParser.parse_confluence_context(raw_table_context)
        result = await self.assistant.run_assistant(
            ctx,
            "confluence_context",
            data_agent_schema.ConfluenceAgentResponse,
            additional_context={"raw_table_context": raw_table_context}
        )
        ctx.agent_context['confluence_context'] = result
        return ctx
    