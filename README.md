# XLSForm Generator

This script generates XLSForm files using LLM and converts them to JSON format using the formconv service.

## How it works

1. The user provides a description of the survey they want to create
2. The script uses an LLM (through smolagents) to generate a proper XLSForm structure
3. The XLSForm is created using the excel-mcp-server
4. The XLSForm is then converted to JSON using the formconv service

## Usage

```bash
python main.py "Create a survey to collect user feedback with name, email, rating (1-5), and comments fields"
```

## Features

- Generates valid XLSForm files with proper structure
- Handles survey, choices, and settings sheets
- Avoids conversion issues by not using complex constraints
- Automatically converts XLSX to JSON format
- Handles file path issues with the excel-mcp-server

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

This will generate an XLSForm file and convert it to JSON format, saving both files in the current directory.