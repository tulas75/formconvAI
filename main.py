#!/usr/bin/env python3
"""
FormConv AI - Command Line Interface
===================================

This script generates XLSForm files using LLM and converts them to JSON format.
"""

import os
import sys
from formconv.core import generate_form_json

# Add the parent directory to the path so we can import the formconv package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    """Main function to run the command line interface."""
    if len(sys.argv) < 2:
        print("Usage: python main.py '<your survey description>'")
        print("\nExample: python main.py 'Create a survey to collect patient "
              "information including name, age, symptoms, and treatment preferences'")
        sys.exit(1)

    user_query = " ".join(sys.argv[1:])
    print(f"Creating form for: {user_query}")

    try:
        json_result = generate_form_json(user_query)
        print("Form generation completed successfully!")
        print("JSON result:")
        print(json_result)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Form generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
