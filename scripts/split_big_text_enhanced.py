#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_big_text_enhanced.py - تقسيم الملف النصي الكبير إلى ملفات منفصلة
مع تنظيف أسماء الملفات وإضافة ترويسة موحدة لتسهيل إزالة المكررات.
الاستخدام: python split_big_text_enhanced.py <ملف_نصي_كبير> [ملف2 ...]
"""

import os
import sys
import re
import shutil

def safe_filename(filename, max_length=150):
    """
    تنظيف اسم الملف ليكون صالحاً لأنظمة الملفات.
    - إزالة الأحرف غير المسموح بها (/:*?"<>|)
    - إزالة أسطر جديدة واستبدالها بمسافة
    - استبدال المسافات المتعددة بمسافة واحدة
    - تقصير الاسم إذا تجاوز الطول المحدد
    """
    # استبدال أي أسطر جديدة بمسافة
    filename = filename.replace('\n', ' ').replace('\r', ' ').strip()
    # إزالة الأحرف غير المسموح بها
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # استبدال المسافات المتعددة بمسافة واحدة
    filename = re.sub(r'\s+', ' ', filename)
    # قص الطول
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename

def get_unique_dirname(target_dir, base_name):
    """إنشاء اسم مجلد فريد لتجنب التكرار"""
    dir_path = os.path.join(target_dir, base_name + "_split")
    if not os.path.exists(dir_path):
        return dir_path
    counter = 1
    while True:
        new_path = os.path.join(target_dir, f"{base_name}_split_{counter}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def split_big_text_file(file_path):
    if not os.path.isfile(file_path):
        print(f"❌ الملف غير موجود: {file_path}")
        return False

    print(f"🔍 تقسيم الملف: {os.path.basename(file_path)}")

    # مجلد الإخراج
    output_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    target_dir = get_unique_dirname(output_dir, base_name)
    os.makedirs(target_dir, exist_ok=True)
    print(f"📁 مجلد الإخراج: {target_dir}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # نمط التعرف على الأقسام: "اسم الملف: " ثم اسم الملف (حتى نهاية السطر)
    # ثم سطر من "-" ثم المحتوى حتى سطر من "="
    pattern = r'اسم الملف: (.+?)\n-{40,}\n(.*?)\n={80,}'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        # طريقة احتياطية: استخدام "اسم الملف:" كفاصل
        parts = content.split('اسم الملف: ')
        if parts[0].strip() == '':
            parts = parts[1:]
        for part in parts:
            # السطر الأول هو اسم الملف
            lines = part.split('\n', 1)
            if len(lines) < 2:
                continue
            file_name_line = lines[0].strip()
            rest = lines[1]
            # نقسم المحتوى عند ظهور "=" بكمية كبيرة
            content_part = rest.split('=' * 80)[0].strip()
            if not content_part:
                continue
            # تنظيف اسم الملف
            safe_name = safe_filename(file_name_line)
            # إذا كان الاسم فارغاً، نتجاهل
            if not safe_name:
                continue
            # بناء المسار
            dest_path = os.path.join(target_dir, safe_name)
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            # إضافة ترويسة
            header = f"# المصدر: {os.path.basename(file_path)}\n# الملف الأصلي: {file_name_line}\n# التقسيم: {safe_name}\n\n"
            with open(dest_path, 'w', encoding='utf-8') as out_f:
                out_f.write(header + content_part)
            print(f"   ✓ {safe_name}")
    else:
        for file_name, file_content in matches:
            file_name = file_name.strip()
            safe_name = safe_filename(file_name)
            if not safe_name:
                continue
            # استبدال \ بـ / لتوحيد المسارات (اختياري)
            safe_name = safe_name.replace('\\', '/')
            dest_path = os.path.join(target_dir, safe_name)
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            header = f"# المصدر: {os.path.basename(file_path)}\n# الملف الأصلي: {file_name}\n# التقسيم: {os.path.basename(dest_path)}\n\n"
            with open(dest_path, 'w', encoding='utf-8') as out_f:
                out_f.write(header + file_content.strip())
            print(f"   ✓ {safe_name}")

    # حذف الملف الأصلي بعد النجاح
    try:
        os.remove(file_path)
        print(f"🗑️ تم حذف الملف الأصلي: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"⚠️ فشل حذف الملف الأصلي: {str(e)}")

    return True

def main():
    if len(sys.argv) < 2:
        print("الاستخدام: python split_big_text_enhanced.py <ملف_نصي_كبير> [ملف2 ...]")
        input("اضغط Enter للخروج...")
        return

    for file_path in sys.argv[1:]:
        split_big_text_file(file_path)
        print("-" * 50)

    input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()
