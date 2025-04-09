from schemas.data_agent_schema import FilterAgentResponse

class FilterTablesNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
        
    async def run(self, ctx):
        gcp_table_context = ctx.global_context['gcp_tables_schema']
        result = await self.assistant.run_assistant(
            ctx,
            "filter_tables",
            FilterAgentResponse,
            additional_context={"gcp_table_context": gcp_table_context},
        )
        ctx.agent_context['filter_tables'] = result
        return ctx