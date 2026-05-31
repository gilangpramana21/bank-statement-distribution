#!/bin/bash
# Quick test script for Bank Statement Distribution System

set -e

echo "=========================================="
echo "Bank Statement Distribution System - Test"
echo "=========================================="
echo ""

# Create virtual environment
echo "1. Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "2. Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "3. Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "4. Installing dependencies..."
pip install -r requirements.txt -q

# Test compile all Python files
echo "5. Compiling all Python files..."
python3 -m compileall src/ -q

# Test imports
echo "6. Testing module imports..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

print("   ✓ Testing models...")
from src import models

print("   ✓ Testing entity_grouper...")
from src import entity_grouper

print("   ✓ Testing package_manager...")
from src import package_manager

print("   ✓ Testing security...")
from src import security

print("   ✓ Testing logger...")
from src import logger

print("")
print("✅ All modules imported successfully!")
print("")
EOF

echo "=========================================="
echo "Test completed successfully!"
echo "=========================================="
echo ""
echo "To use the system:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Configure .env file"
echo "  3. Run: python main.py --help"
echo ""
