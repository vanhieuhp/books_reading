#!/bin/bash
# Setup script for Day 5-6: Apache Avro

echo "Setting up Day 5-6: Apache Avro..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Install Avro Python library
echo ""
echo "Installing Avro Python library..."
pip3 install avro-python3

if [ $? -eq 0 ]; then
    echo "✓ avro-python3 installed successfully"
else
    echo "⚠️  Warning: Failed to install avro-python3"
    echo "   Try: pip3 install avro-python3"
fi

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "import avro.schema; import avro.io; print('✓ Avro modules imported successfully')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "Run the demos with:"
    echo "  python3 avro_demo.py          # Main demonstration"
    echo "  python3 evolution_practice.py # Practice exercises"
    echo ""
else
    echo "⚠️  Warning: Avro modules not available"
    echo "   The demos will show conceptual examples only"
    echo ""
fi
