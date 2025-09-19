"""
Core functionality for FormConv AI
"""
import datetime
import os
import shutil
import time
from typing import Optional

import requests
from dotenv import load_dotenv
from mcp import StdioServerParameters
from smolagents import CodeAgent, LiteLLMModel, MCPClient


def generate_timestamped_filename(base_name: str, extension: str) -> str:
    """Generate a timestamped filename in the format base_name_YYYYMMDD_HHMMSS.extension

    Args:
        base_name: The base name for the file
        extension: The file extension including the dot (e.g., '.xlsx')

    Returns:
        str: The full path with timestamped filename
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"output_files/{base_name}_{timestamp}{extension}"


def ensure_output_directory() -> str:
    """Ensure the output_files directory exists

    Returns:
        str: The path to the output directory
    """
    output_dir = "output_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


# MCP filesystem parameters
mcp_filesystem = StdioServerParameters(
    command="uvx",
    args=["excel-mcp-server", "stdio"]
)


def load_model() -> LiteLLMModel:
    """Load model configuration from environment variables

    Returns:
        LiteLLMModel: The configured model
    """
    load_dotenv()  # Load environment variables from .env file

    # Get model configuration from environment variables
    model_id = os.getenv("MODEL_ID", "deepinfra/Qwen/Qwen3-Next-80B-A3B-Instruct")
    api_key = os.getenv("DEEPINFRA_API_KEY")

    # Initialize the model with API key if provided
    if api_key:
        model = LiteLLMModel(model_id=model_id, temperature=0.6, api_key=api_key)
    else:
        model = LiteLLMModel(model_id=model_id, temperature=0.6)

    return model


def load_xlsform_prompt() -> str:
    """Load the XLSForm prompt template

    Returns:
        str: The content of the XLSForm prompt template
    """
    with open("xlsform_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def validate_xlsform_file(filename: str) -> bool:
    """Check if the XLSForm file was created successfully in the current directory

    Args:
        filename: The name of the file to validate

    Returns:
        bool: True if the file exists and is valid, False otherwise
    """
    current_dir = os.getcwd()
    expected_file_path = os.path.join(current_dir, filename)

    # Check if file exists in the expected location
    if os.path.exists(expected_file_path):
        if os.path.getsize(expected_file_path) > 0:
            return True
        print(f"Error: XLSForm file '{filename}' is empty.")
        return False

    # File not in expected location, check if it exists elsewhere and move it
    print(f"Error: XLSForm file '{filename}' was not created in the current directory.")
    # Try to find and move the file from other locations
    if find_and_move_file(filename, expected_file_path):
        # Check if moved file is valid
        if os.path.getsize(expected_file_path) > 0:
            print(f"Successfully moved '{filename}' to current directory.")
            return True
        print(f"Error: Moved XLSForm file '{filename}' is empty.")
        return False
    return False


def find_and_move_file(filename: str, expected_file_path: str) -> bool:
    """Find a file that might be in a different location and move it to the expected location

    Args:
        filename: The name of the file to find
        expected_file_path: The expected path where the file should be moved

    Returns:
        bool: True if the file was found and moved, False otherwise
    """
    # First, check if the file exists with just the basename in current directory
    simple_filename = os.path.basename(filename)
    if os.path.exists(simple_filename):
        try:
            shutil.move(simple_filename, expected_file_path)
            print(f"Moved '{simple_filename}' to '{expected_file_path}'")
            return True
        except Exception as e:
            print(f"Warning: Could not move file from '{simple_filename}': {e}")
            return False

    # Search for the file in common temporary locations
    search_paths = [
        "/tmp/",
        "/var/tmp/",
        os.path.expanduser("~/Downloads/"),
        os.path.expanduser("~/Desktop/"),
        os.getcwd()  # Also check current directory for any file with the name
    ]

    for search_path in search_paths:
        if os.path.exists(search_path):
            # Look for exact filename
            potential_path = os.path.join(search_path, simple_filename)
            if os.path.exists(potential_path):
                try:
                    shutil.move(potential_path, expected_file_path)
                    print(f"Moved '{simple_filename}' from '{search_path}' "
                          f"to '{expected_file_path}'")
                    return True
                except Exception as e:
                    print(f"Warning: Could not move file from '{potential_path}': {e}")

    # If not found in common locations, search more broadly (but not too broadly)
    try:
        # Search in home directory and subdirectories, but limit depth to avoid long searches
        home_dir = os.path.expanduser("~")
        for root, dirs, files in os.walk(home_dir):
            # Limit search depth to avoid searching the entire system
            depth = root[len(home_dir):].count(os.sep)
            if depth > 3:  # Don't go more than 3 levels deep
                dirs[:] = []  # Don't recurse deeper
                continue

            if simple_filename in files:
                potential_path = os.path.join(root, simple_filename)
                try:
                    shutil.move(potential_path, expected_file_path)
                    print(f"Moved '{simple_filename}' from '{root}' to '{expected_file_path}'")
                    return True
                except Exception as e:
                    print(f"Warning: Could not move file from '{potential_path}': {e}")
    except Exception as e:
        print(f"Warning: Could not search for misplaced file: {e}")

    return False


def create_xlsform(user_query: str, xlsform_filename: str, model: LiteLLMModel,
                  xlsform_prompt_template: str) -> bool:
    """Create an XLSForm based on user query using LLM

    Args:
        user_query: The user's query describing the survey to create
        xlsform_filename: The filename for the XLSForm
        model: The LLM model to use
        xlsform_prompt_template: The prompt template for XLSForm generation

    Returns:
        bool: True if the XLSForm was created successfully, False otherwise
    """
    try:
        with MCPClient([mcp_filesystem]) as mcp_tools:
            tools = list(mcp_tools)

            # Get the absolute path of the current directory
            current_dir = os.getcwd()
            expected_file_path = os.path.join(current_dir, xlsform_filename)

            # Extract just the filename without the path for the LLM
            simple_filename = os.path.basename(xlsform_filename)

            # Create the full prompt by combining the template with user query
            full_prompt = (
                f"{xlsform_prompt_template}\n\n"
                f"User Query: {user_query}\n\n"
                "Please generate a complete XLSForm structure that addresses the user's "
                "requirements. Return the result as a valid Excel file with the sheets "
                "(survey, choices, settings) properly formatted. Create the xlsx file "
                f"using excel-mcp-server tool. Save the file as '{simple_filename}' in "
                "the current folder.\n\n"
                "Important instructions:\n"
                "- ALWAYS create ALL three required sheets: survey, choices, and settings "
                "(even if empty)\n"
                "- DO NOT create any extra sheets like 'Sheet1'\n"
                "- Make sure to save the file properly in the current directory\n"
                "- Avoid any complex constraints or validation formulas\n"
                "- Ensure the file is saved with the exact name '{simple_filename}'\n"
                "- The choices sheet must have the headers 'list_name', 'name', 'label' "
                "even if empty\n"
                "- Every sheet must have headers in the first row\n"
            )

            agent = CodeAgent(tools=tools,
                              model=model,
                              additional_authorized_imports=[
                                "json",
                                "os"
                             ])
            result = agent.run(full_prompt)
            print(f"XLSForm creation result: {result}")

            # Wait a moment for file creation
            time.sleep(2)

            # Check if the file was created in the current directory
            if os.path.exists(simple_filename):
                # Move the file to the output_files directory
                try:
                    shutil.move(simple_filename, expected_file_path)
                    print(f"Moved file from '{simple_filename}' to '{expected_file_path}'")
                    return True
                except Exception as e:
                    print(f"Error moving file: {e}")
                    return False

            # Try to find the file in common locations and move it
            print(f"File '{simple_filename}' not found in current directory. Searching...")
            found = False
            search_paths = ["/tmp/", "/var/tmp/", os.path.expanduser("~/Downloads/")]
            for search_path in search_paths:
                potential_path = os.path.join(search_path, simple_filename)
                if os.path.exists(potential_path):
                    try:
                        shutil.move(potential_path, expected_file_path)
                        print(f"Found and moved file from '{potential_path}' "
                              f"to '{expected_file_path}'")
                        found = True
                        break
                    except Exception as e:
                        print(f"Error moving file from '{potential_path}': {e}")

            if not found:
                print(f"File '{simple_filename}' not found in common locations.")
                # List files in current directory to help debug
                print("Files in current directory:")
                for file in os.listdir("."):
                    print(f"  {file}")
                return False

            # Validate that the file was created in the correct location
            if not validate_xlsform_file(xlsform_filename):
                return False

            print(f"Successfully verified XLSForm file at {expected_file_path}")
            return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error creating XLSForm: {e}")
        return False


def convert_xlsx_to_json(xlsform_filename: str, json_filename: str) -> Optional[str]:
    """Convert the XLSX file to JSON using the formconv API

    Args:
        xlsform_filename: The name of the XLSForm file to convert
        json_filename: The name of the JSON file to create

    Returns:
        Optional[str]: The JSON result if successful, None otherwise
    """
    # First check if the XLSForm file exists
    if not validate_xlsform_file(xlsform_filename):
        return None

    try:
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, xlsform_filename)

        print("Sending XLSForm to conversion service...")
        # Use requests to convert XLSX to JSON
        with open(file_path, "rb") as file:
            files = {"excelFile": file}
            response = requests.post(
                "https://formconv.herokuapp.com/result.json",
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            # Check if the response is valid JSON
            if response.text.strip().startswith("{") or response.text.strip().startswith("["):
                print("Successfully converted XLSX to JSON")
                # Save the JSON result to a file with timestamped name
                json_file_path = os.path.join(current_dir, json_filename)
                with open(json_file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                return response.text
            print("Error: Server did not return valid JSON")
            print(f"Server response: {response.text}")
            print(f"Response headers: {response.headers}")
            return None
        print(f"Error converting XLSX to JSON: {response.status_code} - "
                  f"{response.text}")
        # Save the error response for debugging
        error_file_path = os.path.join(current_dir, "output_files/conversion_error.txt")
        with open(error_file_path, "w", encoding="utf-8") as f:
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Response: {response.text}\n")
            f.write(f"Headers: {response.headers}\n")
        return None

    except requests.exceptions.Timeout:
        print("Error: Timeout while converting XLSX to JSON. The server may be unavailable.")
        return None
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error sending request: {e}")
        return None


def generate_form_json(user_query: str) -> str:
    """Generate a form JSON from a user query

    Args:
        user_query: The user's query describing the survey to create

    Returns:
        str: The generated JSON form

    Raises:
        RuntimeError: If form generation fails
    """
    # Ensure output directory exists
    ensure_output_directory()

    # Load model and prompt
    model = load_model()
    xlsform_prompt_template = load_xlsform_prompt()

    # Generate timestamped filenames
    xlsform_filename = generate_timestamped_filename("xlsform_survey", ".xlsx")
    json_filename = generate_timestamped_filename("form_result", ".json")

    # Create the XLSForm
    xlsform_result = create_xlsform(user_query, xlsform_filename, model, xlsform_prompt_template)
    if not xlsform_result:
        raise RuntimeError("Failed to create XLSForm")

    # Convert to JSON
    print("Converting XLSX to JSON...")
    json_result = convert_xlsx_to_json(xlsform_filename, json_filename)

    if json_result:
        print(f"JSON result saved to {json_filename}")
        return json_result
    raise RuntimeError("Form conversion failed")
