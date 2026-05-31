#!/bin/bash
# Setup script for Bank Statement Distribution System

set -e

echo "=========================================="
echo "Bank Statement Distribution System Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p credentials
mkdir -p temp

# Copy environment file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your actual values"
fi

# Generate encryption key
echo ""
echo "Generating encryption key..."
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" >> .env.generated
echo "Encryption key generated in .env.generated"
echo "Please copy it to your .env file"

# Initialize database
echo ""
read -p "Do you want to initialize the database now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Initializing database..."
    python main.py init
fi

# Validate configuration
echo ""
read -p "Do you want to validate configuration now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Validating configuration..."
    python main.py validate-config
fi

echo ""
echo "=========================================="
echo "Setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your actual credentials"
echo "2. Place Google Drive credentials in credentials/google_drive_credentials.json"
echo "3. Edit config.yaml with your settings"
echo "4. Run 'python main.py test-connections' to test connections"
echo "5. Run 'python main.py run' to execute the workflow"
echo ""
