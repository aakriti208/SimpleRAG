#!/bin/bash
# SimpleRAG Quick Install Script
# Downloads and installs SimpleRAG in one command

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

clear
print_header "=========================================="
print_header "SimpleRAG Quick Installer"
print_header "=========================================="
echo ""

# Check for git
print_info "Checking prerequisites..."
if ! command -v git &> /dev/null; then
    print_error "Git is not installed"
    echo "Please install git from https://git-scm.com/"
    exit 1
fi
print_success "Git found"

# Get repository URL
REPO_URL="${SIMPLERAG_REPO_URL:-https://github.com/aakriti208/SimpleRAG}"
print_info "Repository: $REPO_URL"
echo ""

# Ask for installation directory
read -p "Installation directory [./SimpleRAG]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-./SimpleRAG}

# Expand tilde if present
INSTALL_DIR="${INSTALL_DIR/#\~/$HOME}"

# Check if directory exists
if [ -d "$INSTALL_DIR" ]; then
    echo ""
    print_info "Directory $INSTALL_DIR already exists"
    read -p "Remove and reinstall? (y/N): " CONFIRM
    if [[ $CONFIRM =~ ^[Yy]$ ]]; then
        print_info "Removing existing directory..."
        rm -rf "$INSTALL_DIR"
        print_success "Removed"
    else
        print_error "Installation cancelled"
        exit 1
    fi
fi

echo ""
print_info "Cloning repository to $INSTALL_DIR..."
git clone "$REPO_URL" "$INSTALL_DIR"
print_success "Repository cloned"

# Change to installation directory
cd "$INSTALL_DIR"

# Make install script executable
chmod +x install.sh

echo ""
print_header "=========================================="
print_header "Starting Installation"
print_header "=========================================="
echo ""

# Run the installation script
./install.sh

echo ""
print_header "=========================================="
print_header "Quick Install Complete!"
print_header "=========================================="
echo ""
print_info "SimpleRAG has been installed to: $INSTALL_DIR"
echo ""
echo "To get started:"
echo "  cd $INSTALL_DIR"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
