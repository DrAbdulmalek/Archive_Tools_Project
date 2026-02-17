#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zip_rar_folder2txt.py - النسخة الأصلية (ملف واحد كبير)
تم التحديث لدعم PDF ونقلها لمجلد منفصل، ودعم أرشيفات tar
"""

import sys
import site
try:
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
except Exception:
    pass

import zipfile
import tarfile
import os
import pathlib
import datetime
import tempfile
import sqlite3
import re
import shutil

# ============ استيراد المكتبات الاختيارية ============
RAR_SUPPORT = False
rarfile = None
try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    pass

DOCX_SUPPORT = False
try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    pass

EXCEL_SUPPORT = False
try:
    import pandas as pd
    EXCEL_SUPPORT = True
except ImportError:
    pass

HTML_SUPPORT = False
try:
    from bs4 import BeautifulSoup
    HTML_SUPPORT = True
except ImportError:
    pass

# ============ الامتدادات المدعومة ============
TEXT_EXTENSIONS = {'.txt', '.py', '.js', '.json', '.xml', '.csv', '.md', '.yml', '.yaml', 
                   '.ini', '.cfg', '.conf', '.java', '.c', '.cpp', '.h', '.cs', '.php', 
                   '.rb', '.go', '.rs', '.swift', '.kt', '.sql', '.sh', '.bat', '.ps1',
                   '.r', '.m', '.f', '.for', '.f90', '.f95', '.properties', '.toml',
                   '.lock', '.log', '.tex', '.rst', '.adoc', '.asm', '.v', '.vhdl'}

DB_EXTENSIONS = {'.db', '.sqlite', '.sqlite3'}
WORD_EXTENSIONS = {'.docx'}
EXCEL_EXTENSIONS = {'.xls', '.xlsx'}
HTML_EXTENSIONS = {'.html', '.htm'}
PDF_EXTENSIONS = {'.pdf'}  # ملفات PDF سيتم نقلها لمجلد منفصل
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz'}

# امتدادات ثنائية (يتم تجاهلها)
BINARY_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', '.obj', 
                     '.o', '.a', '.lib', '.dylib', '.bundle', '.class', '.jar', 
                     '.war', '.ear', '.apk', '.ipa', '.app', '.dmg', '.iso', 
                     '.img', '.raw', '.dat', '.pkl', '.pickle', '.npy', '.npz',
                     '.pt', '.pth', '.h5', '.hdf', '.fits', '.parquet', '.feather',
                     '.msi', '.msu'}

# ============ دوال مساعدة ============
def safe_makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def get_unique_filename(base_name, extension):
    """إنشاء اسم ملف فريد لتجنب الكتابة فوق الملفات الموجودة"""
    if not os.path.exists(base_name + extension):
        return base_name + extension
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{extension}"
        if not os.path.exists(new_name):
            return new_name
        counter += 1

def is_split_archive_extension(extension):
    ext_lower = extension.lower()
    if ext_lower.startswith('.z') and ext_lower[2:].isdigit():
        return True
    if ext_lower in ['.001', '.002', '.003', '.004', '.005', '.006', '.007', '.008', '.009', '.010',
                     '.r00', '.r01', '.r02', '.r03', '.r04', '.part1.rar', '.part2.rar', '.part3.rar']:
        return True
    return False

def should_ignore_file(file_path):
    parts = file_path.split('/')
    for part in parts:
        if part.startswith('.') and part != '.' and part != '..':
            return True
    if '__pycache__' in parts:
        return True
    if file_path.endswith('.pyc'):
        return True
    for i, part in enumerate(parts):
        if part == 'venv' and i < len(parts) - 1:
            return True
    if '/venv/' in file_path or file_path.startswith('venv/'):
        return True
    return False

def move_pdf_to_folder(pdf_path, base_dir):
    """نقل ملف PDF إلى مجلد pdfs_to_process داخل base_dir"""
    pdf_dest_dir = os.path.join(base_dir, "pdfs_to_process")
    safe_makedirs(pdf_dest_dir)
    
    dest_path = os.path.join(pdf_dest_dir, os.path.basename(pdf_path))
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(os.path.basename(pdf_path))
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            new_dest = os.path.join(pdf_dest_dir, new_name)
            if not os.path.exists(new_dest):
                dest_path = new_dest
                break
            counter += 1
    shutil.move(pdf_path, dest_path)
    return dest_path

def convert_timestamp(value):
    # نفس الدالة السابقة
    try:
        if pd.isna(value) or value is None:
            return "NULL"
        if isinstance(value, (int, float)):
            try:
                value = datetime.datetime.fromtimestamp(value)
            except:
                pass
        if isinstance(value, str):
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S'
            ]
            for fmt in formats:
                try:
                    value = datetime.datetime.strptime(value, fmt)
                    break
                except:
                    continue
        if isinstance(value, datetime.datetime):
            hour = value.hour
            if hour == 0:
                hour_12 = 12
                meridiem = "ص"
            elif 1 <= hour <= 11:
                hour_12 = hour
                meridiem = "ص"
            elif hour == 12:
                hour_12 = 12
                meridiem = "م"
            else:
                hour_12 = hour - 12
                meridiem = "م"
            return f"{value.day:02d}/{value.month:02d}/{value.year} {hour_12}:{value.minute:02d}:{value.second:02d} {meridiem}"
        return str(value)
    except Exception:
        return str(value)

def extract_text_from_html(html_content):
    if not HTML_SUPPORT:
        return html_content
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        return html_content

def process_file_content(file_path, content_bytes, is_model_file_flag=False):
    if is_model_file_flag:
        return f"[ملف في مجلد models - تم تسجيل الاسم فقط]\nاسم الملف: {file_path}\n", "Model File"
    
    ext = pathlib.Path(file_path).suffix.lower()
    if ext in ('.html', '.htm') and HTML_SUPPORT:
        try:
            content_str = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = content_bytes.decode('latin-1')
            except:
                content_str = None
        if content_str is not None:
            text = extract_text_from_html(content_str)
            return text, "Text (HTML stripped)"
    
    # تحديد نوع الملف
    if len(content_bytes) >= 4:
        if content_bytes[:4] == b'\x63\x00\x00\x00':
            return None, "Python Compiled (.pyc)"
        if content_bytes[:4] == b'\x7f\x45\x4c\x46':
            return None, "ELF Executable"
        if content_bytes[:2] == b'MZ':
            return None, "Windows Executable"
        if content_bytes[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
            return None, "PNG Image"
        if content_bytes[:3] == b'\xff\xd8\xff':
            return None, "JPEG Image"
        if content_bytes[:4] == b'%PDF':
            return None, "PDF Document"  # سيتم التعامل معها في مكان آخر
        if content_bytes[:2] == b'PK':
            return None, "ZIP Archive"
        if content_bytes[:2] == b'\x1f\x8b':
            return None, "GZIP Compressed"
    
    # محاولة فك الترميز
    try:
        content = content_bytes.decode('utf-8')
        return content, "Text"
    except UnicodeDecodeError:
        try:
            content = content_bytes.decode('latin-1')
            return content, "Text"
        except UnicodeDecodeError:
            return None, "Binary"

# دوال تصدير قواعد البيانات و Excel (نفس السابق) - سأختصرها للتوضيح
# (يمكنك الإبقاء عليها كما هي من النسخة السابقة)

def export_db_to_excel(db_path, output_excel):
    # ... (نفس الكود السابق)
    pass

def extract_db_via_excel_to_text(db_path, output_file):
    # ... (نفس الكود السابق)
    pass

def extract_db_direct_to_text(db_path, output_file):
    # ... (نفس الكود السابق)
    pass

def extract_excel_to_text(excel_path, output_file):
    # ... (نفس الكود السابق)
    pass

def extract_docx_to_text(docx_path, output_file):
    # ... (نفس الكود السابق)
    pass

def extract_html_to_text(html_path, output_file):
    # ... (نفس الكود السابق)
    pass

def extract_archive_to_text(archive_path, output_file, archive_type="zip"):
    """استخراج محتويات الأرشيف (ZIP, RAR, TAR) إلى ملف نصي واحد"""
    if not os.path.exists(archive_path):
        print(f"الملف {archive_path} غير موجود!")
        return None, 0, 0
    
    try:
        if archive_type == "zip":
            if not zipfile.is_zipfile(archive_path):
                print(f" ❌ {os.path.basename(archive_path)} ليس ملف ZIP صالح!")
                return None, 0, 0
            archive = zipfile.ZipFile(archive_path, 'r')
        elif archive_type == "rar":
            if not RAR_SUPPORT:
                print(f" ❌ مكتبة rarfile غير مثبتة. لا يمكن معالجة ملفات RAR.")
                return None, 0, 0
            try:
                archive = rarfile.RarFile(archive_path, 'r')
            except Exception as e:
                print(f" ❌ خطأ في فتح ملف RAR: {str(e)}")
                return None, 0, 0
        elif archive_type in ("tar", "tar.gz", "tgz", "tar.bz2", "tar.xz"):
            # تحديد وضع القراءة حسب الامتداد
            mode = 'r'
            if archive_type.endswith('.gz') or archive_type == 'tgz':
                mode = 'r:gz'
            elif archive_type.endswith('.bz2'):
                mode = 'r:bz2'
            elif archive_type.endswith('.xz'):
                mode = 'r:xz'
            try:
                archive = tarfile.open(archive_path, mode)
            except Exception as e:
                print(f" ❌ خطأ في فتح ملف TAR: {str(e)}")
                return None, 0, 0
        else:
            return None, 0, 0
        
        with archive:
            # الحصول على قائمة الملفات (تختلف بين zip/rar و tar)
            if archive_type in ("zip", "rar"):
                file_list = archive.namelist()
            else:  # tar
                file_list = [m.name for m in archive.getmembers() if m.isfile()]
            
            with open(output_file, 'w', encoding='utf-8') as out_file:
                out_file.write("=" * 80 + "\n")
                out_file.write(f"محتوى الأرشيف ({archive_type.upper()}): {os.path.basename(archive_path)}\n")
                out_file.write(f"تاريخ الإنشاء: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                out_file.write(f"اسم ملف الإخراج: {os.path.basename(output_file)}\n")
                out_file.write("=" * 80 + "\n\n")
                
                files_processed = 0
                files_skipped = 0
                binary_files = []
                
                for file_name in sorted(file_list):
                    # تجاهل المجلدات (بعض الأرشيفات قد تحتوي على أسماء مجلدات)
                    if file_name.endswith('/') or file_name.endswith('\\'):
                        continue
                    
                    if should_ignore_file(file_name):
                        files_skipped += 1
                        continue
                    
                    file_ext = pathlib.Path(file_name).suffix.lower()
                    
                    # تجاهل ملفات Excel/Word داخل الأرشيف (لأنها ستعالج كمستندات عند استخراجها)
                    if file_ext in EXCEL_EXTENSIONS or file_ext in WORD_EXTENSIONS:
                        files_skipped += 1
                        continue
                    
                    # تجاهل الملفات الثنائية
                    if file_ext in BINARY_EXTENSIONS:
                        binary_files.append(file_name)
                        files_skipped += 1
                        continue
                    
                    try:
                        # قراءة المحتوى حسب نوع الأرشيف
                        if archive_type in ("zip", "rar"):
                            content_bytes = archive.read(file_name)
                        else:  # tar
                            member = archive.getmember(file_name)
                            f = archive.extractfile(member)
                            content_bytes = f.read() if f else b''
                            f.close()
                        
                        if len(content_bytes) == 0:
                            continue
                        
                        # محاولة فك التشفير
                        try:
                            content = content_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                content = content_bytes.decode('latin-1')
                            except UnicodeDecodeError:
                                files_skipped += 1
                                continue
                        
                        out_file.write(f"اسم الملف: {file_name}\n")
                        out_file.write("-" * 40 + "\n")
                        out_file.write(content)
                        if not content.endswith('\n'):
                            out_file.write('\n')
                        out_file.write("\n" + "=" * 80 + "\n\n")
                        
                        files_processed += 1
                        
                    except Exception as e:
                        print(f" ⚠️ خطأ في معالجة {file_name}: {str(e)}")
                        files_skipped += 1
                        continue
                
                out_file.write("=" * 80 + "\n")
                out_file.write("ملخص المعالجة:\n")
                out_file.write(f"- عدد الملفات النصية المعالجة: {files_processed}\n")
                out_file.write(f"- عدد الملفات المتجاهلة: {files_skipped}\n")
                out_file.write(f"- إجمالي الملفات في الأرشيف: {len(file_list)}\n")
                if binary_files:
                    out_file.write(f"- عدد الملفات الثنائية المتجاهلة: {len(binary_files)}\n")
                out_file.write("=" * 80 + "\n")
        
        print(f" ✓ تم استخراج محتويات {archive_type.upper()} إلى: {output_file}")
        print(f" ✓ تمت معالجة {files_processed} ملفًا نصيًا")
        print(f" ✓ تم تجاهل {files_skipped} ملفًا")
        return output_file, files_processed, files_skipped
    
    except Exception as e:
        print(f" ❌ حدث خطأ في معالجة {archive_path}: {str(e)}")
        return None, 0, 0

def extract_single_file_to_text(file_path, output_file):
    """معالجة ملف فردي (نصي) وحفظه في ملف واحد"""
    if not os.path.isfile(file_path):
        return None, 0, 0
    ext = pathlib.Path(file_path).suffix.lower()
    
    # إذا كان PDF، نقوم بنقله بدلاً من معالجته
    if ext in PDF_EXTENSIONS:
        base_dir = os.path.dirname(file_path)
        dest = move_pdf_to_folder(file_path, base_dir)
        print(f"📄 تم نقل ملف PDF إلى: {dest}")
        print("   استخدم سكريبت PDF المخصص لاحقاً.")
        return None, 0, 1
    
    # إذا كان من أنواع الملفات التي لها معالجة خاصة
    if ext in DB_EXTENSIONS:
        return extract_db_direct_to_text(file_path, output_file)
    elif ext in EXCEL_EXTENSIONS:
        return extract_excel_to_text(file_path, output_file)
    elif ext in WORD_EXTENSIONS:
        return extract_docx_to_text(file_path, output_file)
    elif ext in HTML_EXTENSIONS:
        return extract_html_to_text(file_path, output_file)
    else:
        # ملف نصي عادي
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if len(content.strip()) == 0:
                return None, 0, 1
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"محتوى الملف: {os.path.basename(file_path)}\n")
                f.write(f"تاريخ الإنشاء: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"اسم ملف الإخراج: {os.path.basename(output_file)}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)
                if not content.endswith('\n'):
                    f.write('\n')
                f.write("\n" + "=" * 80 + "\n")
            print(f" ✓ تم استخراج محتوى الملف إلى: {output_file}")
            lines = len(content.split('\n'))
            return output_file, lines, 0
        except Exception as e:
            print(f" ❌ خطأ في معالجة {file_path}: {str(e)}")
            return None, 0, 1

def process_single_item(item_path, via_excel=False):
    """معالجة عنصر واحد"""
    results = []
    if not os.path.exists(item_path):
        print(f"❌ المسار غير موجود: {item_path}")
        return results
    
    output_dir = os.path.dirname(item_path)
    if not output_dir:
        output_dir = '/'
    base_name = os.path.basename(item_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    if os.path.isfile(item_path):
        file_ext = pathlib.Path(item_path).suffix.lower()
        
        if is_split_archive_extension(file_ext):
            print(f"⚠️ ملف جزء من أرشيف متعدد: {base_name} - سيتم تجاهله")
            return results
        
        # تحديد نوع الأرشيف
        if file_ext == '.zip':
            print(f"📦 معالجة ملف ZIP: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_zip_contents"), ".txt")
            result = extract_archive_to_text(item_path, output_file, "zip")
            if result[0]:
                results.append(result)
        elif file_ext == '.rar' and RAR_SUPPORT:
            print(f"📦 معالجة ملف RAR: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_rar_contents"), ".txt")
            result = extract_archive_to_text(item_path, output_file, "rar")
            if result[0]:
                results.append(result)
        elif file_ext in ('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz'):
            print(f"📦 معالجة ملف TAR: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_tar_contents"), ".txt")
            result = extract_archive_to_text(item_path, output_file, file_ext[1:])  # نمرر الامتداد كامل
            if result[0]:
                results.append(result)
        elif file_ext in PDF_EXTENSIONS:
            dest = move_pdf_to_folder(item_path, output_dir)
            print(f"📄 تم نقل ملف PDF إلى: {os.path.relpath(dest, output_dir)}")
        elif file_ext in DB_EXTENSIONS:
            if via_excel:
                print(f"🗄️→📊→📄 معالجة قاعدة بيانات عبر Excel: {base_name}")
                output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_db_via_excel"), ".txt")
                result = extract_db_via_excel_to_text(item_path, output_file)
            else:
                print(f"🗄️ معالجة قاعدة بيانات مباشرة: {base_name}")
                output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_db_direct"), ".txt")
                result = extract_db_direct_to_text(item_path, output_file)
            if result[0]:
                results.append(result)
        elif file_ext in EXCEL_EXTENSIONS:
            print(f"📊 معالجة ملف Excel: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_excel_contents"), ".txt")
            result = extract_excel_to_text(item_path, output_file)
            if result[0]:
                results.append(result)
        elif file_ext in WORD_EXTENSIONS:
            print(f"📝 معالجة مستند Word: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_doc_contents"), ".txt")
            result = extract_docx_to_text(item_path, output_file)
            if result[0]:
                results.append(result)
        elif file_ext in HTML_EXTENSIONS:
            print(f"🌐 استخراج نص من HTML: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_html_text"), ".txt")
            result = extract_html_to_text(item_path, output_file)
            if result[0]:
                results.append(result)
        else:
            # ملف نصي عادي
            print(f"📄 معالجة ملف نصي: {base_name}")
            output_file = get_unique_filename(os.path.join(output_dir, name_without_ext + "_file_contents"), ".txt")
            result = extract_single_file_to_text(item_path, output_file)
            if result[0]:
                results.append(result)
    
    elif os.path.isdir(item_path):
        print(f"📁 معالجة المجلد: {base_name} (لا يتم إنشاء ملف واحد للمجلدات في هذه النسخة)")
        # إذا أردت دعم المجلدات، يمكن إضافة منطق مشابه للنسخة المنفصلة
    else:
        print(f"❌ نوع غير معروف: {item_path}")
    
    return results

def main():
    print("🔍 فحص المكتبات المثبتة:")
    print(f" ✓ zipfile: مثبت")
    print(f" ✓ tarfile: مثبت")
    print(f" ✓ sqlite3: مثبت")
    print(f" ✓ python-docx: {'مثبت' if DOCX_SUPPORT else 'غير مثبت'}")
    print(f" ✓ pandas: {'مثبت' if EXCEL_SUPPORT else 'غير مثبت'}")
    print(f" ✓ beautifulsoup4: {'مثبت' if HTML_SUPPORT else 'غير مثبت'}")
    print(f" ✓ rarfile: {'مثبت' if RAR_SUPPORT else 'غير مثبت'}")
    print()
    
    if len(sys.argv) < 2:
        print("الاستخدام: python script.py [--via-excel] ملف1 ملف2 ...")
        input("اضغط Enter للخروج...")
        return
    
    via_excel = "--via-excel" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--via-excel"]
    if via_excel:
        print("💡 استخدام التحويل عبر Excel للقواعد البيانات")
    
    all_results = []
    total_processed = 0
    total_skipped = 0
    
    print(f"\n🎯 تم العثور على {len(args)} عنصر للمعالجة:")
    for i, item in enumerate(args, 1):
        print(f"\n[{i}/{len(args)}] {'='*50}")
        results = process_single_item(item, via_excel)
        for out_file, proc, skip in results:
            all_results.append(out_file)
            total_processed += proc
            total_skipped += skip
    
    print("\n" + "=" * 60)
    print("📊 ملخص المعالجة النهائي:")
    print("=" * 60)
    print(f"📁 عدد الملفات النصية المنشأة: {len(all_results)}")
    print(f"📄 إجمالي العناصر المعالجة: {total_processed}")
    print(f"🚫 إجمالي العناصر المتجاهلة: {total_skipped}")
    
    print("\n✅ اكتملت المعالجة!")
    input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()
