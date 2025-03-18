from atlassian import Confluence
import json, toml
import dotenv
import os
import logging

class ConfluenceConnector(): 
    '''
    This class interfaces with the Confluence API to:
    - Initialize the Confluence connection
    - Retrieve pages with specified labels
    - Provide a consistent interface for retrieving confluence page content
    - Retrieve html content for each page
    '''
    def __new__(cls, config=None):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConfluenceConnector, cls).__new__(cls)
        return cls.instance

    def __init__(self, config=None):
        dotenv.load_dotenv()
        self.config = config
        self.create_connection()

    def create_connection(self):
        confluence = Confluence(
            url=self.config['confluence']['connector']['base_url'], #Base URL for Confluence instance
            username=os.getenv('CONFLUENCE_API_EMAIL'), #TODO - move all auth to secrets manager
            password=os.getenv('CONFLUENCE_API_KEY')
        )
        
        if not confluence:
            raise Exception("Confluence API failed to initialize.")
        else:
            logging.info("Confluence API initialized.")
        self.connection = confluence

    def get_pages_by_label(self, label):
        pages = self.connection.get_all_pages_by_label(label, expand='version,ancestors')
        return pages
    
    def get_page_by_id(self, page_id, doc_format='body.storage'): 
        return self.connection.get_page_by_id(page_id, expand=doc_format)

    def get_page_data(self, page_id):
        page = self.get_page_by_id(page_id)
        return page

    # end generic confluence functions | begin WFCR Space specific functions

    def get_gcp_mapping(self, **kwargs):
        """
        Returns a mapping of confluence pages to GCP table and dataset names.
        {confluence_page_id: {table_name: table_name, dataset_page_id: dataset_id, dataset_name: dataset_name, conf_label: conf_label}}
        """
        dataset_label = self.config['confluence']['connector']['dataset_label']
        table_label = self.config['confluence']['connector']['table_label']

        if (dataset_label is None) or (table_label is None):
            logging.error("Failed to retrieve dataset or table labels for confluence API.")
            return None

        dataset_pages = self.get_pages_by_label(dataset_label)
        table_pages = self.get_pages_by_label(table_label)

        gcp_mapping = {self.trim_ct(page["id"]):self.trim_ct(page["title"]) for page in dataset_pages} 
        table_mapping = {}
        for table in table_pages:
            table_title = self.trim_ct(table["title"])
            parent_dataset = None
            parent_id = None
            for ancestor in table["ancestors"]:
                parent_trimmed = self.trim_ct(ancestor["title"])
                if parent_trimmed in gcp_mapping.values():
                    parent_dataset = parent_trimmed
                    parent_id = ancestor["id"]
                    break
            table_mapping[table["id"]] = {
                "table_name": table_title, 
                "dataset_page_id": parent_id,
                "dataset_name": parent_dataset,
                "conf_label": dataset_label if parent_dataset is not None else table_label # If no parent then is a dataset
            }
        return table_mapping

    def get_gcp_context(self, page_ids=None, **kwargs):
        """
        Gets the confluence page content for all GCP Tables.
        page_ids = [confluence_page_id]
        """
        gcp_mapping = kwargs.get('gcp_mapping', self.get_gcp_mapping())
        # Filter table_mapping to include only specified page_ids
        if page_ids is not None:
            gcp_mapping = {k: v for k, v in gcp_mapping.items() if k in page_ids}
        
        # Get raw page content for all requested pages
        for page_id in gcp_mapping.keys():
            page_ctx = self.get_page_by_id(page_id)
            page_body = page_ctx['body']['storage']['value']

            if page_body is None:
                logging.error(f"Failed to retrieve page content for {gcp_mapping[page_id]}. ")
            else:
                logging.info(f"Successfully retrieved page content for {gcp_mapping[page_id]}.")
                gcp_mapping[page_id]["content"] = page_body

        gcp_context = {v["dataset_name"]: {"tables": {}, "dataset_content": None} for v in gcp_mapping.values()}

        for table_id, table_info in gcp_mapping.items():
            table_name = table_info["table_name"]
            table_content = table_info["content"]
            dataset_name = table_info["dataset_name"]

            if gcp_context.get(dataset_name) is not None:
                gcp_context[dataset_name]["tables"][table_name] = table_content
        #TODO: add dataset content to gcp_context (table content only for now)
        return gcp_context
    
    def get_pages_from_qualified_names(self, qualified_names: list[str], **kwargs): #eg. ['product.sales']
        page_ids = self.get_page_ids_from_qualified_names(qualified_names, **kwargs)
        return self.get_gcp_context(page_ids, **kwargs)

    def get_page_ids_from_qualified_names(self, qualified_names: list[str], **kwargs):
        gcp_mapping = kwargs.get('gcp_mapping', self.get_gcp_mapping())
        page_ids = [k for k, v in gcp_mapping.items() if f"{v['dataset_name']}.{v['table_name']}" in qualified_names]
        return page_ids

    def trim_ct(self, title): # Get the dataset or table name from the page title
        return title.split(" ")[0].lower()
    