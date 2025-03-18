import logging

class Assistant:
    """
    Helper class to perform LLM Calls using Assistants
    """
    def __init__(self, openai_connector, config):
        self.openai_connector = openai_connector
        self.config = config
    
    def run_assistant(self, ctx, assistant_name, response_schema, additional_context):
        """"
        Initializes the Assistant with the required context and configuration
        args:
            ctx (dict): The context object to be passed to the assistant
            assistant_name (str): The name of the assistant to be called
            response_schema (pydantic model): The schema for the response from the assistant
            additional_context (dict): Additional context to be passed to the assistant for formatting the prompt
        returns:
            response (dict): The response from the assistant conforming to the response_schema
        """
        config = self.config[assistant_name]['openai']
        assistant_id = config['assistant_id']
        base_prompt = config['prompt']
        task_prompt = ctx.email_context['task_prompt']
        formatted_prompt = base_prompt.format(task_prompt=task_prompt, **additional_context)
        logging.info(f"Node: {assistant_name} - Running assistant: {assistant_name} | id: {assistant_id}")
        response_spec = {"type": "json_schema",
            "json_schema": {
                "name": f"{assistant_name}_response_schema",
                "schema": response_schema.model_json_schema()
            }
        }
        response = self.openai_connector.prompt_assistant(assistant_id,formatted_prompt,response_spec=response_spec)
        ctx.agent_context[assistant_name] = {
            "prompt": task_prompt,
            "assistant_id": assistant_id,
            "response": response
        }
        return ctx