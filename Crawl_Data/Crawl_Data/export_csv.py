#!/usr/bin/env python3
"""
Export JSON data sang CSV format để dễ đọc hơn
"""

import json
import csv
import os
from pathlib import Path


def export_to_csv(json_file: str):
    """Export JSON data sang CSV files"""
    
    print(f"📖 Đang đọc file: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    base_name = Path(json_file).stem
    output_dir = Path("output")
    
    # 1. Export modules summary
    modules_csv = output_dir / f"{base_name}_modules.csv"
    print(f"📝 Export modules -> {modules_csv}")
    
    with open(modules_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Module #', 'Title', 'URL', 'Description', 'Duration', 'Units Count'])
        
        for idx, module in enumerate(data.get('modules', []), 1):
            writer.writerow([
                idx,
                module.get('title', ''),
                module.get('url', ''),
                module.get('description', '')[:100] + '...' if len(module.get('description', '')) > 100 else module.get('description', ''),
                module.get('duration', ''),
                len(module.get('units', []))
            ])
    
    # 2. Export units detail
    units_csv = output_dir / f"{base_name}_units.csv"
    print(f"📝 Export units -> {units_csv}")
    
    with open(units_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Module', 'Unit #', 'Unit Title', 'Type', 'URL', 'Has Videos', 'Video Count', 'Has Questions'])
        
        for module in data.get('modules', []):
            module_title = module.get('title', '')
            for idx, unit in enumerate(module.get('units', []), 1):
                content = unit.get('content', {})
                videos = content.get('videos', [])
                questions = content.get('questions', [])
                
                writer.writerow([
                    module_title,
                    idx,
                    unit.get('title', ''),
                    unit.get('type', ''),
                    unit.get('url', ''),
                    'Yes' if videos else 'No',
                    len(videos),
                    'Yes' if questions else 'No'
                ])
    
    # 3. Export videos
    videos_csv = output_dir / f"{base_name}_videos.csv"
    print(f"📝 Export videos -> {videos_csv}")
    
    with open(videos_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Module', 'Video #', 'URL'])
        
        for module in data.get('modules', []):
            module_title = module.get('title', '')

            videos = module.get('content', {}).get('videos', [])
                
            for idx, video in enumerate(videos, 1):
                    writer.writerow([
                        module_title,
                        idx,
                        video.get('embed_url', '')
                    ])
    
    # 4. Export questions
    questions_csv = output_dir / f"{base_name}_questions.csv"
    print(f"📝 Export questions -> {questions_csv}")
    
    with open(questions_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Module', 'Unit', 'Question #', 'Type', 'Question', 'Options'])
        
        for module in data.get('modules', []):
            module_title = module.get('title', '')
            for unit in module.get('units', []):
                unit_title = unit.get('title', '')
                questions = unit.get('content', {}).get('questions', [])
                
                for question in questions:
                    q_num = question.get('question_number', '')
                    writer.writerow([
                        module_title,
                        unit_title,
                        q_num,
                        question.get('type', ''),
                        question.get('question', ''),
                        ' | '.join(question.get('options', []))
                    ])
    
    # 5. Export exercises
    exercises_csv = output_dir / f"{base_name}_exercises.csv"
    print(f"📝 Export exercises -> {exercises_csv}")
    
    with open(exercises_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Module', 'Unit', 'Exercise Steps'])
        
        for module in data.get('modules', []):
            module_title = module.get('title', '')
            for unit in module.get('units', []):
                unit_title = unit.get('title', '')
                steps = unit.get('content', {}).get('exercise_steps', [])
                
                if steps:
                    for idx, step in enumerate(steps, 1):
                        writer.writerow([
                            module_title,
                            unit_title,
                            f"Step {idx}: {step[:200]}"
                        ])
    
    print("\n✅ Export hoàn tất!")
    print(f"📊 Tổng số files CSV: 5")
    print(f"📁 Vị trí: {output_dir}/")


def main():
    print("""
╔════════════════════════════════════════════════╗
║      Export JSON to CSV Converter              ║
╚════════════════════════════════════════════════╝
""")
    
    output_dir = Path("output")
    json_files = list(output_dir.glob("*.json"))
    
    if not json_files:
        print("❌ Không tìm thấy file JSON nào trong folder output/")
        return
    
    print("📋 Các file JSON có sẵn:")
    for idx, file in enumerate(json_files, 1):
        print(f"  {idx}. {file.name}")
    
    print()
    choice = input("Chọn file để export (số thứ tự hoặc 'all' cho tất cả): ").strip().lower()
    
    if choice == 'all':
        for json_file in json_files:
            print(f"\n{'='*50}")
            export_to_csv(json_file)
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(json_files):
                export_to_csv(json_files[idx])
            else:
                print("❌ Số thứ tự không hợp lệ")
        except ValueError:
            print("❌ Input không hợp lệ")


if __name__ == "__main__":
    main()
