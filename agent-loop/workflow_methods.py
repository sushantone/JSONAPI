
from typing import List

from src.providers.llm_provider import LLMProvider
from src.utils import storage_provider
# from src.data_ingest import DataIngestion
from langchain_core.tools import tool

def foreach_output(steps, output_items, callback):
        responses = []
        if output_items and isinstance(output_items, List) and steps and isinstance(steps, List):
            iteration = 0
            for out_item in output_items:
                iteration = iteration + 1
                response = callback(steps, out_item, iteration)
                responses.append(response)
        return responses

@tool
def save_response_tool(project_root, file_name, iteration, response):
    """
    Save the response to a file.
    Args:
        project_root (str): The root directory of the project.
        file_name (str): The name of the file to save the response to.
        iteration (int): The iteration number.
        response (str): The response to save.
    """
    return storage_provider.save_response(project_root, file_name, iteration, response)

@tool
def get_dir_contents_tool(project_root, path_patterns, asdict=False, recursive = False):
    """
    Get the contents of a directory and its subdirectories.
    Args:
        project_root (str): The root directory of the project.
        path_patterns (str): The path patterns to search for files, | separated strings for multiple patterns.
        asdict (bool): Whether to return the contents as a list of dictionaries.
        recursive (bool): Whether to search recursively in subdirectories.
    """
    return storage_provider.get_dir_contents(project_root, path_patterns, asdict, recursive)

FlowMethodMap = {
    "foreach_output": foreach_output,
    "run_ollama": LLMProvider().run_llm,
    "get_dir_contents": storage_provider.get_dir_contents,
    "save_response": storage_provider.save_response,
    "split_content": storage_provider.split_content,
    "run_ollama_vec": LLMProvider().run_llm_vec,
#    "vectorize_data" : DataIngestion.vectorize_data,
#    "create_insert_milvus_collection" : DataIngestion.create_insert_milvus_collection,
    "copy_file": storage_provider.copy_file,
    "clean_directory": storage_provider.clean_directory,
    "run_ollama_v2": LLMProvider().run_llm_v2,
    "get_dir_contents_tool": get_dir_contents_tool,
    "save_response_tool": save_response_tool,
}