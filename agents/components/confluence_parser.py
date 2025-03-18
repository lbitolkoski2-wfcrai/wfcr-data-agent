from bs4 import BeautifulSoup
class ConfluenceParser:
    
    @staticmethod
    def parse_confluence_context(raw_table_context):
        """
        Strips the unnecessary information from the raw confluence context 
        to reduce the number of tokens in the prompt
        args:
            raw_table_context (dict): The raw confluence context
        returns:
            confluence_context (dict): The processed confluence context
        """
        for dataset, dataset_data in raw_table_context.items():
            for table, html_content in dataset_data["tables"].items():
                dataset_data["tables"][table] = ConfluenceParser.parse_confluence_body(html_content)
        return raw_table_context

    def parse_confluence_body(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
    
        for tag in soup.find_all(['style', 'script', 'meta', 'link']):
            tag.decompose()
        
        cleaned_html = str(soup)  
        return cleaned_html