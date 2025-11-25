"""
Microsoft Learn Course Crawler - Markdown Export
Crawl và export ra file .md giống website gốc
"""

import asyncio
import itertools
import json
import re
from playwright.async_api import async_playwright, Page
from typing import List, Dict, Any
from datetime import datetime
import os
import markdownify


class MicrosoftLearnCrawler:
    def __init__(self, course_url: str):
        self.course_url = course_url
        self.base_url = "https://learn.microsoft.com"
        self.output_dir = "output_markdown"
        self.data = {
            "course_url": course_url,
            "crawled_at": datetime.now().isoformat(),
            "learning_paths": []
        }
        
    async def init_browser(self, headless: bool = False):
        """Khởi tạo browser với Playwright"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def close_browser(self):
        """Đóng browser"""
        await self.browser.close()
        await self.playwright.stop()
        
    async def wait_for_load(self, timeout: int = 10000):
        """Đợi trang load xong"""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
        except:
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout)
    
    def sanitize_filename(self, name: str) -> str:
        """Làm sạch tên file"""
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = name.replace(' ', '_')
        return name[:100]  # Giới hạn độ dài
    
    def fix_image_path(self, url: str) -> str:
        """Sửa đường dẫn ảnh: thay ../../ thành /training/"""
        if '../../' in url:
            url = url.replace('../../', '/training/')
        
        # Nếu chưa có domain thì thêm base_url
        if not url.startswith('http'):
            if url.startswith('/'):
                url = f"{self.base_url}{url}"
            else:
                url = f"{self.base_url}/training/{url}"
        
        return url
            
    async def get_course_modules(self) -> List[Dict[str, Any]]:
        """Lấy danh sách modules từ course page"""
        print(f"🔍 Đang truy cập course: {self.course_url}")
        await self.page.goto(self.course_url, wait_until='domcontentloaded')
        await self.wait_for_load()
        await asyncio.sleep(2)
        
        learning_paths = []
        
        print("\n📄 Đang tìm learning paths...")
        try:
            path_links = await self.page.query_selector_all('a[href*="/training/paths/"]')
            print(f"   📋 Found {len(path_links)} learning path links")
            
            path_urls = []
            path_titles = []
            for link in path_links:
                href = await link.get_attribute('href')
                title = await link.text_content() or ""
                if href:
                    path_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    if path_url not in path_urls:
                        path_urls.append(path_url)
                        path_titles.append(title.strip())
            
            print(f"   ✓ Unique paths to crawl: {len(path_urls)}")
            
            for i, (path_url, path_title) in enumerate(zip(path_urls, path_titles), 1):
                print(f"\n{'='*70}")
                print(f"📚 [{i}/{len(path_urls)}] Đang crawl learning path: {path_title}")
                print(f"    URL: {path_url}")
                print(f"{'='*70}")
                
                try:
                    path_modules = await self.get_modules_from_path(path_url, path_title)
                    
                    learning_path = {
                        "title": path_title,
                        "url": path_url,
                        "module_count": len(path_modules),
                        "crawled_at": datetime.now().isoformat(),
                        "modules": path_modules
                    }
                    
                    learning_paths.append(learning_path)
                    
                    print(f"\n  ✓ Hoàn thành path {i}/{len(path_urls)}")
                    print(f"  ✓ Found {len(path_modules)} modules in this path")
                    
                    if i < len(path_urls):
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    print(f"  ⚠️ Lỗi khi crawl path {path_url}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                    
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy learning paths: {e}")
        
        self.data["learning_paths"] = learning_paths
        total_modules = sum(len(path["modules"]) for path in learning_paths)
        
        print(f"\n{'='*70}")
        print(f"📊 TỔNG KẾT:")
        print(f"  - Tổng số learning paths: {len(learning_paths)}")
        print(f"  - Tổng số modules: {total_modules}")
        print(f"{'='*70}\n")
        
        return learning_paths
    
    async def get_module_group_title(self):
        """Lấy tiêu đề nhóm module"""
        try:
            elem = await self.page.query_selector("h1[data-bi-name='page-title'], h1")
            if elem:
                return (await elem.text_content()).strip()
        except:
            return ""
        return ""
     
    async def get_modules_from_path(self, path_url: str, path_title: str) -> List[Dict[str, Any]]:
        """Lấy modules từ learning path"""
        await self.page.goto(path_url, wait_until='domcontentloaded')
        await self.wait_for_load()
        await asyncio.sleep(2)
        
        modules = []
        module_links = await self.page.query_selector_all('a[href*="/training/modules/"]')
        
        print(f"    🔍 Found {len(module_links)} module links in this path")
        
        seen_urls = set()
        for link in module_links:
            href = await link.get_attribute('href')
            if href and href not in seen_urls:
                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                seen_urls.add(href)
                
                title = await link.text_content() or ""
                title = title.strip()
                
                if title.lower() in ['start', 'begin', 'launch', 'continue']:
                    continue
                
                if title:
                    modules.append({
                        'title': title,
                        'url': full_url,
                        'type': self.detect_module_type(title),
                    })
                    print(f"      + {title}")
                    
        return modules
    
    def detect_module_type(self, title: str) -> str:
        """Xác định loại module dựa vào title"""
        title_lower = title.lower()
        if 'introduction' in title_lower:
            return 'introduction'
        elif 'exercise' in title_lower or 'lab' in title_lower:
            return 'exercise'
        elif 'knowledge check' in title_lower or 'quiz' in title_lower or 'assessment' in title_lower:
            return 'quiz'
        elif 'summary' in title_lower:
            return 'summary'
        else:
            return 'content'
        
    async def crawl_module_to_markdown(self, module: Dict[str, Any], path_title: str, module_idx: int) -> str:
        """Crawl module và convert sang markdown"""
        print(f"\n📖 Đang crawl module: {module['title']}")
        
        markdown_content = []
        
        try:
            await self.page.goto(module['url'], wait_until='domcontentloaded')
            await self.wait_for_load()
            await asyncio.sleep(2)

            # Header với metadata
            markdown_content.append(f"---")
            markdown_content.append(f"title: {module['title']}")
            markdown_content.append(f"learning_path: {path_title}")
            markdown_content.append(f"module_number: {module_idx}")
            markdown_content.append(f"url: {module['url']}")
            markdown_content.append(f"type: {module['type']}")
            
            # Lấy duration
            try:
                duration_elem = await self.page.query_selector('span[data-bi-name="duration"]')
                if duration_elem:
                    duration = await duration_elem.text_content()
                    markdown_content.append(f"duration: {duration.strip()}")
            except:
                pass
            
            markdown_content.append(f"crawled_at: {datetime.now().isoformat()}")
            markdown_content.append(f"---\n")
            
            # Title chính
            markdown_content.append(f"# {module['title']}\n")
            
            # Lấy description
            try:
                desc_elem = await self.page.query_selector('meta[name="description"]')
                if desc_elem:
                    desc = await desc_elem.get_attribute('content')
                    if desc:
                        markdown_content.append(f"> {desc}\n")
            except:
                pass
            
            # Lấy nội dung chính
            main_content = await self.page.query_selector('#module-unit-content')
            if main_content:
                # Xử lý các thành phần theo thứ tự
                content_md = await self.extract_content_as_markdown(main_content)
                markdown_content.append(content_md)
            
            # Nếu là quiz, xử lý riêng
            if module['type'] == 'quiz' or 'knowledge check' in module['title'].lower():
                quiz_md = await self.extract_quiz_questions_enhanced()
                if quiz_md:
                    markdown_content.append("\n---\n\n## Knowledge Check\n\n")
                    markdown_content.append(quiz_md)
            
            # Thêm footer
            markdown_content.append(f"\n---\n\n*Source: [{module['url']}]({module['url']})*")
            
            print(f"  ✅ Crawled module successfully")
            
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
            markdown_content.append(f"\n\n**Error crawling this module: {str(e)}**\n")
            
        return "\n".join(markdown_content)
    
    async def extract_content_as_markdown(self, container) -> str:
        """Trích xuất nội dung thành markdown"""
        markdown_lines = []
        
        try:
            # Lấy tất cả elements con theo thứ tự
            elements = await container.query_selector_all('h1, h2, h3, h4, h5, h6, p, ul, ol, pre, table, blockquote, img, video, iframe')
            
            for elem in elements:
                tag = await elem.evaluate('el => el.tagName.toLowerCase()')
                
                # Headings
                if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(tag[1])
                    text = await elem.text_content()
                    if text and text.strip():
                        markdown_lines.append(f"\n{'#' * level} {text.strip()}\n")
                
                # Paragraphs
                elif tag == 'p':
                    text = await elem.text_content()
                    if text and len(text.strip()) > 10:
                        # Xử lý inline code
                        inner_html = await elem.inner_html()
                        text = await self.convert_html_to_markdown(inner_html)
                        markdown_lines.append(f"{text}\n")
                
                # Lists
                elif tag in ['ul', 'ol']:
                    list_md = await self.extract_list_as_markdown(elem, tag)
                    markdown_lines.append(list_md)
                
                # Code blocks
                elif tag == 'pre':
                    code_elem = await elem.query_selector('code')
                    if code_elem:
                        code_text = await code_elem.text_content()
                        
                        # Lấy language
                        lang = 'text'
                        class_attr = await code_elem.get_attribute('class')
                        if class_attr:
                            for cls in class_attr.split():
                                if 'language-' in cls:
                                    lang = cls.replace('language-', '')
                                    break
                        
                        markdown_lines.append(f"\n```{lang}")
                        markdown_lines.append(code_text.strip())
                        markdown_lines.append("```\n")
                
                # Tables
                elif tag == 'table':
                    table_md = await self.extract_table_as_markdown(elem)
                    markdown_lines.append(table_md)
                
                # Blockquotes
                elif tag == 'blockquote':
                    text = await elem.text_content()
                    if text:
                        lines = text.strip().split('\n')
                        for line in lines:
                            markdown_lines.append(f"> {line.strip()}")
                        markdown_lines.append("")
                
                # Images - SỬA ĐƯỜNG DẪN ẢNH Ở ĐÂY
                elif tag == 'img':
                    src = await elem.get_attribute('src')
                    alt = await elem.get_attribute('alt') or 'image'
                    if src:
                        # Sửa đường dẫn ảnh
                        src = self.fix_image_path(src)
                        markdown_lines.append(f"\n![{alt}]({src})\n")
                
                # Videos
                elif tag == 'video':
                    sources = await elem.query_selector_all('source')
                    if sources:
                        src = await sources[0].get_attribute('src')
                        if src:
                            if not src.startswith('http'):
                                src = f"{self.base_url}{src}"
                            markdown_lines.append(f"\n🎥 **Video**: [{src}]({src})\n")
                
                # iframes (YouTube, etc)
                elif tag == 'iframe':
                    src = await elem.get_attribute('src')
                    if src:
                        if 'youtube' in src or 'youtu.be' in src:
                            markdown_lines.append(f"\n🎥 **Video**: [{src}]({src})\n")
                        else:
                            markdown_lines.append(f"\n📺 **Embedded Content**: [{src}]({src})\n")
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract content: {e}")
        
        return "\n".join(markdown_lines)
    
    async def convert_html_to_markdown(self, html: str) -> str:
        """Convert simple HTML to markdown"""
        # Strong/Bold
        html = re.sub(r'<strong>(.*?)</strong>', r'**\1**', html)
        html = re.sub(r'<b>(.*?)</b>', r'**\1**', html)
        
        # Em/Italic
        html = re.sub(r'<em>(.*?)</em>', r'*\1*', html)
        html = re.sub(r'<i>(.*?)</i>', r'*\1*', html)
        
        # Code
        html = re.sub(r'<code>(.*?)</code>', r'`\1`', html)
        
        # Links
        html = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', html)
        
        # Remove remaining tags
        html = re.sub(r'<[^>]+>', '', html)
        
        return html.strip()
    
    async def extract_list_as_markdown(self, list_elem, list_type: str) -> str:
        """Trích xuất list thành markdown"""
        lines = []
        items = await list_elem.query_selector_all('li')
        
        for i, item in enumerate(items, 1):
            text = await item.text_content()
            if text:
                prefix = f"{i}." if list_type == 'ol' else "-"
                lines.append(f"{prefix} {text.strip()}")
        
        lines.append("")  # Empty line after list
        return "\n".join(lines)
    
    async def extract_table_as_markdown(self, table_elem) -> str:
        """Trích xuất table thành markdown"""
        lines = []
        rows = await table_elem.query_selector_all('tr')
        
        for row_idx, row in enumerate(rows):
            cells = await row.query_selector_all('td, th')
            row_data = []
            for cell in cells:
                text = await cell.text_content()
                row_data.append(text.strip() if text else '')
            
            if row_data:
                lines.append("| " + " | ".join(row_data) + " |")
                
                # Add separator after header row
                if row_idx == 0:
                    lines.append("| " + " | ".join(["---"] * len(row_data)) + " |")
        
        lines.append("")  # Empty line after table
        return "\n".join(lines)
    
    async def extract_quiz_questions_enhanced(self) -> List[Dict[str, Any]]:
        """
        Trích xuất câu hỏi quiz với đáp án, thử submit cho đến khi score = 100%
        """
        questions_options = []
        correct_answers_found = []

        try:
            # Đợi quiz load
            await asyncio.sleep(2)

            # Click Start/Begin quiz nếu có
            start_buttons = await self.page.query_selector_all(
                'button:has-text("Start"), button:has-text("Begin"), button:has-text("Check your knowledge")'
            )
            if start_buttons:
                try:
                    await start_buttons[0].click()
                    await asyncio.sleep(3)
                except:
                    pass

            # Lấy tất cả câu hỏi
            question_containers = await self.page.query_selector_all("div.quiz-question")
            print(f"🔍 Found {len(question_containers)} questions")

            # Lấy câu hỏi + options
            for q_elem in question_containers:
                q_title_elem = await q_elem.query_selector(".quiz-question-title p")
                question_text = (await q_title_elem.text_content()).strip()

                option_labels = await q_elem.query_selector_all("label.quiz-choice")
                options = []
                inputs = []
                for lbl in option_labels:
                    text = (await lbl.text_content()).strip()
                    inp = await lbl.query_selector("input")
                    options.append(text)
                    inputs.append(inp)

                questions_options.append({
                    "element": q_elem,
                    "question": question_text,
                    "options": options,
                    "inputs": inputs
                })
                correct_answers_found.append(None)

            # Tạo tất cả tổ hợp đáp án
            choices_indices = [list(range(len(q["options"]))) for q in questions_options]
            all_combinations = list(itertools.product(*choices_indices))

            # Lặp thử cho đến khi score = 100%
            for combo in all_combinations:
                # Click đáp án cho các câu chưa biết
                for q_idx, q_data in enumerate(questions_options):
                    if correct_answers_found[q_idx] is None:
                        inp_idx = combo[q_idx]
                    else:
                        inp_idx = q_data["options"].index(correct_answers_found[q_idx])
                    inp = q_data["inputs"][inp_idx]
                    await inp.click(force=True)

                # Click Submit
                submit_btn = await self.page.query_selector(
                    "button[data-bi-name='module-unit-module-assessment-submit']"
                )
                await submit_btn.click()
                await asyncio.sleep(1)

                # Đọc score tổng
                score_elem = await self.page.query_selector("#module-assessment-result-score")
                score_text = await score_elem.text_content() if score_elem else "0%"
                score = int(score_text.strip().replace("%", "") or 0)
                print(f"➡ Tried combo {combo}, score: {score}%")

                if score < 100:
                    # Reload page nếu chưa 100%
                    await self.page.reload()
                    await asyncio.sleep(2)
                    # Lấy lại element + input
                    question_containers = await self.page.query_selector_all("div.quiz-question")
                    for i, q_elem in enumerate(question_containers):
                        questions_options[i]["element"] = q_elem
                        option_labels = await q_elem.query_selector_all("label.quiz-choice")
                        inputs = [await lbl.query_selector("input") for lbl in option_labels]
                        questions_options[i]["inputs"] = inputs
                else:
                    # Score = 100%, lưu đáp án đúng
                    for q_idx, q_data in enumerate(questions_options):
                        input_checked = await q_data["element"].query_selector("input:checked")
                        if input_checked:
                            checked_value = await input_checked.get_attribute("value")
                            for i, inp in enumerate(q_data["inputs"]):
                                val = await inp.get_attribute("value")
                                if val == checked_value:
                                    correct_answers_found[q_idx] = q_data["options"][i]
                                    break
                    print("      📄 Crawling quiz results page after achieving 100%...")
                    break
            
            # Sau khi đạt 100%, trang đã hiển thị kết quả
            # Crawl nội dung trang này thành markdown
                    # markdown_lines = []
                    # main_content = await self.page.query_selector('#module-unit-content, main, .quiz-results')
                    
                    # if main_content:
                    #     content_md = await self.extract_content_as_markdown(main_content)
                    #     markdown_lines.append(content_md)
                    # else:
                    #     print("      ⚠️ Could not find quiz results content")
                    # print("✅ Achieved 100% score!")
                    # break

            # Tạo kết quả trả về
            results = []
            for q_idx, q_data in enumerate(questions_options):
                results.append({
                    "question_number": q_idx + 1,
                    "question": q_data["question"],
                    "options": q_data["options"],
                    "correct_answers": [correct_answers_found[q_idx]] if correct_answers_found[q_idx] else ["Not found"],
                    "type": "multiple_choice" if len(q_data["options"]) > 0 else "text",
                    "explanation": ""
                })

            return markdownify.markdownify(json.dumps(results, ensure_ascii=False, indent=2))
            # return "\n".join(markdown_lines)
        except Exception as e:
            print(f"⚠️ Error in extract_quiz_questions_enhanced: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # async def extract_quiz_as_markdown(self) -> str:
        """
        Trích xuất quiz thành markdown - sau khi đạt 100 điểm, crawl trang kết quả
        """
        markdown_lines = []
        
        try:
            # Gọi hàm tìm đáp án và đạt 100%
            quiz_results = await self.extract_quiz_questions_enhanced()
            
            if not quiz_results:
                return ""
            
            print("      📄 Crawling quiz results page after achieving 100%...")
            
            # Sau khi đạt 100%, trang đã hiển thị kết quả
            # Crawl nội dung trang này thành markdown
            main_content = await self.page.query_selector('#module-unit-content, main, .quiz-results')
            
            if main_content:
                content_md = await self.extract_content_as_markdown(main_content)
                markdown_lines.append(content_md)
            else:
                print("      ⚠️ Could not find quiz results content")
            
        except Exception as e:
            print(f"⚠️ Error in extract_quiz_as_markdown: {e}")
        
        return "\n".join(markdown_lines)
        
    async def crawl(self, max_modules: int = None):
        """Hàm main để crawl toàn bộ course"""
        await self.init_browser(headless=False)
        
        try:
            print("=" * 60)
            print("🚀 BẮT ĐẦU CRAWL MICROSOFT LEARN COURSE")
            print("=" * 60)
            
            learning_paths = await self.get_course_modules()
            
            if not learning_paths:
                print("❌ Không tìm thấy learning paths nào!")
                return
            
            total_modules = sum(len(path["modules"]) for path in learning_paths)
            print(f"\n✅ Tìm thấy {len(learning_paths)} learning paths với tổng {total_modules} modules")
            
            # Tạo thư mục output
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Tạo file index
            index_content = ["# Microsoft Learn Course\n"]
            index_content.append(f"**Course URL**: {self.course_url}\n")
            index_content.append(f"**Crawled at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            index_content.append(f"**Total Learning Paths**: {len(learning_paths)}\n")
            index_content.append(f"**Total Modules**: {total_modules}\n")
            index_content.append("\n---\n\n")
            
            module_counter = 0
            
            for path_idx, learning_path in enumerate(learning_paths, 1):
                print(f"\n{'=' * 70}")
                print(f"📚 LEARNING PATH {path_idx}/{len(learning_paths)}: {learning_path['title']}")
                print(f"{'=' * 70}")
                
                # Tạo thư mục cho learning path
                path_dir = os.path.join(
                    self.output_dir, 
                    f"{path_idx:02d}_{self.sanitize_filename(learning_path['title'])}"
                )
                os.makedirs(path_dir, exist_ok=True)
                
                # Thêm vào index
                index_content.append(f"## {path_idx}. {learning_path['title']}\n")
                index_content.append(f"**URL**: {learning_path['url']}\n")
                index_content.append(f"**Modules**: {len(learning_path['modules'])}\n\n")
                
                modules = learning_path['modules']
                
                if max_modules and module_counter >= max_modules:
                    print(f"⚠️ Đã đạt giới hạn {max_modules} modules")
                    break
                
                for idx, module in enumerate(modules, 1):
                    module_counter += 1
                    
                    if max_modules and module_counter > max_modules:
                        break
                    
                    print(f"\n{'=' * 60}")
                    print(f"📖 MODULE {idx}/{len(modules)} (Tổng: {module_counter}/{total_modules})")
                    print(f"{'=' * 60}")
                    
                    # Crawl module thành markdown
                    markdown_content = await self.crawl_module_to_markdown(
                        module, 
                        learning_path['title'],
                        idx
                    )
                    
                    # Lưu file markdown
                    module_filename = f"{idx:02d}_{self.sanitize_filename(module['title'])}.md"
                    module_filepath = os.path.join(path_dir, module_filename)
                    
                    with open(module_filepath, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    print(f"  💾 Saved: {module_filepath}")
                    
                    # Thêm vào index
                    index_content.append(f"  {idx}. [{module['title']}]({path_dir}/{module_filename})\n")
                    
                    await asyncio.sleep(2)
                
                index_content.append("\n")
                print(f"\n✅ Hoàn thành learning path: {learning_path['title']}")
                
            # Lưu file index
            index_path = os.path.join(self.output_dir, "README.md")
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write("".join(index_content))
            
            print("\n" + "=" * 60)
            print("🎉 HOÀN THÀNH CRAWL!")
            print("=" * 60)
            print(f"\n📊 Thống kê:")
            print(f"  - Số learning paths: {len(learning_paths)}")
            print(f"  - Tổng modules đã crawl: {module_counter}")
            print(f"  - Output directory: {self.output_dir}")
            print(f"  - Index file: {index_path}")
            
        except Exception as e:
            print(f"\n❌ Lỗi nghiêm trọng: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()


async def main():
    # URL course cần crawl
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    
    crawler = MicrosoftLearnCrawler(course_url)
    
    # Crawl course
    await crawler.crawl(
        max_modules=7  # Bỏ hoặc set None để crawl tất cả modules
    )


if __name__ == "__main__":
    asyncio.run(main())