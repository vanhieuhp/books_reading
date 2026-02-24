#!/bin/bash
# Setup script for Day 3-4: Protocol Buffers

echo "Setting up Day 3-4: Protocol Buffers..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check for protoc
if command -v protoc &> /dev/null; then
    echo "✓ protoc found: $(protoc --version)"
else
    echo ""
    echo "⚠️  protoc not found!"
    echo ""
    echo "Install Protocol Buffers compiler:"
    echo "  macOS:   brew install protobuf"
    echo "  Linux:   sudo apt-get install protobuf-compiler"
    echo "  Windows: choco install protoc"
    echo ""
    echo "Or download from: https://grpc.io/docs/protoc-installation/"
    echo ""
    echo "The demo will still run but show conceptual examples only."
    echo ""
fi

# Install Python protobuf library
echo ""
echo "Installing Python protobuf library..."
pip3 install protobuf

if [ $? -eq 0 ]; then
    echo "✓ protobuf Python library installed"
else
    echo "⚠️  Warning: Failed to install protobuf"
fi

# Try to generate protobuf code
if command -v protoc &> /dev/null; then
    echo ""
    echo "Generating Protocol Buffers code..."
    cd "$(dirname "$0")"
    protoc --python_out=. --proto_path=proto proto/user.proto
    
    if [ $? -eq 0 ]; then
        echo "✓ Generated user_pb2.py"
    else
        echo "⚠️  Warning: Failed to generate protobuf code"
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Run the demo with:"
echo "  python3 protobuf_demo.py"
echo ""
