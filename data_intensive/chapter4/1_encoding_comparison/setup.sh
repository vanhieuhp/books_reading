#!/bin/bash
# Setup script for Day 1: Encoding Fundamentals

echo "Setting up Day 1: Encoding Fundamentals..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Install msgpack
echo ""
echo "Installing required packages..."
pip3 install msgpack

if [ $? -eq 0 ]; then
    echo "✓ msgpack installed successfully"
else
    echo "⚠️  Warning: Failed to install msgpack"
    echo "   You can still run the demo with JSON and Pickle only"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Run the demo with:"
echo "  python3 encoding_demo.py"
echo ""
