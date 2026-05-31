#!/bin/bash
# Create .env file for Bank Statement Distribution System

echo "Creating .env file..."

# Generate encryption key
KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create .env file
cat > .env << EOF
# Bank Statement Distribution System - Environment Variables

# Encryption Key (auto-generated)
ENCRYPTION_KEY=$KEY

# Database Credentials
DB_USER=postgres
DB_PASSWORD=postgres

# Email Credentials
EMAIL_USER=test@example.com
EMAIL_PASSWORD=test123

# Admin Email Addresses (comma-separated)
ADMIN_EMAILS=admin@example.com

# Environment
ENVIRONMENT=development
EOF

echo "✅ .env file created successfully!"
echo ""
echo "Contents:"
cat .env
echo ""
echo "You can now run: python main.py init"
