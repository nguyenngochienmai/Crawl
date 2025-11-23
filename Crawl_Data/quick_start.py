#!/usr/bin/env python3
"""
Quick Start Script - Chạy crawler với các cấu hình đơn giản
"""

import asyncio
import sys
from crawler import MicrosoftLearnCrawler


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║       Microsoft Learn Course Crawler - Quick Start           ║
║                     SC-200T00 Course                          ║
╚═══════════════════════════════════════════════════════════════╝
""")


async def run_full_crawl():
    """Crawl TOÀN BỘ course (tất cả modules và units)"""
    print_banner()
    print("🔥 MODE: FULL CRAWL - Crawl tất cả modules và units")
    print("⏱️  Thời gian dự kiến: 1-2 giờ\n")
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=None,      # Crawl TẤT CẢ modules
        crawl_units=True       # Crawl chi tiết units
    )
    
    crawler.save_data("sc200_full_complete.json")
    print("\n✅ Hoàn thành! Kiểm tra folder output/")


async def run_quick_test():
    """Crawl nhanh 5 modules đầu tiên (để test)"""
    print_banner()
    print("⚡ MODE: QUICK TEST - Crawl 5 modules đầu")
    print("⏱️  Thời gian dự kiến: 5-10 phút\n")
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=5,         # Chỉ 5 modules
        crawl_units=True
    )
    
    crawler.save_data("sc200_test_5modules.json")
    print("\n✅ Test hoàn thành! Kiểm tra folder output/")


async def run_modules_only():
    """Chỉ crawl danh sách modules, không crawl chi tiết units"""
    print_banner()
    print("📋 MODE: MODULES ONLY - Chỉ lấy danh sách modules")
    print("⏱️  Thời gian dự kiến: 1-2 phút\n")
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=None,
        crawl_units=False      # KHÔNG crawl chi tiết
    )
    
    crawler.save_data("sc200_modules_list.json")
    print("\n✅ Hoàn thành! Kiểm tra folder output/")


async def run_custom():
    """Tùy chỉnh số lượng modules"""
    print_banner()
    print("🎯 MODE: CUSTOM CRAWL\n")
    
    try:
        num_modules = int(input("Nhập số modules muốn crawl (hoặc 0 cho tất cả): "))
        if num_modules < 0:
            num_modules = 0
    except ValueError:
        print("❌ Số không hợp lệ, sử dụng 10 modules")
        num_modules = 10
        
    max_modules = None if num_modules == 0 else num_modules
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=max_modules,
        crawl_units=True
    )
    
    filename = f"sc200_custom_{num_modules if num_modules > 0 else 'all'}_modules.json"
    crawler.save_data(filename)
    print(f"\n✅ Hoàn thành! Kiểm tra output/{filename}")


def main():
    print_banner()
    print("Chọn chế độ crawl:")
    print("  1️⃣  Quick Test (5 modules đầu) - Nhanh nhất")
    print("  2️⃣  Modules Only (danh sách modules) - Rất nhanh")
    print("  3️⃣  Full Crawl (tất cả modules + units) - Đầy đủ nhất")
    print("  4️⃣  Custom (tùy chỉnh số modules)")
    print("  0️⃣  Thoát\n")
    
    choice = input("Lựa chọn của bạn: ").strip()
    
    if choice == "1":
        asyncio.run(run_quick_test())
    elif choice == "2":
        asyncio.run(run_modules_only())
    elif choice == "3":
        confirm = input("⚠️  Full crawl có thể mất 1-2 giờ. Tiếp tục? (y/n): ")
        if confirm.lower() == 'y':
            asyncio.run(run_full_crawl())
        else:
            print("❌ Đã hủy")
    elif choice == "4":
        asyncio.run(run_custom())
    elif choice == "0":
        print("👋 Tạm biệt!")
    else:
        print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi người dùng")
        print("💡 Các checkpoint đã được lưu trong folder output/")
        sys.exit(0)
