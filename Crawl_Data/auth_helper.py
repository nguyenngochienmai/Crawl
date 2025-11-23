"""
Microsoft Account Authentication Helper
Script hỗ trợ đăng nhập Microsoft account nếu cần
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os


async def login_microsoft(email: str = None, password: str = None):
    """
    Đăng nhập Microsoft account và lưu session
    """
    
    if not email or not password:
        print("⚠️  Chưa cấu hình email/password")
        print("Bạn cần tạo file .env với:")
        print("MS_EMAIL=your_email@example.com")
        print("MS_PASSWORD=your_password")
        return False
        
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        print("🔐 Đang đăng nhập Microsoft...")
        
        # Truy cập trang login
        await page.goto("https://login.microsoftonline.com")
        await asyncio.sleep(2)
        
        # Nhập email
        email_input = await page.query_selector('input[type="email"]')
        if email_input:
            await email_input.fill(email)
            await page.click('input[type="submit"]')
            await asyncio.sleep(2)
            
        # Nhập password
        password_input = await page.query_selector('input[type="password"]')
        if password_input:
            await password_input.fill(password)
            await page.click('input[type="submit"]')
            await asyncio.sleep(30)
            
        # Lưu cookies/storage state
        storage_state = await context.storage_state()
        
        os.makedirs('.auth', exist_ok=True)
        with open('.auth/microsoft_session.json', 'w') as f:
            json.dump(storage_state, f)
            
        print("✅ Đăng nhập thành công! Session đã được lưu.")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi đăng nhập: {e}")
        return False
        
    finally:
        await browser.close()
        await playwright.stop()


async def load_session():
    """Load session đã lưu"""
    session_file = '.auth/microsoft_session.json'
    
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    # Để test login riêng
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv('MS_EMAIL')
    password = os.getenv('MS_PASSWORD')
    
    asyncio.run(login_microsoft(email, password))
