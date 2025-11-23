"""
Microsoft Learn Course Crawler
Crawl toàn bộ course content từ Microsoft Learn
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
            
    async def get_course_modules(self) -> List[Dict[str, Any]]:
        """Lấy danh sách modules từ course page - CRAWL TẤT CẢ LEARNING PATHS"""
        print(f"🔍 Đang truy cập course: {self.course_url}")
        await self.page.goto(self.course_url, wait_until='domcontentloaded')
        await self.wait_for_load()
        
        # Đợi content load
        await asyncio.sleep(2)
        
        # Tìm tất cả learning paths
        learning_paths = []
        
        print("\n🔄 Đang tìm learning paths...")
        try:
            path_links = await self.page.query_selector_all('a[href*="/training/paths/"]')
            print(f"   📋 Found {len(path_links)} learning path links")
            
            # Lấy tất cả URLs của paths trước để tránh stale element
            path_urls = []
            path_titles = []
            for link in path_links:
                href = await link.get_attribute('href')
                title = await link.text_content() or ""
                if href:
                    path_url = href if href.startswith('http') else f"{self.base_url}{href}"
                    if path_url not in path_urls:  # Tránh duplicate
                        path_urls.append(path_url)
                        path_titles.append(title.strip())
            
            print(f"   ✓ Unique paths to crawl: {len(path_urls)}")
            
            # Crawl từng learning path
            for i, (path_url, path_title) in enumerate(zip(path_urls, path_titles), 1):
                print(f"\n{'='*70}")
                print(f"📚 [{i}/{len(path_urls)}] Đang crawl learning path: {path_title}")
                print(f"    URL: {path_url}")
                print(f"{'='*70}")
                
                try:
                    # Lấy modules từ path này
                    path_modules = await self.get_modules_from_path(path_url, path_title)
                    
                    # Tạo learning path object với modules bên trong
                    learning_path = {
                        "title": path_title,
                        "url": path_url,
                        "module_count": len(path_modules),
                        "crawled_at": datetime.now().isoformat(),
                        "modules": path_modules  # Modules nằm trong path
                    }
                    
                    learning_paths.append(learning_path)
                    
                    print(f"\n  ✓ Hoàn thành path {i}/{len(path_urls)}")
                    print(f"  ✓ Found {len(path_modules)} modules in this path")
                    
                    # Delay giữa các paths
                    if i < len(path_urls):
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    print(f"  ⚠️ Lỗi khi crawl path {path_url}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                    
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy learning paths: {e}")
        
        # Lưu learning paths vào data
        self.data["learning_paths"] = learning_paths
        
        # Tính tổng số modules
        total_modules = sum(len(path["modules"]) for path in learning_paths)
        
        print(f"\n{'='*70}")
        print(f"📊 TỔNG KẾT:")
        print(f"  - Tổng số learning paths: {len(learning_paths)}")
        print(f"  - Tổng số modules: {total_modules}")
        print(f"{'='*70}\n")
        
        return learning_paths
    
    async def get_module_group_title(self):
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
                
                # Skip các button text
                if title.lower() in ['start', 'begin', 'launch', 'continue']:
                    continue
                
                if title:
                    modules.append({
                        'title': title,
                        'url': full_url,
                        'type': self.detect_module_type(title),
                        'content': {}
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
        
    async def crawl_module_content(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl nội dung chi tiết của module"""
        print(f"\n📖 Đang crawl module: {module['title']}")
        
        try:
            await self.page.goto(module['url'], wait_until='domcontentloaded')
            await self.wait_for_load()
            await asyncio.sleep(2)

            module["module_group"] = await self.get_module_group_title()

            
            # Lấy description
            try:
                desc_elem = await self.page.query_selector('meta[name="description"]')
                if desc_elem:
                    module['description'] = await desc_elem.get_attribute('content')
            except:
                module['description'] = ""
                
            # Lấy duration
            try:
                duration_elem = await self.page.query_selector('span[data-bi-name="duration"]')
                if duration_elem:
                    module['duration'] = await duration_elem.text_content()
            except:
                module['duration'] = ""
            
            # Lấy nội dung chi tiết của module
            module['content']['full_content'] = await self.extract_full_content()
            
            # Lấy code blocks
            module['content']['code_blocks'] = await self.extract_code_blocks()
            
            # Lấy videos với download links
            module['content']['videos'] = await self.extract_videos_enhanced()
            
            # Lấy images
            module['content']['images'] = await self.extract_images()
            
            # Nếu là quiz, lấy questions với answers
            if module['type'] == 'quiz' or 'knowledge check' in module['title'].lower():
                module['content']['questions'] = await self.extract_quiz_questions_enhanced()
                
            # Nếu là exercise, lấy tasks chi tiết
            if module['type'] == 'exercise' or 'exercise' in module['title'].lower() or 'lab' in module['title'].lower():
                module['content']['exercise_steps'] = await self.extract_exercise_enhanced()
            
            print(f"  ✅ Crawled module successfully")
            
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
            
        return module
        
    async def extract_full_content(self) -> Dict[str, Any]:
        """Trích xuất toàn bộ nội dung bài học"""
        content = {
            'sections': [],
            'headings': [],
            'paragraphs': [],
            'lists': [],
            'tables': []
        }
        
        try:
            # Lấy main content area
            main_content = await self.page.query_selector('//*[@id="module-unit-content"]')
            if not main_content:
                return content
            
            # Lấy tất cả headings
            headings = await main_content.query_selector_all('h1, h2, h3, h4, h5, h6')
            for h in headings:
                tag = await h.evaluate('el => el.tagName.toLowerCase()')
                text = await h.text_content()
                if text and text.strip():
                    content['headings'].append({
                        'level': tag,
                        'text': text.strip()
                    })
            
            # Lấy tất cả paragraphs
            paragraphs = await main_content.query_selector_all('p')
            for p in paragraphs:
                text = await p.text_content()
                if text and len(text.strip()) > 20:  # Bỏ qua đoạn quá ngắn
                    content['paragraphs'].append(text.strip())
            
            # Lấy lists (ul, ol)
            lists = await main_content.query_selector_all('ul, ol')
            for lst in lists:
                items = await lst.query_selector_all('li')
                list_items = []
                for item in items:
                    text = await item.text_content()
                    if text:
                        list_items.append(text.strip())
                if list_items:
                    content['lists'].append(list_items)
            
            # Lấy tables
            tables = await main_content.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                table_data = []
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    row_data = []
                    for cell in cells:
                        text = await cell.text_content()
                        row_data.append(text.strip() if text else '')
                    if row_data:
                        table_data.append(row_data)
                if table_data:
                    content['tables'].append(table_data)
            
            # Tạo full text từ tất cả nội dung
            full_text = []
            for section in content['headings']:
                full_text.append(f"\n## {section['text']}\n")
            for para in content['paragraphs']:
                full_text.append(para)
            
            content['full_text'] = '\n\n'.join(full_text)
            
        except Exception as e:
            print(f"      ⚠️ Lỗi extract content: {e}")
        
        return content
    
    async def extract_code_blocks(self) -> List[Dict[str, str]]:
        """Trích xuất code blocks"""
        code_blocks = []
        
        try:
            # Tìm code blocks
            code_elements = await self.page.query_selector_all('pre code, .code-block, pre')
            
            for code_elem in code_elements:
                # Lấy language
                lang = ''
                class_attr = await code_elem.get_attribute('class')
                if class_attr:
                    # Extract language from class like "language-python"
                    for cls in class_attr.split():
                        if 'language-' in cls:
                            lang = cls.replace('language-', '')
                            break
                
                code_text = await code_elem.text_content()
                if code_text and len(code_text.strip()) > 10:
                    code_blocks.append({
                        'language': lang or 'unknown',
                        'code': code_text.strip()
                    })
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract code blocks: {e}")
        
        return code_blocks
    
    async def extract_images(self) -> List[Dict[str, str]]:
        """Trích xuất images với thông tin chi tiết"""
        images = []
        
        try:
            img_elements = await self.page.query_selector_all('img')
            
            for img in img_elements:
                src = await img.get_attribute('src')
                alt = await img.get_attribute('alt') or ''
                title = await img.get_attribute('title') or ''
                
                if src and not src.startswith('data:'):  # Bỏ qua base64 images
                    full_src = src if src.startswith('http') else f"{self.base_url}{src}"
                    images.append({
                        'url': full_src.replace('../../', '/en-us/training/'),
                        'alt': alt,
                        'title': title
                    })
        
        except Exception as e:
            print(f"      ⚠️ Lỗi extract images: {e}")
        
        return images
    
    async def extract_videos_enhanced(self) -> List[Dict[str, Any]]:
        """Trích xuất video links nâng cao với download info"""
        videos = []
        
        try:
            # 1. YouTube videos
            youtube_iframes = await self.page.query_selector_all('iframe[src*="youtube.com"], iframe[src*="youtu.be"]')
            for iframe in youtube_iframes:
                src = await iframe.get_attribute('src')
                if src:
                    # Extract video ID
                    video_id = None
                    if 'embed/' in src:
                        video_id = src.split('embed/')[-1].split('?')[0]
                    elif 'v=' in src:
                        video_id = src.split('v=')[-1].split('&')[0]
                    
                    videos.append({
                        'type': 'youtube',
                        'platform': 'YouTube',
                        'embed_url': src,
                        'video_id': video_id,
                        'watch_url': f"https://www.youtube.com/watch?v={video_id}" if video_id else src,
                        'download_note': 'Use yt-dlp or youtube-dl to download'
                    })
            
            # 2. Microsoft Stream videos
            stream_iframes = await self.page.query_selector_all('iframe[src*="microsoft.com/videoplayer"], iframe[src*="msit.microsoftstream.com"], iframe[src*="microsoftstream.com"], iframe[src*="learn-video.azurefd.net"]')
            for iframe in stream_iframes:
                src = await iframe.get_attribute('src')
                if src:
                    videos.append({
                        'type': 'microsoft_stream',
                        'platform': 'Microsoft Stream',
                        'embed_url': src,
                        'download_note': 'Requires Microsoft account and Stream Recorder extension'
                    })
            
            # 3. Direct video URLs
            video_tags = await self.page.query_selector_all('video')
            for video in video_tags:
                sources = await video.query_selector_all('source')
                for source in sources:
                    src = await source.get_attribute('src')
                    video_type = await source.get_attribute('type') or 'video/mp4'
                    if src:
                        full_url = src if src.startswith('http') else f"{self.base_url}{src}"
                        videos.append({
                            'type': 'direct',
                            'platform': 'Direct Download',
                            'url': full_url,
                            'mime_type': video_type,
                            'download_note': 'Direct download available'
                        })
            
            # 4. Tìm video links trong text
            page_content = await self.page.content()
            
            # Tìm các mp4 links
            mp4_links = re.findall(r'https?://[^\s<>"]+\.mp4', page_content)
            for link in set(mp4_links):
                if not any(v.get('url') == link for v in videos):
                    videos.append({
                        'type': 'direct',
                        'platform': 'Direct Download',
                        'url': link,
                        'mime_type': 'video/mp4',
                        'download_note': 'Direct download available'
                    })
            
            if videos:
                print(f"      🎥 Found {len(videos)} videos")
            
        except Exception as e:
            print(f"      ⚠️ Lỗi extract videos: {e}")
        
        return videos
        
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
                    print("✅ Achieved 100% score!")
                    break

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

            return results

        except Exception as e:
            print(f"⚠️ Lỗi extract quiz: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def extract_exercise_enhanced(self) -> Dict[str, Any]:
        """Trích xuất bài tập/lab CHI TIẾT"""
        exercise = {
            'title': '',
            'description': '',
            'duration': '',
            'steps': [],
            'requirements': [],
            'verification': []
        }
        
        try:
            # Lấy title và description
            title_elem = await self.page.query_selector('h1, h2')
            if title_elem:
                exercise['title'] = await title_elem.text_content()
            
            # Lấy duration
            duration_elem = await self.page.query_selector('[class*="duration"], [data-duration]')
            if duration_elem:
                exercise['duration'] = await duration_elem.text_content()
            
            # Lấy description/overview
            desc_elem = await self.page.query_selector('[class*="description"], [class*="overview"], .intro p')
            if desc_elem:
                exercise['description'] = await desc_elem.text_content()
            
            # Lấy requirements/prerequisites
            req_section = await self.page.query_selector('[class*="requirement"], [class*="prerequisite"]')
            if req_section:
                req_items = await req_section.query_selector_all('li, p')
                for item in req_items:
                    text = await item.text_content()
                    if text:
                        exercise['requirements'].append(text.strip())
            
            # Lấy các bước thực hiện
            step_selectors = [
                'ol li',
                '[class*="step"]',
                '[class*="task"] li',
                'article li'
            ]
            
            for selector in step_selectors:
                steps = await self.page.query_selector_all(selector)
                if len(steps) > 3:  # Đủ steps
                    for idx, step in enumerate(steps, 1):
                        text = await step.text_content()
                        if text and len(text.strip()) > 15:
                            
                            # Lấy code blocks trong step
                            code_blocks = []
                            code_elems = await step.query_selector_all('code, pre')
                            for code in code_elems:
                                code_text = await code.text_content()
                                if code_text:
                                    code_blocks.append(code_text.strip())
                            
                            exercise['steps'].append({
                                'step_number': idx,
                                'instruction': text.strip(),
                                'code_snippets': code_blocks
                            })
                    
                    if exercise['steps']:
                        break
            
            # Lấy verification/validation steps
            verify_section = await self.page.query_selector('[class*="verify"], [class*="validation"], [class*="check"]')
            if verify_section:
                verify_items = await verify_section.query_selector_all('li, p')
                for item in verify_items:
                    text = await item.text_content()
                    if text:
                        exercise['verification'].append(text.strip())
            
            print(f"      🔨 Extracted {len(exercise['steps'])} exercise steps")
            
        except Exception as e:
            print(f"      ⚠️ Lỗi extract exercise: {e}")
        
        return exercise
        
    async def crawl(self, max_modules: int = None):
        """Hàm main để crawl toàn bộ course"""
        await self.init_browser(headless=False)
        
        try:
            # 1. Lấy danh sách learning paths với modules
            print("=" * 60)
            print("🚀 BẮT ĐẦU CRAWL MICROSOFT LEARN COURSE")
            print("=" * 60)
            
            learning_paths = await self.get_course_modules()
            
            if not learning_paths:
                print("❌ Không tìm thấy learning paths nào!")
                return
            
            total_modules = sum(len(path["modules"]) for path in learning_paths)
            print(f"\n✅ Tìm thấy {len(learning_paths)} learning paths với tổng {total_modules} modules")
            
            # 2. Crawl từng learning path và modules của nó
            module_counter = 0
            for path_idx, learning_path in enumerate(learning_paths, 1):
                print(f"\n{'=' * 70}")
                print(f"📚 LEARNING PATH {path_idx}/{len(learning_paths)}: {learning_path['title']}")
                print(f"{'=' * 70}")
                
                modules = learning_path['modules']
                
                # Giới hạn số modules nếu cần (để test)
                if max_modules and module_counter >= max_modules:
                    print(f"⚠️ Đã đạt giới hạn {max_modules} modules")
                    break
                
                # Crawl từng module trong path này
                for idx, module in enumerate(modules, 1):
                    module_counter += 1
                    
                    if max_modules and module_counter > max_modules:
                        break
                    
                    print(f"\n{'=' * 60}")
                    print(f"📖 MODULE {idx}/{len(modules)} (Tổng: {module_counter}/{total_modules})")
                    print(f"{'=' * 60}")
                    
                    module = await self.crawl_module_content(module)
                    
                    # Lưu checkpoint sau mỗi 5 modules
                    if module_counter % 5 == 0:
                        self.save_data(f"checkpoint_module_{module_counter}.json")
                    
                    await asyncio.sleep(2)  # Delay giữa các modules
                
                print(f"\n✅ Hoàn thành learning path: {learning_path['title']}")
                
            print("\n" + "=" * 60)
            print("🎉 HOÀN THÀNH CRAWL!")
            print("=" * 60)
            print(f"\n📊 Thống kê:")
            print(f"  - Số learning paths: {len(learning_paths)}")
            print(f"  - Tổng modules đã crawl: {module_counter}")
            
        except Exception as e:
            print(f"\n❌ Lỗi nghiêm trọng: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()
            
    def save_data(self, filename: str = "course_data.json"):
        """Lưu data ra file JSON"""
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 Đã lưu data vào: {filepath}")
        
        # Tạo summary
        total_modules = sum(len(path.get('modules', [])) for path in self.data.get('learning_paths', []))
        total_videos = 0
        total_code_blocks = 0
        total_images = 0
        
        for path in self.data.get('learning_paths', []):
            for module in path.get('modules', []):
                total_videos += len(module.get('content', {}).get('videos', []))
                total_code_blocks += len(module.get('content', {}).get('code_blocks', []))
                total_images += len(module.get('content', {}).get('images', []))
        
        summary = {
            'total_learning_paths': len(self.data.get('learning_paths', [])),
            'total_modules': total_modules,
            'total_videos': total_videos,
            'total_code_blocks': total_code_blocks,
            'total_images': total_images,
            'crawled_at': self.data['crawled_at']
        }
        
        # Thêm breakdown theo learning path
        path_breakdown = []
        for path in self.data.get('learning_paths', []):
            path_breakdown.append({
                'title': path.get('title', 'Unknown'),
                'url': path.get('url', ''),
                'module_count': len(path.get('modules', []))
            })
        summary['learning_paths_breakdown'] = path_breakdown
        
        summary_path = os.path.join(output_dir, 'summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"📊 Summary:")
        print(f"  - Learning Paths: {summary['total_learning_paths']}")
        print(f"  - Modules: {summary['total_modules']}")
        print(f"  - Videos: {summary['total_videos']}")
        print(f"  - Code blocks: {summary['total_code_blocks']}")
        print(f"  - Images: {summary['total_images']}")
        print(f"\n  Modules per path:")
        for path_info in path_breakdown:
            print(f"    - {path_info['title']}: {path_info['module_count']} modules")




async def main():
    # URL course cần crawl
    course_url = "https://learn.microsoft.com/en-us/training/courses/sc-200t00"
    
    crawler = MicrosoftLearnCrawler(course_url)

    # Crawl course - Sẽ tự động crawl TẤT CẢ learning paths
    await crawler.crawl(
        # max_modules=2  # Bỏ hoặc set None để crawl tất cả modules
    )
    
    # Lưu kết quả cuối cùng
    crawler.save_data("sc200_course_full.json")


if __name__ == "__main__":
    asyncio.run(main())