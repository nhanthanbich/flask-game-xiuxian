#!/bin/bash
# Script chạy Flask Web App

echo "══════════════════════════════════════════════════"
echo "   Tu Tiên Ký - Flask Web Application"
echo "══════════════════════════════════════════════════"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 không được cài đặt!"
    exit 1
fi

echo "✓ Python 3: $(python3 --version)"

# Install dependencies
echo ""
echo "Đang cài đặt dependencies..."
pip3 install -r requirements.txt

# Set environment
export FLASK_APP=flask_app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run Flask app
echo ""
echo "══════════════════════════════════════════════════"
echo "   Khởi động Flask server..."
echo "   Mở trình duyệt: http://localhost:5000"
echo "══════════════════════════════════════════════════"
echo ""

python3 flask_app.py
