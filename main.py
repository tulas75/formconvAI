import sys
import os
import requests
import shutil
from smolagents import MCPClient, CodeAgent, LiteLLMModel, ToolCallingAgent, tool
from mcp import StdioServerParameters
from dotenv import load_dotenv
#import litellm
#litellm._turn_on_debug()

mcp_filesystem = StdioServerParameters(
    command="uvx",
    args=["excel-mcp-server", "stdio"]
)

load_dotenv()  # Load environment variables from .env file

model_id="deepinfra/moonshotai/Kimi-K2-Instruct-0905"
#model = LiteLLMModel(model_id=model_id, drop_params = True, temperature ="0.6")
model = LiteLLMModel(model_id=model_id, temperature=0.6)

# Read the XLSForm prompt template
with open("xlsform_prompt.txt", "r") as f:
    xlsform_prompt_template = f.read()

def validate_xlsform_file():
    """Check if the XLSForm file was created successfully"""
    # Check in current directory first
    if os.path.exists("xlsform_survey.xlsx"):
        if os.path.getsize("xlsform_survey.xlsx") > 0:
            return True
        else:
            print("Error: XLSForm file 'xlsform_survey.xlsx' is empty.")
            return False
    
    # Check in /tmp directory
    if os.path.exists("/tmp/xlsform_survey.xlsx"):
        if os.path.getsize("/tmp/xlsform_survey.xlsx") > 0:
            # Copy file to current directory
            shutil.copy("/tmp/xlsform_survey.xlsx", "xlsform_survey.xlsx")
            print("Copied XLSForm file from /tmp to current directory")
            return True
        else:
            print("Error: XLSForm file '/tmp/xlsform_survey.xlsx' is empty.")
            return False
    
    print("Error: XLSForm file 'xlsform_survey.xlsx' was not created.")
    return False

def create_xlsform(user_query):
    """Create an XLSForm based on user query using LLM"""
    try:
        with MCPClient([mcp_filesystem]) as mcp_tools:
            tools = list(mcp_tools)
            
            # Create the full prompt by combining the template with user query
            full_prompt = f"""
{xlsform_prompt_template}

User Query: {user_query}

Please generate a complete XLSForm structure that addresses the user's requirements. 
Return the result as a valid Excel file with the sheets (survey, choices, settings) properly formatted.
Save the file as 'xlsform_survey.xlsx' in the current working directory.

Important instructions:
- ONLY create the required sheets: survey, choices, and settings
- DO NOT create any extra sheets like 'Sheet1'
- Make sure to save the file properly
- Avoid any complex constraints or validation formulas
- Ensure all file paths are correctly specified
"""
            
            agent = CodeAgent(tools=tools, 
                              model=model, 
                              #add_base_tools=True,
                              additional_authorized_imports=[
                                "json",
                                "pandas",
                             ],                      
            )
            result = agent.run(full_prompt)
            print(f"XLSForm creation result: {result}")
            
            # Validate that the file was created
            if not validate_xlsform_file():
                return False
                
            return result
    except Exception as e:
        print(f"Error creating XLSForm: {e}")
        return False

def convert_xlsx_to_json():
    """Convert the XLSX file to JSON using the formconv API"""
    # First check if the XLSForm file exists
    if not validate_xlsform_file():
        return None
        
    try:
        print("Sending XLSForm to conversion service...")
        # Use requests to convert XLSX to JSON
        with open("xlsform_survey.xlsx", "rb") as file:
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
                # Save the JSON result to a file
                with open("form_result.json", "w") as f:
                    f.write(response.text)
                return response.text
            else:
                print("Error: Server did not return valid JSON")
                print(f"Server response: {response.text}")
                print(f"Response headers: {response.headers}")
                return None
        else:
            print(f"Error converting XLSX to JSON: {response.status_code} - {response.text}")
            # Save the error response for debugging
            with open("conversion_error.txt", "w") as f:
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Response: {response.text}\n")
                f.write(f"Headers: {response.headers}\n")
            return None
    except requests.exceptions.Timeout:
        print("Error: Timeout while converting XLSX to JSON. The server may be unavailable.")
        return None
    except Exception as e:
        print(f"Error sending request: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py '<your survey description>'")
        print("\nExample: python main.py 'Create a survey to collect patient information including name, age, symptoms, and treatment preferences'")
        sys.exit(1)
    
    user_query = " ".join(sys.argv[1:])
    print(f"Creating XLSForm for: {user_query}")
    
    # Create the XLSForm
    xlsform_result = create_xlsform(user_query)
    if not xlsform_result:
        print("Failed to create XLSForm. Exiting.")
        sys.exit(1)
    
    # Convert to JSON
    print("Converting XLSX to JSON...")
    json_result = convert_xlsx_to_json()
    
    if json_result:
        print("Form conversion completed successfully!")
        print("JSON result saved to form_result.json")
    else:
        print("Form conversion failed. Check conversion_error.txt for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
