# 🚀 HƯỚNG DẪN SỬ DỤNG NHANH

## TÓM TẮT

Script này crawl **TOÀN BỘ** nội dung từ Microsoft Learn Course bao gồm:
- ✅ Nội dung bài học chi tiết (text, headings, paragraphs, tables, lists)
- ✅ Code blocks với syntax
- ✅ Videos (YouTube + Microsoft Stream) với download links
- ✅ Câu hỏi Knowledge Check với options và đáp án
- ✅ Bài tập/Labs với từng bước chi tiết
- ✅ Images với metadata

## SETUP - CHỈ 1 LẦN

```bash
# 1. Clone/Download code về
cd Crawl_Data

# 2. Chạy setup script
./setup.sh

# Hoặc manual:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## SỬ DỤNG

### 🎯 Cách 1: Quick Start (ĐỀ XUẤT)

```bash
python quick_start.py
```

Chọn chế độ:
- **1**: Test nhanh (5 modules) - 5-10 phút
- **2**: Chỉ lấy danh sách modules - 2 phút  
- **3**: Full crawl (TẤT CẢ) - 1-2 giờ ⚠️
- **4**: Tùy chỉnh số modules

### 🎯 Cách 2: Manual

```bash
# Edit crawler.py dòng cuối, đổi max_modules
python crawler.py
```

## KẾT QUẢ

File output trong folder `output/`:
```
output/
├── sc200_course_full.json      # Data đầy đủ
├── checkpoint_module_X.json    # Checkpoints
└── summary.json                # Tóm tắt
```

## XEM KẾT QUẢ

### Export ra CSV (dễ đọc hơn)

```bash
python export_csv.py
```

Tạo 5 files CSV:
- `*_modules.csv` - Danh sách modules
- `*_units.csv` - Chi tiết units
- `*_videos.csv` - Tất cả videos
- `*_questions.csv` - Câu hỏi + đáp án
- `*_exercises.csv` - Bài tập

### Download Videos

```bash
# Cài yt-dlp trước (cho YouTube)
brew install yt-dlp

# Chạy download script
python download_videos.py
```

## CẤU TRÚC DATA

Mỗi unit có:

```json
{
  "content": {
    "full_content": {
      "full_text": "Nội dung đầy đủ...",
      "headings": [...],
      "paragraphs": [...],
      "lists": [...],
      "tables": [...]
    },
    "code_blocks": [
      {"language": "python", "code": "..."}
    ],
    "videos": [
      {
        "type": "youtube",
        "video_id": "abc123",
        "watch_url": "https://youtube.com/watch?v=...",
        "download_note": "Use yt-dlp"
      }
    ],
    "questions": [
      {
        "question": "...",
        "options": ["A", "B", "C"],
        "correct_answers": ["B"],
        "explanation": "..."
      }
    ],
    "exercise_steps": {
      "steps": [
        {
          "step_number": 1,
          "instruction": "...",
          "code_snippets": ["..."]
        }
      ]
    }
  }
}
```

## LƯU Ý

### ✅ CRAWL ĐƯỢC

- ✅ Toàn bộ nội dung text
- ✅ Code examples
- ✅ YouTube video links (có thể download bằng yt-dlp)
- ✅ Direct video downloads
- ✅ Câu hỏi quiz (options)
- ✅ Bài tập chi tiết
- ✅ Images

### ⚠️ GIỚI HẠN

- ⚠️ **Đáp án quiz**: Một số đáp án chỉ hiện sau khi submit, cần login
- ⚠️ **Microsoft Stream videos**: Cần account và extension để download
- ⚠️ **Interactive exercises**: Chỉ lấy được instructions, không run được
- ⚠️ **Rate limiting**: Chạy quá nhanh có thể bị block tạm thời

### 💡 TIPS

1. **Chạy test trước**: Dùng option 1 (Quick Test) để kiểm tra
2. **Checkpoints**: Script tự động lưu sau mỗi module, có thể dừng và resume
3. **Headless mode**: Đổi `headless=False` → `True` trong code để chạy nền
4. **Slow network**: Tăng timeout trong code nếu mạng chậm
5. **Resume sau lỗi**: Dùng checkpoint files để continue

## TROUBLESHOOTING

### Lỗi "playwright not found"
```bash
pip install playwright
playwright install chromium
```

### Browser bị đóng giữa chừng
- Network issue hoặc website block
- Giảm tốc độ crawl (tăng delay)
- Chạy lại với checkpoint files

### Không lấy được videos/questions
- Trang cần login → dùng `auth_helper.py`
- Content load chậm → tăng `asyncio.sleep()` time
- Anti-scraping → đổi user agent hoặc dùng proxy

### Out of memory
- Giảm số modules crawl một lúc
- Crawl từng phần rồi merge sau

## HỖ TRỢ

Nếu cần crawl course khác:
1. Đổi URL trong `crawler.py` hoặc `quick_start.py`
2. Chạy lại script

Format data không đúng ý:
1. Sửa trong `crawler.py` các hàm `extract_*`
2. Hoặc dùng `export_csv.py` để customize output
