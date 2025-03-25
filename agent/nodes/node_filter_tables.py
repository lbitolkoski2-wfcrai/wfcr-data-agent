import agent_utils.schemas.data_agent_schema as data_agent_schema

class FilterTablesNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
        
    async def run(self, ctx):
        gcp_table_context = ctx.global_context['gcp_tables_schema']
        result = await self.assistant.run_assistant(
            ctx,
            "filter_tables",
            data_agent_schema.FilterAgentResponse,
            additional_context={"gcp_table_context": gcp_table_context}
        )
        ctx.agent_context['filter_tables'] = result
        return ctx