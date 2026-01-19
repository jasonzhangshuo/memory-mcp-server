#!/bin/bash
# Quick start script for Personal Memory MCP Server

set -e

echo "=========================================="
echo "Personal Memory MCP Server - Quick Start"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if database exists
if [ ! -f "memory.db" ]; then
    echo "🗄️  Initializing database and loading seed data..."
    python storage/seed.py
else
    echo "✅ Database already exists"
fi

# Verify setup
echo ""
echo "🔍 Verifying setup..."
python verify_setup.py

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure MCP Server in Cursor (see MCP_CONFIG.md)"
echo "2. Run: python main.py (to start the server)"
echo "3. Test with: python test_mcp_tools.py"
echo ""
