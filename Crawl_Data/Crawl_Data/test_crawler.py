"""
Microsoft Learn Course Crawler with Markdown Output
Crawl course content và xuất ra định dạng Markdown
"""

import asyncio
import itertools
import json
import re
from playwright.async_api import async_playwright, Page
from typing import List, Dict, Any
from datetime import datetime
import os


class MicrosoftLearnCrawler:
    def __init__(self, course_url: str):
        self.course_url = course_url
        self.base_url = "https://learn.microsoft.com"
        self.data = {
            "course_url": course_url,
            "course_title": "",
            "course_description": "",
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
    
    async def get_course_info(self):
        """Lấy thông tin course"""
        print(f"📚 Đang lấy thông tin course...")
        await self.page.goto(self.course_url, wait_until='domcontentloaded')
        await self.wait_for_load()
        await asyncio.sleep(2)
        
        try:
            # Lấy course title
            title_elem = await self.page.query_selector('h1')
            if title_elem:
                self.data['course_title'] = (await title_elem.text_content()).strip()
            
            # Lấy course description
            desc_elem = await self.page.query_selector('meta[name="description"]')
            if desc_elem:
                self.data['course_description'] = await desc_elem.get_attribute('content')
                
            print(f"  ✅ Course: {self.data['course_title']}")
        except Exception as e:
            print(f"  ⚠️ Không lấy được thông tin course: {e}")
            
    async def get_learning_paths(self) -> List[Dict[str, Any]]:
        """Lấy danh sách learning paths từ course"""
        print(f"🔍 Đang tìm learning paths...")
        
        learning_paths = []
        
        try:
            # Tìm tất cả learning path sections
            path_sections = await self.page.query_selector_all('[data-bi-name="learning-path-card"], .card, [class*="learning-path"]')
            
            if not path_sections:
                # Nếu không tìm thấy sections, tìm trực tiếp module links
                print("  📝 Không tìm thấy learning paths, tìm trực tiếp modules...")
                modules = await self.get_modules_from_page(self.course_url)
                if modules:
                    learning_paths.append({
                        'title': 'Main Content',
                        'description': '',
                        'modules': modules
                    })
                return learning_paths
            
            # Lấy thông tin từng learning path
            for section in path_sections:
                try:
                    # Lấy title
                    title_elem = await section.query_selector('h2, h3, .title')
                    if not title_elem:
                        continue
                        
                    title = (await title_elem.text_content()).strip()
                    
                    # Lấy description
                    desc_elem = await section.query_selector('p, .description')
                    description = (await desc_elem.text_content()).strip() if desc_elem else ''
                    
                    # Lấy path URL
                    path_link = await section.query_selector('a[href*="/training/paths/"]')
                    if path_link:
                        path_url = await path_link.get_attribute('href')
                        if not path_url.startswith('http'):
                            path_url = f"{self.base_url}{path_url}"
                        
                        # Lấy modules từ path
                        modules = await self.get_modules_from_path(path_url, title)
                    else:
                        # Lấy modules từ section hiện tại
                        modules = await self.get_modules_from_section(section)
                    
                    if modules:
                        learning_paths.append({
                            'title': title,
                            'description': description,
                            'modules': modules
                        })
                        print(f"  ✅ Found learning path: {title} ({len(modules)} modules)")
                        
                except Exception as e:
                    print(f"  ⚠️ Lỗi xử lý section: {e}")
                    continue
                    
        except Exception as e:
            print(f"  ⚠️ Lỗi lấy learning paths: {e}")
        
        return learning_paths
    
    async def get_modules_from_section(self, section) -> List[Dict[str, Any]]:
        """Lấy modules từ một section"""
        modules = []
        module_links = await section.query_selector_all('a[href*="/training/modules/"]')
        
        seen_urls = set()
        for link in module_links:
            href = await link.get_attribute('href')
            if href and href not in seen_urls:
                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                seen_urls.add(href)
                
                title = (await link.text_content()).strip()
                if title:
                    modules.append({
                        'title': title,
                        'url': full_url,
                        'units': []
                    })
        
        return modules
    
    async def get_modules_from_page(self, page_url: str) -> List[Dict[str, Any]]:
        """Lấy modules từ page URL"""
        modules = []
        module_links = await self.page.query_selector_all('a[href*="/training/modules/"]')
        
        seen_urls = set()
        for link in module_links:
            href = await link.get_attribute('href')
            if href and href not in seen_urls:
                # Chỉ lấy base module URL (không có unit)
                base_href = href.split('?')[0]
                if base_href not in seen_urls:
                    full_url = base_href if base_href.startswith('http') else f"{self.base_url}{base_href}"
                    seen_urls.add(base_href)
                    
                    title = (await link.text_content()).strip()
                    if title and '/training/modules/' in href:
                        modules.append({
                            'title': title,
                            'url': full_url,
                            'units': []
                        })
        
        return modules
            
    async def get_modules_from_path(self, path_url: str, path_title: str) -> List[Dict[str, Any]]:
        """Lấy modules từ learning path"""
        print(f"  📖 Đang crawl learning path: {path_title}")
        await self.page.goto(path_url, wait_until='domcontentloaded')
        await self.wait_for_load()
        await asyncio.sleep(2)
        
        return await self.get_modules_from_page(path_url)
    
    async def crawl_module(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl một module và tất cả units của nó"""
        print(f"\n📦 Đang crawl module: {module['title']}")
        
        try:
            await self.page.goto(module['url'], wait_until='domcontentloaded')
            await self.wait_for_load()
            await asyncio.sleep(2)
            
            # Lấy module description
            desc_elem = await self.page.query_selector('meta[name="description"]')
            if desc_elem:
                module['description'] = await desc_elem.get_attribute('content')
            
            # Lấy danh sách units
            module['units'] = await self.get_module_units()
            
            # Crawl từng unit
            for idx, unit in enumerate(module['units'], 1):
                print(f"  📄 Unit {idx}/{len(module['units'])}: {unit['title']}")
                await self.crawl_unit(unit)
                await asyncio.sleep(1)
            
            print(f"  ✅ Hoàn thành module")
            
        except Exception as e:
            print(f"  ❌ Lỗi crawl module: {e}")
        
        return module
    
    async def get_module_units(self) -> List[Dict[str, Any]]:
        """Lấy danh sách units trong module"""
        units = []
        
        try:
            # Tìm navigation/TOC
            nav_items = await self.page.query_selector_all('[role="navigation"] a, .units-list a, [class*="unit"] a')
            
            seen_urls = set()
            for item in nav_items:
                href = await item.get_attribute('href')
                if href and '/training/modules/' in href and href not in seen_urls:
                    seen_urls.add(href)
                    
                    title = (await item.text_content()).strip()
                    full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    
                    # Xác định loại unit
                    unit_type = self.detect_unit_type(title, href)
                    
                    units.append({
                        'title': title,
                        'url': full_url,
                        'type': unit_type,
                        'content': {}
                    })
        
        except Exception as e:
            print(f"    ⚠️ Lỗi lấy units: {e}")
        
        return units
    
    def detect_unit_type(self, title: str, url: str) -> str:
        """Xác định loại unit"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if 'introduction' in title_lower or '/1-' in url_lower:
            return 'introduction'
        elif 'knowledge check' in title_lower or 'quiz' in title_lower or 'check-knowledge' in url_lower:
            return 'quiz'
        elif 'exercise' in title_lower or 'lab' in title_lower:
            return 'exercise'
        elif 'summary' in title_lower:
            return 'summary'
        else:
            return 'content'
    
    async def crawl_unit(self, unit: Dict[str, Any]):
        """Crawl nội dung của một unit"""
        try:
            await self.page.goto(unit['url'], wait_until='domcontentloaded')
            await self.wait_for_load()
            await asyncio.sleep(2)
            
            # Lấy nội dung chính
            unit['content'] = await self.extract_unit_content()
            
            # Nếu là quiz, lấy câu hỏi
            if unit['type'] == 'quiz':
                unit['content']['questions'] = await self.extract_quiz_questions_enhanced()
            
            # Nếu là exercise, lấy steps
            if unit['type'] == 'exercise':
                unit['content']['exercise'] = await self.extract_exercise_enhanced()
            
        except Exception as e:
            print(f"    ⚠️ Lỗi crawl unit: {e}")
    
    async def extract_unit_content(self) -> Dict[str, Any]:
        """Trích xuất nội dung unit"""
        content = {
            'headings': [],
            'paragraphs': [],
            'lists': [],
            'code_blocks': [],
            'images': [],
            'videos': [],
            'tables': []
        }
        
        try:
            main_content = await self.page.query_selector('#main, [role="main"], .content')
            if not main_content:
                return content
            
            # Lấy headings
            headings = await main_content.query_selector_all('h1, h2, h3, h4, h5, h6')
            for h in headings:
                tag = await h.evaluate('el => el.tagName.toLowerCase()')
                text = (await h.text_content()).strip()
                if text:
                    content['headings'].append({
                        'level': tag,
                        'text': text
                    })
            
            # Lấy paragraphs
            paragraphs = await main_content.query_selector_all('p')
            for p in paragraphs:
                text = (await p.text_content()).strip()
                if text and len(text) > 20:
                    content['paragraphs'].append(text)
            
            # Lấy lists
            lists = await main_content.query_selector_all('ul, ol')
            for lst in lists:
                items = await lst.query_selector_all('li')
                list_items = []
                for item in items:
                    text = (await item.text_content()).strip()
                    if text:
                        list_items.append(text)
                if list_items:
                    list_type = await lst.evaluate('el => el.tagName.toLowerCase()')
                    content['lists'].append({
                        'type': list_type,
                        'items': list_items
                    })
            
            # Lấy code blocks
            content['code_blocks'] = await self.extract_code_blocks()
            
            # Lấy images
            content['images'] = await self.extract_images()
            
            # Lấy videos
            content['videos'] = await self.extract_videos_enhanced()
            
            # Lấy tables
            tables = await main_content.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                table_data = []
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    row_data = []
                    for cell in cells:
                        text = (await cell.text_content()).strip()
                        row_data.append(text)
                    if row_data:
                        table_data.append(row_data)
                if table_data:
                    content['tables'].append(table_data)
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract content: {e}")
        
        return content
    
    async def extract_code_blocks(self) -> List[Dict[str, str]]:
        """Trích xuất code blocks"""
        code_blocks = []
        
        try:
            code_elements = await self.page.query_selector_all('pre code, .code-block, pre')
            
            for code_elem in code_elements:
                lang = ''
                class_attr = await code_elem.get_attribute('class')
                if class_attr:
                    for cls in class_attr.split():
                        if 'language-' in cls:
                            lang = cls.replace('language-', '')
                            break
                
                code_text = (await code_elem.text_content()).strip()
                if code_text and len(code_text) > 10:
                    code_blocks.append({
                        'language': lang or 'text',
                        'code': code_text
                    })
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract code blocks: {e}")
        
        return code_blocks
    
    async def extract_images(self) -> List[Dict[str, str]]:
        """Trích xuất images"""
        images = []
        
        try:
            img_elements = await self.page.query_selector_all('img')
            
            for img in img_elements:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or ''
                
                if src and not src.startswith('data:'):
                    full_src = src if src.startswith('http') else f"{self.base_url}{src}"
                    images.append({
                        'url': full_src,
                        'alt': alt
                    })
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract images: {e}")
        
        return images
    
    async def extract_videos_enhanced(self) -> List[Dict[str, Any]]:
        """Trích xuất video links"""
        videos = []
        
        try:
            # YouTube videos
            youtube_iframes = await self.page.query_selector_all('iframe[src*="youtube.com"], iframe[src*="youtu.be"]')
            for iframe in youtube_iframes:
                src = await iframe.get_attribute('src')
                if src:
                    video_id = None
                    if 'embed/' in src:
                        video_id = src.split('embed/')[-1].split('?')[0]
                    
                    videos.append({
                        'type': 'youtube',
                        'url': f"https://www.youtube.com/watch?v={video_id}" if video_id else src,
                        'embed_url': src
                    })
            
            # Microsoft Stream
            stream_iframes = await self.page.query_selector_all('iframe[src*="microsoft.com/videoplayer"], iframe[src*="microsoftstream.com"]')
            for iframe in stream_iframes:
                src = await iframe.get_attribute('src')
                if src:
                    videos.append({
                        'type': 'microsoft_stream',
                        'url': src
                    })
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract videos: {e}")
        
        return videos
    
    async def extract_quiz_questions_enhanced(self) -> List[Dict[str, Any]]:
        """Trích xuất câu hỏi quiz với đáp án"""
        questions_options = []
        correct_answers_found = []

        try:
            await asyncio.sleep(2)

            # Click Start quiz nếu có
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
            
            if not question_containers:
                return []
            
            print(f"      🎯 Found {len(question_containers)} questions")

            for q_elem in question_containers:
                q_title_elem = await q_elem.query_selector(".quiz-question-title p")
                if not q_title_elem:
                    continue
                    
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

            # Thử cho đến khi score = 100%
            for combo in all_combinations:
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
                if submit_btn:
                    await submit_btn.click()
                    await asyncio.sleep(1)

                # Đọc score
                score_elem = await self.page.query_selector("#module-assessment-result-score")
                score_text = await score_elem.text_content() if score_elem else "0%"
                score = int(score_text.strip().replace("%", "") or 0)

                if score < 100:
                    await self.page.reload()
                    await asyncio.sleep(2)
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
                    print(f"      ✅ Achieved 100% score!")
                    break

            # Tạo kết quả
            results = []
            for q_idx, q_data in enumerate(questions_options):
                results.append({
                    "question": q_data["question"],
                    "options": q_data["options"],
                    "correct_answer": correct_answers_found[q_idx] if correct_answers_found[q_idx] else "Not found"
                })

            return results

        except Exception as e:
            print(f"      ⚠️ Lỗi extract quiz: {e}")
            return []
    
    async def extract_exercise_enhanced(self) -> Dict[str, Any]:
        """Trích xuất bài tập chi tiết"""
        exercise = {
            'steps': [],
            'requirements': []
        }
        
        try:
            # Lấy các bước thực hiện
            step_elements = await self.page.query_selector_all('ol li, [class*="step"]')
            
            for idx, step in enumerate(step_elements, 1):
                text = (await step.text_content()).strip()
                if text and len(text) > 15:
                    code_blocks = []
                    code_elems = await step.query_selector_all('code, pre')
                    for code in code_elems:
                        code_text = (await code.text_content()).strip()
                        if code_text:
                            code_blocks.append(code_text)
                    
                    exercise['steps'].append({
                        'step': idx,
                        'instruction': text,
                        'code': code_blocks
                    })
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract exercise: {e}")
        
        return exercise
    
    def generate_markdown(self) -> str:
        """Tạo file Markdown từ dữ liệu đã crawl"""
        md = []
        
        # Header
        md.append(f"# {self.data['course_title']}\n")
        md.append(f"> Crawled from: {self.data['course_url']}")
        md.append(f"> Date: {self.data['crawled_at']}\n")
        
        if self.data.get('course_description'):
            md.append(f"## Description\n")
            md.append(f"{self.data['course_description']}\n")
        
        md.append("---\n")
        
        # Learning Paths
        for path_idx, path in enumerate(self.data['learning_paths'], 1):
            md.append(f"## {path['title']}\n")
            
            if path.get('description'):
                md.append(f"{path['description']}\n")
            
            # Modules
            for mod_idx, module in enumerate(path['modules'], 1):
                md.append(f"### Module {mod_idx}: {module['title']}\n")
                
                if module.get('description'):
                    md.append(f"**Description:** {module['description']}\n")
                
                # Units
                for unit_idx, unit in enumerate(module.get('units', []), 1):
                    md.append(f"#### Unit {unit_idx}: {unit['title']}\n")
                    
                    content = unit.get('content', {})
                    
                    # Headings & Paragraphs
                    for heading in content.get('headings', []):
                        level = int(heading['level'][1])
                        md.append(f"{'#' * (level + 3)} {heading['text']}\n")
                    
                    for para in content.get('paragraphs', []):
                        md.append(f"{para}\n")
                    
                    # Lists
                    for lst in content.get('lists', []):
                        list_type = lst.get('type', 'ul')
                        for i, item in enumerate(lst.get('items', []), 1):
                            if list_type == 'ol':
                                md.append(f"{i}. {item}")
                            else:
                                md.append(f"- {item}")
                        md.append("")
                    
                    # Code blocks
                    for code in content.get('code_blocks', []):
                        md.append(f"```{code['language']}")
                        md.append(code['code'])
                        md.append("```\n")
                    
                    # Images
                    for img in content.get('images', []):
                        md.append(f"![{img['alt']}]({img['url']})\n")
                    
                    # Videos
                    for video in content.get('videos', []):
                        md.append(f"**Video ({video['type']}):** {video['url']}\n")
                    
                    # Tables
                    for table in content.get('tables', []):
                        if len(table) > 0:
                            # Header
                            md.append("| " + " | ".join(table[0]) + " |")
                            md.append("| " + " | ".join(["---"] * len(table[0])) + " |")
                            # Rows
                            for row in table[1:]:
                                md.append("| " + " | ".join(row) + " |")
                            md.append("")
                    
                    # Quiz
                    if unit['type'] == 'quiz':
                        questions = content.get('questions', [])
                        if questions:
                            md.append("##### Knowledge Check\n")
                            for q_idx, q in enumerate(questions, 1):
                                md.append(f"**Question {q_idx}:** {q['question']}\n")
                                for opt in q['options']:
                                    md.append(f"- {opt}")
                                md.append(f"\n**Correct Answer:** {q['correct_answer']}\n")
                    
                    # Exercise
                    if unit['type'] == 'exercise':
                        exercise = content.get('exercise', {})
                        if exercise.get('steps'):
                            md.append("##### Exercise Steps\n")
                            for step in exercise['steps']:
                                md.append(f"{step['step']}. {step['instruction']}\n")
                                for code in step.get('code', []):
                                    md.append(f"```")
                                    md.append(code)
                                    md.append("```\n")
                    
                    md.append("---\n")
        
        return "\n".join(md)
    
    async def crawl(self, max_paths: int = None, max_modules_per_path: int = None):
        """Hàm main để crawl toàn bộ course"""
        await self.init_browser(headless=False)
        
        try:
            print("=" * 60)
            print("🚀 BẮT ĐẦU CRAWL MICROSOFT LEARN COURSE")
            print("=" * 60)
            
            # Lấy thông tin course
            await self.get_course_info()
            
            # Lấy learning paths
            learning_paths = await self.get_learning_paths()
            
            if not learning_paths:
                print("❌ Không tìm thấy learning paths!")
                return
            
            print(f"\n✅ Tìm thấy {len(learning_paths)} learning paths")
            
            # Giới hạn số lượng nếu cần
            if max_paths:
                learning_paths = learning_paths[:max_paths]
            
            # Crawl từng learning path
            for path_idx, path in enumerate(learning_paths, 1):
                print(f"\n{'=' * 60}")
                print(f"📚 LEARNING PATH {path_idx}/{len(learning_paths)}: {path['title']}")
                print(f"{'=' * 60}")
                
                modules = path['modules']
                if max_modules_per_path:
                    modules = modules[:max_modules_per_path]
                
                # Crawl từng module
                for mod_idx, module in enumerate(modules, 1):
                    print(f"\n📦 Module {mod_idx}/{len(modules)}")
                    await self.crawl_module(module)
                    await asyncio.sleep(2)
                
                self.data['learning_paths'].append(path)
            
            print("\n" + "=" * 60)
            print("🎉 HOÀN THÀNH CRAWL!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Lỗi nghiêm trọng: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()
    
    def save_data(self, json_filename: str = "course_data.json", md_filename: str = "course_content.md"):
        """Lưu data ra file JSON và Markdown"""
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Lưu JSON
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Đã lưu JSON: {json_path}")
        
        # Tạo và lưu Markdown
        markdown_content = self.generate_markdown()
        md_path = os.path.join(output_dir, md_filename)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"📝 Đã lưu Markdown: {md_path}")
        
        # Tạo summary
        total_modules = sum(len(path['modules']) for path in self.data['learning_paths'])
        total_units = sum(
            len(module.get('units', []))
            for path in self.data['learning_paths']
            for module in path['modules']
        )
        
        summary = {
            'course_title': self.data['course_title'],
            'total_learning_paths': len(self.data['learning_paths']),
            'total_modules': total_modules,
            'total_units': total_units,
            'crawled_at': self.data['crawled_at']
        }
        
        summary_path = os.path.join(output_dir, 'summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Summary:")
        print(f"  - Learning Paths: {summary['total_learning_paths']}")
        print(f"  - Modules: {summary['total_modules']}")
        print(f"  - Units: {summary['total_units']}")


async def main():
    """
    Main function để chạy crawler
    """
    
    # URL course cần crawl
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    
    # Hoặc có thể crawl từ learning path
    # course_url = "https://learn.microsoft.com/en-us/training/paths/sc-200-mitigate-threats-using-microsoft-365-defender/"
    
    # Hoặc crawl trực tiếp một module
    # course_url = "https://learn.microsoft.com/en-us/training/modules/introduction-microsoft-365-threat-protection/"
    
    crawler = MicrosoftLearnCrawler(course_url)
    
    # Crawl course
    # Bỏ max_paths và max_modules_per_path để crawl toàn bộ
    await crawler.crawl(
        max_paths=1,              # Chỉ crawl 1 learning path đầu tiên (để test)
        max_modules_per_path=2    # Chỉ crawl 2 modules đầu tiên mỗi path (để test)
    )
    
    # Lưu kết quả
    crawler.save_data(
        json_filename="sc200_course_data.json",
        md_filename="sc200_course_content.md"
    )


if __name__ == "__main__":
    asyncio.run(main())