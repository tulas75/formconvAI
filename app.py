"""
Flask API for FormConv AI
========================

This module provides a Flask web API for generating forms using AI.
"""

from flask import Flask, request, jsonify
import os
import sys

# Add the parent directory to the path so we can import the formconv package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from formconv.core import generate_form_json

app = Flask(__name__)


@app.route('/responseAI.json', methods=['POST'])
def generate_form():
    """
    Generate a form JSON from a user query.
    
    Expected JSON input:
    {
        "query": "Create a survey to collect user feedback with name, email, rating, and comments"
    }
    
    Returns:
    {
        "success": true,
        "data": {...}  // The generated JSON form
    }
    """
    try:
        # Get the query from the request
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter'
            }), 400
        
        user_query = data['query']
        
        # Generate the form JSON
        json_result = generate_form_json(user_query)
        
        # Return the result
        return jsonify({
            'success': True,
            'data': json_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
