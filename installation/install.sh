#!/bin/bash
# SimpleRAG Installation Script for Unix/Mac/Linux
# This script automates the installation of SimpleRAG for Canvas LMS

set -e  # Exit on error

echo "=========================================="
echo "SimpleRAG Installation Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check Python version
print_info "Checking Python installation..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
        PYTHON_CMD=python3
    else
        print_error "Python 3.11+ is required. Found: $PYTHON_VERSION"
        echo "Please install Python 3.11 or newer from https://www.python.org/"
        exit 1
    fi
else
    print_error "Python 3 is not installed."
    echo "Please install Python 3.11+ from https://www.python.org/"
    exit 1
fi
print_success "Python found: $($PYTHON_CMD --version)"

# Create virtual environment
print_info "Creating virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi
$PYTHON_CMD -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded"

# Install requirements
print_info "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Setup environment file
print_info "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.template .env
    print_success "Created .env file from template"
    print_info "Please edit .env file with your Canvas API credentials"
else
    print_info ".env file already exists (skipping)"
fi

# Check for Ollama
print_info "Checking for Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is installed"

    # Check if Ollama service is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama service is running"

        # Check if model is installed
        print_info "Checking for gemma:2b model..."
        if ollama list | grep -q "gemma:2b"; then
            print_success "gemma:2b model is installed"
        else
            print_info "Installing gemma:2b model (this will take a few minutes)..."
            ollama pull gemma:2b
            print_success "gemma:2b model installed"
        fi
    else
        print_info "Ollama is installed but not running"
        print_info "Start it with: ollama serve"
    fi
else
    print_error "Ollama is not installed"
    echo ""
    echo "Ollama is required for answer generation."
    echo "Installation instructions:"
    echo "  macOS/Linux: Visit https://ollama.ai and download the installer"
    echo "  After installation, run:"
    echo "    ollama serve"
    echo "    ollama pull gemma:2b"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p data/chroma_db
mkdir -p data/metadata
print_success "Directories created"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your Canvas API credentials:"
echo "   Edit the .env file with your Canvas API token and course IDs"
echo ""
echo "2. Activate the virtual environment (in new terminal sessions):"
echo "   source venv/bin/activate"
echo ""
echo "3. Ingest your Canvas content:"
echo "   python scripts/ingest_data.py --course YOUR_COURSE_ID --full"
echo ""
echo "4. Start the web interface:"
echo "   python app.py"
echo "   Then visit: http://localhost:8000"
echo ""
echo "For help, see README.md or contact support"
echo ""
