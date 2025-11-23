# Microsoft Learn Course Crawler

Script Python để crawl toàn bộ nội dung course từ Microsoft Learn bao gồm:
- 📚 **Modules** với mô tả đầy đủ
- 📹 **Videos** (YouTube, Microsoft Stream) với download links
- 📝 **Nội dung bài học** chi tiết (headings, paragraphs, code blocks, tables)
- ❓ **Knowledge Check Questions** với options và đáp án
- � **Exercises/Labs** với từng bước chi tiết
- 🖼️ **Images** với alt text và titles

## ⚠️ Tại sao KHÔNG dùng n8n?

**n8n KHÔNG phù hợp** cho task này vì:
- ❌ Microsoft Learn là dynamic website (JavaScript rendering)
- ❌ Cần browser automation để load content
- ❌ Phải handle authentication và cookies
- ❌ Quiz/exercises có anti-scraping protection
- ❌ n8n chỉ phù hợp với simple API/HTTP requests

**✅ Giải pháp: Python + Playwright** - automation browser thực sự!

## Yêu cầu

- Python 3.8+
- Playwright

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cài đặt Playwright browsers

```bash
playwright install chromium
```

## Sử dụng

### 🚀 Quick Start (Khuyến nghị)

```bash
python quick_start.py
```

Menu sẽ hiện:
1. **Quick Test** (5 modules) - Test nhanh 5-10 phút
2. **Modules Only** - Chỉ lấy danh sách modules
3. **Full Crawl** - Crawl toàn bộ (1-2 giờ)
4. **Custom** - Tùy chỉnh số modules

### 📥 Download Videos

Sau khi crawl xong:

```bash
python download_videos.py
```

Hỗ trợ:
- YouTube videos (cần yt-dlp: `brew install yt-dlp`)
- Direct video downloads
- Generate download script

### 📊 Export to CSV

```bash
python export_csv.py
```

Tạo các file CSV:
- `*_modules.csv` - Danh sách modules
- `*_units.csv` - Chi tiết units
- `*_videos.csv` - Tất cả videos
- `*_questions.csv` - Câu hỏi và đáp án
- `*_exercises.csv` - Bài tập

## Authentication (Optional)

Nếu cần đăng nhập Microsoft account:

1. Tạo file `.env`:
```bash
MS_EMAIL=your_email@example.com
MS_PASSWORD=your_password
```

2. Chạy script login:
```bash
python auth_helper.py
```

3. Session sẽ được lưu vào `.auth/microsoft_session.json`

## Output

Kết quả được lưu trong folder `output/`:

- `sc200_course_full.json` - Dữ liệu đầy đủ
- `checkpoint_module_X.json` - Checkpoint sau mỗi module
- `summary.json` - Tóm tắt số liệu

### Cấu trúc JSON output

```json
{
  "course_url": "...",
  "crawled_at": "2025-11-16T...",
  "modules": [
    {
      "title": "Module title",
      "url": "...",
      "description": "Full description",
      "duration": "45 min",
      "units": [
        {
          "title": "Unit title",
          "url": "...",
          "type": "content|exercise|quiz|introduction|summary",
          "content": {
            "full_content": {
              "full_text": "Complete text content",
              "headings": [{"level": "h2", "text": "..."}],
              "paragraphs": ["..."],
              "lists": [["item1", "item2"]],
              "tables": [[["cell1", "cell2"]]]
            },
            "code_blocks": [
              {
                "language": "python",
                "code": "print('hello')"
              }
            ],
            "videos": [
              {
                "type": "youtube",
                "platform": "YouTube",
                "video_id": "abc123",
                "watch_url": "https://youtube.com/watch?v=abc123",
                "embed_url": "...",
                "download_note": "Use yt-dlp"
              }
            ],
            "images": [
              {
                "url": "https://...",
                "alt": "Description",
                "title": "Title"
              }
            ],
            "questions": [
              {
                "question_number": 1,
                "question": "What is...?",
                "options": ["A", "B", "C"],
                "correct_answers": ["B"],
                "explanation": "Because...",
                "type": "multiple_choice"
              }
            ],
            "exercise_steps": {
              "title": "Exercise name",
              "description": "...",
              "duration": "30 min",
              "requirements": ["Azure account", "..."],
              "steps": [
                {
                  "step_number": 1,
                  "instruction": "Do this...",
                  "code_snippets": ["az login", "..."]
                }
              ],
              "verification": ["Check if..."]
            }
          }
        }
      ]
    }
  ]
}
```

## Features

✅ **Full Content Extraction**
- Toàn bộ text content (headings, paragraphs, lists, tables)
- Code blocks với syntax highlighting info
- Images với metadata

✅ **Video Extraction**
- YouTube videos với video ID và watch URLs
- Microsoft Stream embeds
- Direct video downloads
- Download instructions cho từng loại

✅ **Quiz & Questions**
- Câu hỏi với tất cả options
- Đáp án đúng (nếu có)
- Explanations/feedback

✅ **Exercises & Labs**
- Từng bước chi tiết
- Code snippets trong mỗi step
- Requirements và verification steps

✅ **Smart Crawling**
- Auto checkpoint sau mỗi module
- Resume capability
- Rate limiting tránh bị block
- Error handling và retry  

## Lưu ý

- Script chạy với browser visible (`headless=False`) để debug dễ hơn
- Có delay giữa các requests để tránh rate limit
- Checkpoint tự động lưu sau mỗi module
- Có thể dừng và tiếp tục bằng checkpoint files

## Troubleshooting

### Lỗi "playwright not found"
```bash
pip install playwright
playwright install chromium
```

### Crawl chậm
- Tăng `headless=True` trong `init_browser()` để chạy nền
- Giảm delay time trong code

### Thiếu nội dung
- Một số nội dung yêu cầu đăng nhập → dùng `auth_helper.py`
- Một số content bị protect → cần manual check

## License

MIT
