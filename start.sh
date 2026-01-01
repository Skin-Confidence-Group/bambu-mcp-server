#!/bin/bash
# Quick start script for local development

set -e

echo "🚀 Starting Bambu MCP Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -e .

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your Bambu credentials"
    exit 1
fi

# Start the server
echo "✅ Starting server on http://localhost:8000"
echo "📡 MCP endpoint: http://localhost:8000/sse"
echo "🏥 Health check: http://localhost:8000/health"
echo ""
python -m bambu_mcp.server
