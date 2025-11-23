#!/usr/bin/env python3
"""
Quick Start Script - Chạy crawler với các cấu hình đơn giản
"""

import asyncio
import sys
from ms_learn_crawler_fixed import MicrosoftLearnCrawler


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║       Microsoft Learn Course Crawler - Quick Start           ║
║                     SC-200T00 Course                          ║
╚═══════════════════════════════════════════════════════════════╝
""")


async def run_full_crawl():
    """Crawl TOÀN BỘ course (tất cả modules)"""
    print_banner()
    print("🔥 MODE: FULL CRAWL - Crawl tất cả modules")
    print("⏱️  Thời gian dự kiến: 30-60 phút\n")
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=None      # Crawl TẤT CẢ modules
    )
    
    crawler.save_data("sc200_full_complete.json")
    
    # Convert sang Markdown
    print("\n📝 Converting to Markdown...")
    crawler.convert_to_markdown("sc200_full_complete.md")
    
    print("\n✅ Hoàn thành! Kiểm tra folder output/")
    print("   - JSON: output/sc200_full_complete.json")
    print("   - Markdown: output/sc200_full_complete.md")


async def run_quick_test():
    """Crawl nhanh 3 modules đầu tiên (để test)"""
    print_banner()
    print("⚡ MODE: QUICK TEST - Crawl 3 modules đầu")
    print("⏱️  Thời gian dự kiến: 3-5 phút\n")
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=3         # Chỉ 3 modules
    )
    
    crawler.save_data("sc200_test_3modules.json")
    
    # Convert sang Markdown
    print("\n📝 Converting to Markdown...")
    crawler.convert_to_markdown("sc200_test_3modules.md")
    
    print("\n✅ Test hoàn thành! Kiểm tra folder output/")
    print("   - JSON: output/sc200_test_3modules.json")
    print("   - Markdown: output/sc200_test_3modules.md")


async def run_single_module():
    """Crawl chỉ 1 module để test nhanh"""
    print_banner()
    print("🎯 MODE: SINGLE MODULE - Crawl 1 module")
    print("⏱️  Thời gian dự kiến: 1-2 phút\n")
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=1         # Chỉ 1 module
    )
    
    crawler.save_data("sc200_single_module.json")
    
    # Convert sang Markdown
    print("\n📝 Converting to Markdown...")
    crawler.convert_to_markdown("sc200_single_module.md")
    
    print("\n✅ Hoàn thành! Kiểm tra folder output/")
    print("   - JSON: output/sc200_single_module.json")
    print("   - Markdown: output/sc200_single_module.md")


async def run_custom():
    """Tùy chỉnh số lượng modules"""
    print_banner()
    print("🎯 MODE: CUSTOM CRAWL\n")
    
    try:
        num_modules = int(input("Nhập số modules muốn crawl (hoặc 0 cho tất cả): "))
        if num_modules < 0:
            num_modules = 0
    except ValueError:
        print("❌ Số không hợp lệ, sử dụng 5 modules")
        num_modules = 5
        
    max_modules = None if num_modules == 0 else num_modules
    
    # Tùy chọn convert sang Markdown
    convert_md = input("Convert sang Markdown? (y/n, mặc định y): ").strip().lower()
    if convert_md == '':
        convert_md = 'y'
    
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    crawler = MicrosoftLearnCrawler(course_url)
    
    await crawler.crawl(
        max_modules=max_modules
    )
    
    filename_base = f"sc200_custom_{num_modules if num_modules > 0 else 'all'}_modules"
    crawler.save_data(f"{filename_base}.json")
    
    # Convert sang Markdown nếu được yêu cầu
    if convert_md == 'y':
        print("\n📝 Converting to Markdown...")
        crawler.convert_to_markdown(f"{filename_base}.md")
        print(f"   - Markdown: output/{filename_base}.md")
    
    print(f"\n✅ Hoàn thành! Kiểm tra output/{filename_base}.json")


async def run_url_custom():
    """Crawl từ URL tùy chỉnh"""
    print_banner()
    print("🌐 MODE: CUSTOM URL\n")
    
    default_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    print(f"URL mặc định: {default_url}")
    custom_url = input("Nhập URL course (Enter để dùng mặc định): ").strip()
    
    if not custom_url:
        custom_url = default_url
    
    try:
        num_modules = int(input("Nhập số modules muốn crawl (0 = tất cả): "))
        if num_modules < 0:
            num_modules = 0
    except ValueError:
        print("❌ Số không hợp lệ, crawl tất cả modules")
        num_modules = 0
    
    max_modules = None if num_modules == 0 else num_modules
    
    crawler = MicrosoftLearnCrawler(custom_url)
    
    await crawler.crawl(max_modules=max_modules)
    
    # Tạo tên file từ URL
    import re
    course_name = re.search(r'/courses/([^/]+)', custom_url)
    course_name = course_name.group(1) if course_name else 'custom_course'
    
    filename_base = f"{course_name}_{num_modules if num_modules > 0 else 'all'}_modules"
    crawler.save_data(f"{filename_base}.json")
    
    # # Convert sang Markdown
    # print("\n📝 Converting to Markdown...")
    # crawler.convert_to_markdown(f"{filename_base}.md")
    
    # print(f"\n✅ Hoàn thành!")
    # print(f"   - JSON: output/{filename_base}.json")
    # print(f"   - Markdown: output/{filename_base}.md")


def main():
    print_banner()
    print("Chọn chế độ crawl:")
    print("  1️⃣  Quick Test (3 modules) - Nhanh nhất, để test")
    print("  2️⃣  Single Module (1 module) - Test rất nhanh")
    print("  3️⃣  Full Crawl (tất cả modules) - Đầy đủ nhất")
    print("  4️⃣  Custom (tùy chỉnh số modules)")
    print("  5️⃣  Custom URL (crawl course khác)")
    print("  0️⃣  Thoát\n")
    
    choice = input("Lựa chọn của bạn: ").strip()
    
    if choice == "1":
        asyncio.run(run_quick_test())
    elif choice == "2":
        asyncio.run(run_single_module())
    elif choice == "3":
        confirm = input("⚠️  Full crawl có thể mất 30-60 phút. Tiếp tục? (y/n): ")
        if confirm.lower() == 'y':
            asyncio.run(run_full_crawl())
        else:
            print("❌ Đã hủy")
    elif choice == "4":
        asyncio.run(run_custom())
    elif choice == "5":
        asyncio.run(run_url_custom())
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
