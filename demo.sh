#!/bin/bash

echo "=== XLSForm Generator Demo ==="
echo ""

echo "1. Creating a simple feedback survey..."
python main.py "Create a simple survey to collect user feedback with name, email, rating (1-5), and comments fields"

echo ""
echo "2. Creating a medical clinic patient survey..."
python main.py "Create a survey for a medical clinic to collect patient information including name, age, gender, symptoms, and preferred treatment. Include a rating question for overall satisfaction."

echo ""
echo "=== Demo Complete ==="
echo "Check the generated XLSForm files and JSON results in the current directory."