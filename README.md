# XLSForm Generator

This script generates XLSForm files using LLM and converts them to JSON format using the formconv service.

## How it works

1. The user provides a description of the survey they want to create
2. The script uses an LLM (through smolagents) to generate a proper XLSForm structure
3. The XLSForm is created using the excel-mcp-server
4. The XLSForm is then converted to JSON using the formconv service

## Environment Variables

The script uses the following environment variables, which should be set in a `.env` file:

- `DEEPINFRA_API_KEY`: Your DeepInfra API key (optional but recommended)
- `MODEL_ID`: The model ID to use (defaults to `deepinfra/Qwen/Qwen3-Next-80B-A3B-Instruct`)

Example `.env` file:
```env
DEEPINFRA_API_KEY=your_api_key_here
MODEL_ID=deepinfra/Qwen/Qwen3-Next-80B-A3B-Instruct
```

## Usage

```bash
python main.py "Create a survey to collect user feedback with name, email, rating (1-5), and comments fields"
```

## Features

- Generates valid XLSForm files with proper structure
- Handles survey, choices, and settings sheets
- Avoids conversion issues by not using complex constraints
- Automatically converts XLSX to JSON format with timestamped filenames
- Handles file path issues with the excel-mcp-server
- Uses environment variables for configuration
- Generates timestamped filenames to avoid overwriting previous results
- All generated files are saved in the `output_files` directory

## Filename Convention

Files are saved with timestamped names to avoid conflicts in the `output_files` directory:
- XLSForm files: `output_files/xlsform_survey_YYYYMMDD_HHMMSS.xlsx`
- JSON result files: `output_files/form_result_YYYYMMDD_HHMMSS.json`

## Requirements

- Python 3.8+
- smolagents
- excel-mcp-server (installed via uvx)
- requests
- pandas
- openpyxl

## Installation

```bash
pip install -r requirements.txt
```

## Example

```bash
python main.py "Create a medical clinic survey to collect patient information including name, age, gender, symptoms, and preferred treatment. Include a rating question for overall satisfaction."
```

This will generate an XLSForm file and convert it to JSON format, saving both files in the `output_files` directory with timestamped filenames.