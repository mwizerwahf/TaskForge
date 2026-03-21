import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from app package
from app import create_app

# Create the Flask app instance
app = create_app()

# Vercel serverless function handler
# This is the entry point for Vercel
if __name__ != '__main__':
    # Running on Vercel
    pass
else:
    # Local development
    try:
        from app import socketio
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except ImportError:
        app.run(debug=True, host='0.0.0.0', port=5000)
