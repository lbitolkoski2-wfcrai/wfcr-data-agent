import logging
import asyncio

class ExecuteSQLNode():
    def __init__(self, agent):
        self.assistant = agent.assistant
        self.bq_connector = agent.bq_connector  
    
    async def run(self, ctx):
            logging.info(f"Node: executing SQL for job {ctx.job_id}")
            sql_response = ctx.agent_context['sql_gen']['response']['result']
            is_valid_bq_sql = self.bq_connector.validate_query(sql_response['sql'])
            sql_response['valid'] = is_valid_bq_sql

            if not is_valid_bq_sql:
                logging.error(f"Node: execute_sql - Invalid SQL: {sql_response['sql']}")
                return ctx

            destination_tbl = f"gcp-wow-food-fco-auto-dev.xwfcrauto.{ctx.job_id}"  # TODO: Move to config
            bq_job = await self.bq_connector.async_execute_query(
                sql_response['sql'],
                destination=destination_tbl,
                write_disposition="WRITE_TRUNCATE",
                job_timeout_ms=1000 * 60 * 3,
                labels={"job_id": ctx.job_id, "agent": "data_agent"}
            )
            await asyncio.sleep(10) # Wait for dry run to validate and short queries to complete
            # TODO: Add error handling for job failure 
            # Status is either |done|error|processing|
            ctx.agent_context['execute_sql'] = {"job_id": bq_job.result.job_id, "status": bq_job.result.state, "destination": destination_tbl}
            return ctx
