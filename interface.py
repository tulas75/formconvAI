"""
Gradio Interface for FormConv AI
==============================

This module provides a Gradio web interface for testing the FormConv AI API.
Users can input survey queries and download the generated XLSX and JSON files.
"""

import os
import json
import tempfile
import requests
import gradio as gr


def generate_form(query: str) -> tuple:
    """
    Generate a form from a user query by calling the Flask API.
    
    Args:
        query (str): The user's survey query
        
    Returns:
        tuple: A tuple containing (xlsx_file_path, json_file_path, status_message)
    """
    if not query.strip():
        return None, None, "Please enter a survey query."
    
    try:
        # Call the Flask API endpoint
        api_url = "http://127.0.0.1:5001/responseAI.json"
        payload = {"query": query}
        
        response = requests.post(api_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                # Get the JSON data
                json_data = result.get("data")
                
                # Create temporary files for download
                xlsx_temp_path = None
                json_temp_path = None
                
                # Find the latest XLSX file in output_files directory
                output_dir = "output_files"
                if os.path.exists(output_dir):
                    xlsx_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx')]
                    if xlsx_files:
                        # Get the most recent XLSX file
                        xlsx_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
                        latest_xlsx = xlsx_files[0]
                        xlsx_temp_path = os.path.join(output_dir, latest_xlsx)
                
                # Create a temporary JSON file with the response data
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as json_temp:
                    # Parse and pretty print the JSON data
                    if isinstance(json_data, str):
                        try:
                            parsed_json = json.loads(json_data)
                            json.dump(parsed_json, json_temp, indent=2, ensure_ascii=False)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, write as is
                            json_temp.write(json_data)
                    else:
                        json.dump(json_data, json_temp, indent=2, ensure_ascii=False)
                    json_temp_path = json_temp.name
                
                status_message = "Form generated successfully! You can download the files below."
                return xlsx_temp_path, json_temp_path, status_message
            else:
                error_msg = result.get("error", "Unknown error occurred")
                return None, None, f"API Error: {error_msg}"
        else:
            return None, None, f"API Request Failed: {response.status_code} - {response.text}"
            
    except requests.exceptions.ConnectionError:
        return None, None, "Connection Error: Could not connect to the API. Please ensure the Flask server is running."
    except requests.exceptions.Timeout:
        return None, None, "Timeout Error: The request took too long to process."
    except Exception as e:
        return None, None, f"Unexpected Error: {str(e)}"


# Global variable to store the last generated files for download
last_generated_files: dict = {"xlsx": None, "json": None}


def generate_and_store(query: str) -> tuple:
    """
    Generate a form and store the file paths for later retrieval.
    
    Args:
        query (str): The user's survey query
        
    Returns:
        tuple: A tuple containing (status_message,)
    """
    xlsx_path, json_path, status = generate_form(query)
    
    # Store the file paths globally
    last_generated_files["xlsx"] = xlsx_path
    last_generated_files["json"] = json_path
    
    return (status,)


def get_xlsx_file() -> dict:
    """
    Get the path to the last generated XLSX file.
    
    Returns:
        dict: Dictionary with file path for Gradio or None if not available
    """
    xlsx_path = last_generated_files["xlsx"]
    if xlsx_path and os.path.exists(xlsx_path):
        return gr.update(value=xlsx_path, visible=True)
    return gr.update(visible=False)


def get_json_file() -> dict:
    """
    Get the path to the last generated JSON file.
    
    Returns:
        dict: Dictionary with file path for Gradio or None if not available
    """
    json_path = last_generated_files["json"]
    if json_path and os.path.exists(json_path):
        return gr.update(value=json_path, visible=True)
    return gr.update(visible=False)


def main():
    """Launch the Gradio interface"""
    with gr.Blocks(title="FormConv AI - Survey Generator") as demo:
        gr.Markdown("# FormConv AI - Survey Generator")
        gr.Markdown("Generate surveys from natural language queries and download XLSX/JSON files")
        
        with gr.Row():
            with gr.Column():
                query_input = gr.Textbox(
                    label="Survey Query",
                    placeholder="Enter your survey requirements (e.g., 'Create a survey to collect patient information including name, age, symptoms, and treatment preferences')",
                    lines=3
                )
                generate_btn = gr.Button("Generate Survey")
                
            with gr.Column():
                status_output = gr.Textbox(label="Status", interactive=False)
        
        with gr.Row():
            with gr.Column():
                xlsx_output = gr.File(label="Download XLSX File", file_types=[".xlsx"], visible=False)
            with gr.Column():
                json_output = gr.File(label="Download JSON File", file_types=[".json"], visible=False)
        
        generate_btn.click(
            fn=generate_and_store,
            inputs=query_input,
            outputs=[status_output]
        ).then(
            fn=get_xlsx_file,
            outputs=[xlsx_output]
        ).then(
            fn=get_json_file,
            outputs=[json_output]
        )
    
    return demo


if __name__ == "__main__":
    demo = main()
    demo.launch(server_name="0.0.0.0", server_port=7860)