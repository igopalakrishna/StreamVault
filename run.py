#!/usr/bin/env python3
"""
CS-GY 6083 - Project Part II
Streaming Platform Web Application

Entry point for the Flask application.
Run with: python run.py
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode for development - disable in production
    # Port 5001 to avoid conflict with macOS AirPlay Receiver on port 5000
    app.run(debug=True, host='0.0.0.0', port=5001)
