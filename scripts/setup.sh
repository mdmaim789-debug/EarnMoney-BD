#!/bin/bash

# EarnMoney BD - Quick Setup Script
# This script sets up the project for local development

echo "🚀 EarnMoney BD - Setup Script"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your BOT_TOKEN"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p webapp/js
mkdir -p webapp/css
mkdir -p logs

# Initialize database
echo "🗄️  Initializing database..."
python -c "import asyncio; from database.database import init_db; asyncio.run(init_db())"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env and add your BOT_TOKEN"
echo "2. Run API: uvicorn api.main:app --reload"
echo "3. Run Bot: python bot/main.py"
echo ""
echo "💡 For production deployment, see README.md"
