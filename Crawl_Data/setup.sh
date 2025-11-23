#!/bin/bash
# Script setup nhanh cho crawler

echo "🚀 Microsoft Learn Course Crawler - Setup Script"
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt"
    echo "   Cài đặt Python từ: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python3 đã cài đặt: $(python3 --version)"
echo ""

# Tạo virtual environment nếu chưa có
if [ ! -d ".venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment đã được tạo"
else
    echo "✅ Virtual environment đã tồn tại"
fi
echo ""

# Activate virtual environment và cài dependencies
echo "📥 Cài đặt dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies đã được cài đặt"
echo ""

# Cài đặt Playwright browsers
echo "🌐 Cài đặt Playwright browsers..."
python -m playwright install chromium
echo "✅ Playwright browsers đã được cài đặt"
echo ""

# Tạo output directory
mkdir -p output
echo "✅ Output directory đã được tạo"
echo ""

echo "🎉 SETUP HOÀN TẤT!"
echo ""
echo "📝 Cách sử dụng:"
echo "   1. Crawl nhanh (test):     python quick_start.py"
echo "   2. Crawl tùy chỉnh:        python crawler.py"
echo "   3. Xem hướng dẫn:          cat README.md"
echo ""
echo "💡 Tip: Sử dụng quick_start.py để chọn chế độ crawl phù hợp"
echo ""
