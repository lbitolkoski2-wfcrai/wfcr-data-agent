import os
import dotenv
from google.cloud import bigquery
import json
import logging

class BigQueryConnector():
    def __init__(self, config):
        self.config = config
        dotenv.load_dotenv()
        self.client = bigquery.Client(
            project=config['bigquery']['project_id']
        )


        self.valid_datasets = config['bigquery']['valid_datasets']
        self.project_id = config['bigquery']['project_id']
        self.gcp_region = config['bigquery']['region']
        logging.info(f"BigQueryConnector: initialized with project_id: {self.project_id} and region: {self.gcp_region}")
        logging.info(f"BigQueryConnector: Valid datasets: {self.valid_datasets}")
        pass

    def project_tables(self):
        schema_query = f"""
        SELECT CONCAT(table_schema,'.', table_name) as qualified_name, table_schema as dataset_name, table_name, option_value as description
        FROM `{self.project_id}.{self.gcp_region}.INFORMATION_SCHEMA.TABLE_OPTIONS`  
        WHERE option_name="description"
        AND table_schema in UNNEST({self.valid_datasets})
        """
        schema_query = schema_query.replace('\n', '').replace('\r', '')
        rows = self.execute_query(schema_query)
        results = [dict(row) for row in rows]
        return results

    def project_columns(self):
        schema_query = f"""
            SELECT CONCAT(table_schema,'.', table_name) as qualified_name, table_schema as dataset_name, table_name, column_name, data_type
            FROM `{self.project_id}.{self.gcp_region}.INFORMATION_SCHEMA.COLUMNS` 
            WHERE table_schema in UNNEST({self.valid_datasets})"""
        schema_query = schema_query.replace('\n', '').replace('\r', '')
        rows = self.execute_query(schema_query)
        results = [dict(row) for row in rows]
        return results
    
    def execute_query(self, query):
        query_result = self.client.query_and_wait(query)
        return query_result


