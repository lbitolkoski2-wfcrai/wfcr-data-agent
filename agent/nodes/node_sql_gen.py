from schemas.data_agent_schema import SQLGenAgentResponse

class SQLGenNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
    
    async def run(self, ctx):
        confluence_context = ctx.agent_context['confluence_context']['response']['result']        
        filtered_tables = [f"{k['dataset']}.{k['table']}" for k in ctx.agent_context['filter_tables']['response']['result']['datasets']]
        gcp_context = [k for k in ctx.global_context['gcp_columns_schema'] if k["qualified_name"] in filtered_tables]
        result = await self.assistant.run_assistant(
            ctx,
            "sql_gen",
            SQLGenAgentResponse,
            additional_context={
                "confluence_context": confluence_context, 
                "gcp_schema_context": gcp_context
            }
        )
        ctx.agent_context['sql_gen'] = result
        return ctx