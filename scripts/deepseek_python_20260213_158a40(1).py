#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import os
import sys
import pathlib
import datetime
import subprocess
import tempfile

# محاولة استيراد مكتبة rarfile
RAR_SUPPORT = False
rarfile = None
try:
    import rarfile
    RAR_SUPPORT = True
except ImportError:
    pass

# قائمة الامتدادات النصية المعروفة
TEXT_EXTENSIONS = {
    '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', 
    '.csv', '.md', '.yml', '.yaml', '.ini', '.cfg', '.conf',
    '.java', '.c', '.cpp', '.h', '.cs', '.php', '.rb', '.go',
    '.rs', '.swift', '.kt', '.sql', '.sh', '.bat', '.ps1',
    '.r', '.m', '.f', '.for', '.f90', '.f95', '.properties',
    '.toml', '.lock', '.log', '.tex', '.rst', '.adoc', '.asm',
    '.v', '.vhdl', '.verilog', '.ps', '.svg', '.ts', '.tsx',
    '.jsx', '.vue', '.svelte', '.elm', '.clj', '.scala', '.hs',
    '.lhs', '.erl', '.ex', '.exs', '.ml', '.mli'
}

# قائمة الامتدادات الثنائية المعروفة
BINARY_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
    '.obj', '.o', '.a', '.lib', '.dylib', '.bundle', '.class',
    '.jar', '.war', '.ear', '.apk', '.ipa', '.app', '.dmg',
    '.iso', '.img', '.raw', '.dat', '.db', '.sqlite', '.mdb',
    '.accdb', '.odb', '.hdf5', '.nc', '.mat', '.pkl', '.pickle',
    '.npy', '.npz', '.pt', '.pth', '.h5', '.hdf', '.fits',
    '.parquet', '.feather', '.orc', '.avro', '.proto', '.pb'
}

def is_split_archive_extension(extension):
    ext_lower = extension.lower()
    if ext_lower.startswith('.z'):
        remaining = ext_lower[2:]
        if remaining.isdigit():
            return True
    if ext_lower in ['.001', '.002', '.003', '.004', '.005', 
                     '.006', '.007', '.008', '.009', '.010',
                     '.r00', '.r01', '.r02', '.r03', '.r04',
                     '.part1.rar', '.part2.rar', '.part3.rar']:
        return True
    return False

def install_unrar_windows():
    try:
        import urllib.request
        print("  🔧 محاولة تثبيت unrar تلقائيًا...")
        unrar_url = "https://www.rarlab.com/rar/unrarw32.exe"
        temp_dir = tempfile.gettempdir()
        unrar_exe = os.path.join(temp_dir, "unrar.exe")
        print(f"  📥 جاري تنزيل unrar...")
        urllib.request.urlretrieve(unrar_url, unrar_exe)
        print(f"  📦 جاري استخراج unrar...")
        unrar_dir = os.path.join(temp_dir, "unrar")
        os.makedirs(unrar_dir, exist_ok=True)
        try:
            subprocess.run([unrar_exe, f"-o{unrar_dir}"], capture_output=True, check=True)
        except:
            try:
                import py7zr
                with py7zr.SevenZipFile(unrar_exe, mode='r') as z:
                    z.extractall(path=unrar_dir)
            except:
                pass
        for root, dirs, files in os.walk(unrar_dir):
            if "unrar.exe" in files:
                unrar_path = os.path.join(root, "unrar.exe")
                rarfile.UNRAR_TOOL = unrar_path
                print(f"  ✅ تم العثور على unrar في: {unrar_path}")
                return True
        print("  ⚠️  لم يتم العثور على unrar.exe في الملف المستخرج")
        return False
    except Exception as e:
        print(f"  ❌ فشل تثبيت unrar تلقائيًا: {str(e)}")
        print(f"  ℹ️  يمكنك تثبيت WinRAR يدويًا من: https://www.win-rar.com/")
        return False

def get_unique_filename(target_dir, base_name, extension=".txt"):
    """إنشاء اسم ملف فريد في المسار target_dir"""
    counter = 1
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = os.path.join(target_dir, base_name)
    if not os.path.exists(base_path + extension):
        return base_path + extension
    new_path = os.path.join(target_dir, f"{base_name}_{timestamp}{extension}")
    if not os.path.exists(new_path):
        return new_path
    import random
    random_suffix = random.randint(1000, 9999)
    new_path = os.path.join(target_dir, f"{base_name}_{timestamp}_{random_suffix}{extension}")
    if not os.path.exists(new_path):
        return new_path
    while True:
        new_path = os.path.join(target_dir, f"{base_name}_{timestamp}_{counter}{extension}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def is_text_file(content_bytes):
    if not content_bytes:
        return False
    try:
        content_bytes.decode('utf-8')
        return True
    except UnicodeDecodeError:
        try:
            content_bytes.decode('latin-1')
            return True
        except UnicodeDecodeError:
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
        if part == 'venv':
            if i < len(parts) - 1:
                return True
    if '/venv/' in file_path:
        return True
    if file_path.startswith('venv/'):
        return True
    return False

def is_model_file(file_path):
    file_path_lower = file_path.lower()
    patterns = ['models/', 'models\\', '/models/', '\\models\\']
    for pattern in patterns:
        if pattern in file_path_lower:
            return True
    if file_path_lower.startswith('models/'):
        return True
    return False

def get_file_type(file_path, content_bytes):
    if len(content_bytes) >= 4:
        if content_bytes[:4] == b'\x63\x00\x00\x00':
            return "Python Compiled (.pyc)"
        if content_bytes[:4] == b'\x7f\x45\x4c\x46':
            return "ELF Executable"
        if content_bytes[:2] == b'MZ':
            return "Windows Executable"
        if content_bytes[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
            return "PNG Image"
        if content_bytes[:3] == b'\xff\xd8\xff':
            return "JPEG Image"
        if content_bytes[:4] == b'%PDF':
            return "PDF Document"
        if content_bytes[:2] == b'PK':
            return "ZIP Archive"
        if content_bytes[:2] == b'\x1f\x8b':
            return "GZIP Compressed"
    if is_text_file(content_bytes):
        return "Text"
    return "Binary"

def process_file_content(file_path, content_bytes, is_model_file_flag=False):
    if is_model_file_flag:
        return f"[ملف في مجلد models - تم تسجيل الاسم فقط]\nاسم الملف: {file_path}\n", "Model File"
    file_type = get_file_type(file_path, content_bytes)
    if file_type != "Text":
        return None, file_type
    try:
        content = content_bytes.decode('utf-8')
        return content, "Text"
    except UnicodeDecodeError:
        try:
            content = content_bytes.decode('latin-1')
            return content, "Text"
        except UnicodeDecodeError:
            return None, "Binary"

def extract_single_file_to_text(file_path, output_file):
    if not os.path.exists(file_path):
        print(f"الملف {file_path} غير موجود!")
        return None, 0, 0, []
    if not os.path.isfile(file_path):
        print(f"{file_path} ليس ملفًا!")
        return None, 0, 0, []
    
    ext = pathlib.Path(file_path).suffix.lower()
    ignored_files = []
    
    if ext in BINARY_EXTENSIONS:
        reason = f"امتداد ثنائي معروف {ext}"
        ignored_files.append((os.path.basename(file_path), reason))
        print(f"  ⚠️ تجاهل ({reason}): {os.path.basename(file_path)}")
        return None, 0, 1, ignored_files
    
    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        
        if len(content_bytes) == 0:
            reason = "ملف فارغ"
            ignored_files.append((os.path.basename(file_path), reason))
            print(f"  ⚠️ تجاهل ({reason}): {os.path.basename(file_path)}")
            return None, 0, 1, ignored_files
        
        is_model = is_model_file(file_path)
        content, file_type = process_file_content(file_path, content_bytes, is_model)
        
        if file_type != "Text" and file_type != "Model File":
            reason = f"نوع الملف: {file_type}"
            ignored_files.append((os.path.basename(file_path), reason))
            print(f"  ⚠️ تجاهل ({reason}): {os.path.basename(file_path)}")
            return None, 0, 1, ignored_files
        
        with open(output_file, 'w', encoding='utf-8') as out_file:
            out_file.write("=" * 80 + "\n")
            out_file.write(f"محتوى الملف: {os.path.basename(file_path)}\n")
            out_file.write(f"تاريخ الإنشاء: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out_file.write(f"اسم ملف الإخراج: {os.path.basename(output_file)}\n")
            out_file.write("=" * 80 + "\n\n")
            out_file.write(f"اسم الملف: {os.path.basename(file_path)}\n")
            out_file.write("-" * 40 + "\n")
            if is_model:
                out_file.write(content)
            elif content:
                out_file.write(content)
            if content and not content.endswith('\n'):
                out_file.write('\n')
            out_file.write("\n" + "=" * 80 + "\n")
            
            # كتابة الملفات المتجاهلة
            out_file.write("\n" + "=" * 80 + "\n")
            out_file.write("الملفات المتجاهلة:\n")
            out_file.write("=" * 80 + "\n")
            if ignored_files:
                for fname, reason in sorted(ignored_files):
                    out_file.write(f"- {fname} : {reason}\n")
            else:
                out_file.write("لم يتم تجاهل أي ملف.\n")
        
        print(f"  ✓ تم استخراج محتوى الملف إلى: {output_file}")
        return output_file, 1, 0, ignored_files
        
    except Exception as e:
        reason = f"خطأ في القراءة: {str(e)}"
        ignored_files.append((os.path.basename(file_path), reason))
        print(f"  ⚠️ تجاهل ({reason}): {os.path.basename(file_path)}")
        return None, 0, 1, ignored_files

def extract_archive_to_text(archive_path, output_file, archive_type="zip"):
    if not os.path.exists(archive_path):
        print(f"الملف {archive_path} غير موجود!")
        return None, 0, 0, []
    
    ignored_files = []
    
    try:
        if archive_type == "zip":
            if not zipfile.is_zipfile(archive_path):
                print(f"  ❌ {os.path.basename(archive_path)} ليس ملف ZIP صالح!")
                return None, 0, 0, []
            archive = zipfile.ZipFile(archive_path, 'r')
            use_unrar = False
        elif archive_type == "rar":
            if not RAR_SUPPORT:
                print(f"  ❌ مكتبة rarfile غير مثبتة. لا يمكن معالجة ملفات RAR.")
                return None, 0, 0, []
            
            unrar_path = None
            possible_paths = [
                'unrar',
                'C:\\Program Files\\WinRAR\\UnRAR.exe',
                'C:\\Program Files (x86)\\WinRAR\\UnRAR.exe',
                'C:\\Program Files\\7-Zip\\7z.exe',
                '/usr/bin/unrar',
                '/usr/local/bin/unrar',
                '/usr/bin/7z',
            ]
            for path in possible_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=2)
                    if result.returncode == 0:
                        unrar_path = path
                        break
                except:
                    continue
            use_unrar = unrar_path is not None
            
            if not use_unrar and sys.platform == "win32":
                if install_unrar_windows():
                    for path in possible_paths:
                        try:
                            result = subprocess.run([path, '--version'], capture_output=True, timeout=2)
                            if result.returncode == 0:
                                unrar_path = path
                                use_unrar = True
                                break
                        except:
                            continue
            
            try:
                if not rarfile.is_rarfile(archive_path):
                    print(f"  ❌ {os.path.basename(archive_path)} ليس ملف RAR صالح!")
                    return None, 0, 0, []
                if use_unrar and unrar_path:
                    rarfile.UNRAR_TOOL = unrar_path
                    print(f"  ℹ️  استخدام {os.path.basename(unrar_path)} لفتح ملف RAR")
                archive = rarfile.RarFile(archive_path, 'r')
            except rarfile.NeedFirstVolume:
                print(f"  ❌ {os.path.basename(archive_path)} يحتاج إلى ملفات RAR أخرى (ملف متعدد الأجزاء).")
                return None, 0, 0, []
            except Exception as e:
                print(f"  ❌ خطأ في فتح ملف RAR: {str(e)}")
                return None, 0, 0, []
        
        with archive:
            file_list = archive.namelist()
            
            with open(output_file, 'w', encoding='utf-8') as out_file:
                out_file.write("=" * 80 + "\n")
                out_file.write(f"محتوى الأرشيف ({archive_type.upper()}): {os.path.basename(archive_path)}\n")
                if archive_type == "rar":
                    out_file.write(f"أداة الاستخراج: {'unrar' if use_unrar else 'الموزع المدمج'}\n")
                out_file.write(f"تاريخ الإنشاء: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                out_file.write(f"اسم ملف الإخراج: {os.path.basename(output_file)}\n")
                out_file.write("=" * 80 + "\n\n")
                
                files_processed = 0
                files_skipped = 0
                model_files_count = 0
                ignored_folders = set()
                ignored_venv_files = []
                binary_files = []
                rar_read_errors = 0
                
                for file_name in sorted(file_list):
                    if file_name.endswith('/'):
                        continue
                    
                    if should_ignore_file(file_name):
                        files_skipped += 1
                        if '/venv/' in file_name or file_name.startswith('venv/'):
                            ignored_venv_files.append(file_name)
                            ignored_folders.add('venv')
                            reason = "مجلد venv/"
                        else:
                            folder = '/'.join(file_name.split('/')[:-1])
                            reason = "مجلد مخفي أو __pycache__"
                            for part in folder.split('/'):
                                if part.startswith('.') and part != '.' and part != '..':
                                    reason = f"مجلد مخفي: {part}"
                                    ignored_folders.add(part)
                                    break
                                if part == '__pycache__':
                                    reason = "مجلد __pycache__"
                                    ignored_folders.add('__pycache__')
                                    break
                        ignored_files.append((file_name, reason))
                        print(f"    ⚠️ تجاهل ({reason}): {file_name}")
                        continue
                    
                    file_ext = pathlib.Path(file_name).suffix.lower()
                    
                    if file_ext in BINARY_EXTENSIONS:
                        binary_files.append(file_name)
                        files_skipped += 1
                        reason = f"امتداد ثنائي {file_ext}"
                        ignored_files.append((file_name, reason))
                        print(f"    ⚠️ تجاهل ({reason}): {file_name}")
                        continue
                    
                    try:
                        if archive_type == "zip":
                            with archive.open(file_name, 'r') as file_in_archive:
                                content_bytes = file_in_archive.read()
                        elif archive_type == "rar":
                            try:
                                with archive.open(file_name, 'r') as file_in_archive:
                                    content_bytes = file_in_archive.read()
                            except Exception as e:
                                rar_read_errors += 1
                                files_skipped += 1
                                reason = f"خطأ في قراءة RAR: {str(e)}"
                                ignored_files.append((file_name, reason))
                                print(f"    ⚠️ تجاهل ({reason}): {file_name}")
                                if rar_read_errors == 4:
                                    print(f"    ℹ️  ... وأخطاء أخرى في قراءة ملفات RAR")
                                continue
                        
                        if len(content_bytes) == 0:
                            files_skipped += 1
                            reason = "ملف فارغ"
                            ignored_files.append((file_name, reason))
                            print(f"    ⚠️ تجاهل ({reason}): {file_name}")
                            continue
                        
                        is_model = is_model_file(file_name)
                        
                        content, file_type = process_file_content(file_name, content_bytes, is_model)
                        
                        if file_type != "Text" and file_type != "Model File":
                            binary_files.append(f"{file_name} ({file_type})")
                            files_skipped += 1
                            reason = f"نوع الملف: {file_type}"
                            ignored_files.append((file_name, reason))
                            print(f"    ⚠️ تجاهل ({reason}): {file_name}")
                            continue
                        
                        out_file.write(f"اسم الملف: {file_name}\n")
                        out_file.write("-" * 40 + "\n")
                        
                        if is_model:
                            model_files_count += 1
                            out_file.write(content)
                        elif content:
                            out_file.write(content)
                        
                        if content and not content.endswith('\n'):
                            out_file.write('\n')
                        
                        out_file.write("\n" + "=" * 80 + "\n\n")
                        files_processed += 1
                        
                    except Exception as e:
                        print(f"    ⚠️ خطأ في معالجة {file_name}: {str(e)}")
                        files_skipped += 1
                        reason = f"خطأ في المعالجة: {str(e)}"
                        ignored_files.append((file_name, reason))
                        print(f"    ⚠️ تجاهل ({reason}): {file_name}")
                        continue
                
                # كتابة الملخص
                out_file.write("\n" + "=" * 80 + "\n")
                out_file.write("ملخص المعالجة:\n")
                out_file.write(f"- عدد الملفات النصية المعالجة: {files_processed}\n")
                out_file.write(f"- عدد الملفات المتجاهلة: {files_skipped}\n")
                out_file.write(f"- عدد ملفات models (تم تسجيل الأسماء فقط): {model_files_count}\n")
                out_file.write(f"- إجمالي الملفات في الأرشيف: {len(file_list)}\n")
                
                if archive_type == "rar" and rar_read_errors > 0:
                    out_file.write(f"- أخطاء قراءة ملفات RAR: {rar_read_errors}\n")
                    if not use_unrar:
                        out_file.write("  (لتحسين قراءة ملفات RAR، قم بتثبيت WinRAR أو 7-Zip)\n")
                
                if ignored_folders:
                    out_file.write(f"- المجلدات/الأنواع المتجاهلة: {', '.join(sorted(ignored_folders))}\n")
                
                if ignored_venv_files:
                    out_file.write(f"- عدد الملفات في مجلدات venv/ المتجاهلة: {len(ignored_venv_files)}\n")
                
                if binary_files:
                    out_file.write(f"- عدد الملفات الثنائية المتجاهلة: {len(binary_files)}\n")
                
                if model_files_count > 0:
                    out_file.write(f"ℹ️  ملاحظة: تم تسجيل أسماء فقط لـ {model_files_count} ملف في مجلدات models/\n")
                    out_file.write("   ولم يتم استخراج محتواها لتجنب الملفات الكبيرة.\n")
                
                # كتابة قائمة الملفات المتجاهلة
                out_file.write("\n" + "=" * 80 + "\n")
                out_file.write("الملفات المتجاهلة (مع سبب التجاهل):\n")
                out_file.write("=" * 80 + "\n")
                if ignored_files:
                    for fname, reason in sorted(ignored_files):
                        out_file.write(f"- {fname} : {reason}\n")
                else:
                    out_file.write("لم يتم تجاهل أي ملف.\n")
                
                out_file.write("=" * 80 + "\n")
        
        print(f"  ✓ تم استخراج محتويات {archive_type.upper()} إلى: {output_file}")
        print(f"  ✓ تمت معالجة {files_processed} ملفًا نصيًا")
        print(f"  ✓ تم تسجيل أسماء {model_files_count} ملف في مجلدات models/")
        print(f"  ✓ تم تجاهل {files_skipped} ملفًا")
        print(f"  ✓ تم تسجيل أسماء الملفات المتجاهلة في الملف الناتج وطباعتها على الشاشة.")
        
        if archive_type == "rar" and rar_read_errors > 0:
            print(f"  ⚠️  كانت هناك {rar_read_errors} أخطاء في قراءة ملفات RAR")
            if not use_unrar:
                print(f"  💡 للحصول على نتائج أفضل، قم بتثبيت WinRAR أو 7-Zip")
        
        return output_file, files_processed, files_skipped, ignored_files
        
    except Exception as e:
        print(f"  ❌ حدث خطأ في معالجة {archive_path}: {str(e)}")
        return None, 0, 0, []

def extract_folder_to_text(folder_path, output_file):
    if not os.path.exists(folder_path):
        print(f"المجلد {folder_path} غير موجود!")
        return None, 0, 0, []
    if not os.path.isdir(folder_path):
        print(f"{folder_path} ليس مجلدًا صالحًا!")
        return None, 0, 0, []
    
    ignored_files = []
    
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            out_file.write("=" * 80 + "\n")
            out_file.write(f"محتوى المجلد: {os.path.basename(folder_path)}\n")
            out_file.write(f"تاريخ الإنشاء: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out_file.write(f"اسم ملف الإخراج: {os.path.basename(output_file)}\n")
            out_file.write("=" * 80 + "\n\n")
            
            files_processed = 0
            files_skipped = 0
            model_files_count = 0
            ignored_folders = set()
            ignored_venv_files = []
            binary_files = []
            total_files_count = 0
            
            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                dirs[:] = [d for d in dirs if d != '__pycache__']
                dirs[:] = [d for d in dirs if d != 'venv']
                
                for file in files:
                    total_files_count += 1
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, folder_path)
                    rel_path_unix = rel_path.replace('\\', '/')
                    
                    if should_ignore_file(rel_path_unix):
                        files_skipped += 1
                        if '/venv/' in rel_path_unix or rel_path_unix.startswith('venv/'):
                            ignored_venv_files.append(rel_path_unix)
                            ignored_folders.add('venv')
                            reason = "مجلد venv/"
                        else:
                            folder = '/'.join(rel_path_unix.split('/')[:-1])
                            reason = "مجلد مخفي أو __pycache__"
                            for part in folder.split('/'):
                                if part.startswith('.') and part != '.' and part != '..':
                                    reason = f"مجلد مخفي: {part}"
                                    ignored_folders.add(part)
                                    break
                                if part == '__pycache__':
                                    reason = "مجلد __pycache__"
                                    ignored_folders.add('__pycache__')
                                    break
                        ignored_files.append((rel_path_unix, reason))
                        print(f"  ⚠️ تجاهل ({reason}): {rel_path_unix}")
                        continue
                    
                    file_ext = pathlib.Path(file).suffix.lower()
                    
                    if file_ext in BINARY_EXTENSIONS:
                        binary_files.append(rel_path_unix)
                        files_skipped += 1
                        reason = f"امتداد ثنائي {file_ext}"
                        ignored_files.append((rel_path_unix, reason))
                        print(f"  ⚠️ تجاهل ({reason}): {rel_path_unix}")
                        continue
                    
                    try:
                        with open(file_path, 'rb') as f:
                            content_bytes = f.read()
                        
                        if len(content_bytes) == 0:
                            files_skipped += 1
                            reason = "ملف فارغ"
                            ignored_files.append((rel_path_unix, reason))
                            print(f"  ⚠️ تجاهل ({reason}): {rel_path_unix}")
                            continue
                        
                        is_model = is_model_file(rel_path_unix)
                        
                        content, file_type = process_file_content(rel_path_unix, content_bytes, is_model)
                        
                        if file_type != "Text" and file_type != "Model File":
                            binary_files.append(f"{rel_path_unix} ({file_type})")
                            files_skipped += 1
                            reason = f"نوع الملف: {file_type}"
                            ignored_files.append((rel_path_unix, reason))
                            print(f"  ⚠️ تجاهل ({reason}): {rel_path_unix}")
                            continue
                        
                        out_file.write(f"اسم الملف: {rel_path_unix}\n")
                        out_file.write("-" * 40 + "\n")
                        
                        if is_model:
                            model_files_count += 1
                            out_file.write(content)
                        elif content:
                            out_file.write(content)
                        
                        if content and not content.endswith('\n'):
                            out_file.write('\n')
                        
                        out_file.write("\n" + "=" * 80 + "\n\n")
                        files_processed += 1
                        
                    except Exception as e:
                        print(f"  ⚠️ خطأ في معالجة {rel_path_unix}: {str(e)}")
                        files_skipped += 1
                        reason = f"خطأ في المعالجة: {str(e)}"
                        ignored_files.append((rel_path_unix, reason))
                        print(f"  ⚠️ تجاهل ({reason}): {rel_path_unix}")
                        continue
            
            # كتابة الملخص
            out_file.write("\n" + "=" * 80 + "\n")
            out_file.write("ملخص المعالجة:\n")
            out_file.write(f"- عدد الملفات النصية المعالجة: {files_processed}\n")
            out_file.write(f"- عدد الملفات المتجاهلة: {files_skipped}\n")
            out_file.write(f"- عدد ملفات models (تم تسجيل الأسماء فقط): {model_files_count}\n")
            out_file.write(f"- إجمالي الملفات المفحوصة: {total_files_count}\n")
            
            if ignored_folders:
                out_file.write(f"- المجلدات/الأنواع المتجاهلة: {', '.join(sorted(ignored_folders))}\n")
            
            if ignored_venv_files:
                out_file.write(f"- عدد الملفات في مجلدات venv/ المتجاهلة: {len(ignored_venv_files)}\n")
            
            if binary_files:
                out_file.write(f"- عدد الملفات الثنائية المتجاهلة: {len(binary_files)}\n")
            
            if model_files_count > 0:
                out_file.write(f"ℹ️  ملاحظة: تم تسجيل أسماء فقط لـ {model_files_count} ملف في مجلدات models/\n")
                out_file.write("   ولم يتم استخراج محتواها لتجنب الملفات الكبيرة.\n")
            
            # كتابة قائمة الملفات المتجاهلة
            out_file.write("\n" + "=" * 80 + "\n")
            out_file.write("الملفات المتجاهلة (مع سبب التجاهل):\n")
            out_file.write("=" * 80 + "\n")
            if ignored_files:
                for fname, reason in sorted(ignored_files):
                    out_file.write(f"- {fname} : {reason}\n")
            else:
                out_file.write("لم يتم تجاهل أي ملف.\n")
            
            out_file.write("=" * 80 + "\n")
        
        print(f"  ✓ تم استخراج محتويات المجلد إلى: {output_file}")
        print(f"  ✓ تمت معالجة {files_processed} ملفًا نصيًا")
        print(f"  ✓ تم تسجيل أسماء {model_files_count} ملف في مجلدات models/")
        print(f"  ✓ تم تجاهل {files_skipped} ملفًا")
        print(f"  ✓ تم تسجيل أسماء الملفات المتجاهلة في الملف الناتج وطباعتها على الشاشة.")
        
        return output_file, files_processed, files_skipped, ignored_files
        
    except Exception as e:
        print(f"❌ حدث خطأ في معالجة {folder_path}: {str(e)}")
        return None, 0, 0, []

def find_archives_in_folder(folder_path):
    archives = []
    archive_extensions = ['.zip']
    if RAR_SUPPORT:
        archive_extensions.append('.rar')
    
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            file_ext = pathlib.Path(file).suffix.lower()
            if is_split_archive_extension(file_ext):
                continue
            if file_ext in archive_extensions:
                archive_path = os.path.join(root, file)
                archives.append(archive_path)
    return archives

def process_single_item(item_path):
    results = []
    # المجلد الذي سيتم وضع المخرجات فيه (بجانب العنصر)
    output_dir = os.path.dirname(item_path)
    if not output_dir:  # إذا كان العنصر في الجذر
        output_dir = '/'
    
    if os.path.isfile(item_path):
        file_ext = pathlib.Path(item_path).suffix.lower()
        
        if is_split_archive_extension(file_ext):
            print(f"\n🔍 ملف جزء من أرشيف متعدد: {os.path.basename(item_path)}")
            print(f"   ⚠️  هذا الملف جزء من أرشيف مضغوط متعدد الأجزاء. سيتم تجاهله.")
            return results
        
        if zipfile.is_zipfile(item_path):
            print(f"\n📦 معالجة ملف ZIP: {os.path.basename(item_path)}")
            base_name = os.path.splitext(os.path.basename(item_path))[0]
            output_file = get_unique_filename(output_dir, base_name + "_zip_contents", ".txt")
            result = extract_archive_to_text(item_path, output_file, "zip")
            if result[0]:
                results.append((result[0], result[1], result[2]))
        
        elif RAR_SUPPORT and rarfile and rarfile.is_rarfile(item_path):
            print(f"\n📦 معالجة ملف RAR: {os.path.basename(item_path)}")
            base_name = os.path.splitext(os.path.basename(item_path))[0]
            output_file = get_unique_filename(output_dir, base_name + "_rar_contents", ".txt")
            result = extract_archive_to_text(item_path, output_file, "rar")
            if result[0]:
                results.append((result[0], result[1], result[2]))
        
        else:
            # ملف عادي
            if file_ext in TEXT_EXTENSIONS or file_ext not in BINARY_EXTENSIONS:
                print(f"\n📄 معالجة ملف: {os.path.basename(item_path)}")
                base_name = os.path.splitext(os.path.basename(item_path))[0]
                output_file = get_unique_filename(output_dir, base_name + "_file_contents", ".txt")
                result = extract_single_file_to_text(item_path, output_file)
                if result[0]:
                    results.append((result[0], result[1], result[2]))
                elif result[3]:
                    # تم تخطيه، وقد طبعنا بالفعل الرسالة داخل الدالة
                    pass
            else:
                print(f"\n❌ نوع الملف غير مدعوم أو ثنائي: {os.path.basename(item_path)}")
                print(f"   يجب أن يكون ملف نصي (مثل .txt, .py, .md) أو ملف ZIP/RAR أو مجلد.")
    
    elif os.path.isdir(item_path):
        print(f"\n🔍 معالجة المجلد: {os.path.basename(item_path)}")
        # للمجلد، نضع الملف الناتج في نفس المجلد الأصلي (بجانب المجلد)
        base_name = os.path.basename(item_path)  # اسم المجلد
        output_file = get_unique_filename(output_dir, base_name + "_folder_contents", ".txt")
        result = extract_folder_to_text(item_path, output_file)
        if result[0]:
            results.append((result[0], result[1], result[2]))
        
        archives = find_archives_in_folder(item_path)
        if archives:
            print(f"  📦 وجد {len(archives)} ملفًا مضغوطًا داخل المجلد:")
            for archive_path in archives:
                archive_name = os.path.basename(archive_path)
                rel_path = os.path.relpath(archive_path, item_path)
                print(f"    - {rel_path}")
                
                if archive_path.lower().endswith('.zip'):
                    base_name = os.path.splitext(archive_name)[0]
                    output_file = get_unique_filename(output_dir, base_name + "_zip_contents", ".txt")
                    result = extract_archive_to_text(archive_path, output_file, "zip")
                elif archive_path.lower().endswith('.rar') and RAR_SUPPORT:
                    base_name = os.path.splitext(archive_name)[0]
                    output_file = get_unique_filename(output_dir, base_name + "_rar_contents", ".txt")
                    result = extract_archive_to_text(archive_path, output_file, "rar")
                else:
                    continue
                
                if result[0]:
                    results.append((result[0], result[1], result[2]))
    
    else:
        print(f"\n❌ المسار غير موجود: {item_path}")
    
    return results

def main():
    print("🔍 فحص المكتبات المثبتة:")
    print(f"   ✓ zipfile: مثبت (دعم ملفات ZIP)")
    
    if RAR_SUPPORT:
        print(f"   ✓ rarfile: مثبت (دعم ملفات RAR)")
        unrar_found = False
        for tool in ['unrar', '7z']:
            try:
                subprocess.run([tool, '--version'], capture_output=True, timeout=2)
                print(f"   ✓ {tool}: مثبت في النظام")
                unrar_found = True
            except:
                continue
        if not unrar_found and sys.platform == "win32":
            for path in ['C:\\Program Files\\WinRAR\\UnRAR.exe', 
                        'C:\\Program Files\\7-Zip\\7z.exe']:
                if os.path.exists(path):
                    print(f"   ✓ {os.path.basename(path)}: مثبت")
                    unrar_found = True
        if not unrar_found:
            print(f"   ⚠️  unrar/7z: غير مثبت (مطلوب لملفات RAR المعقدة)")
            print(f"   ℹ️  سيتم استخدام الموزع المدمج في rarfile")
            print(f"   💡 للحصول على نتائج أفضل، قم بتثبيت WinRAR أو 7-Zip")
    else:
        print(f"   ❌ rarfile: غير مثبت (لا دعم لملفات RAR)")
        print(f"   ℹ️  قم بتثبيتها باستخدام: pip install rarfile")
    
    print()
    
    if len(sys.argv) < 2:
        print("استخراج محتويات ملفات ZIP أو RAR أو مجلدات أو ملفات نصية إلى ملفات نصية")
        print("=" * 60)
        print("الاستخدام:")
        print("1. اسحب عدة ملفات ZIP/RAR أو مجلدات أو ملفات نصية وأفلتها فوق هذا السكريبت")
        print("2. أو استخدم: python script.py ملف1.txt ملف2.py مجلد1 ملف.zip ...")
        print("\nملاحظات:")
        print("- يمكنك سحب وإفلات عدة ملفات ومجلدات في نفس الوقت")
        print("- إذا كان المجلد يحتوي على ملفات مضغوطة، سيتم معالجتها أيضًا")
        print("- سيتم تجاهل جميع المجلدات التي تبدأ بنقطة (مثل .venv, .git)")
        print("- سيتم تجاهل مجلدات __pycache__ وملفات .pyc")
        print("- سيتم تجاهل مجلدات venv/ (بدون نقطة في البداية)")
        print("- سيتم تجاهل الملفات الثنائية (صور، تنفيذيات، إلخ)")
        print("- سيتم تجاهل ملفات الأرشيف المتعددة الأجزاء (مثل .z01, .z02, .r00, .part1.rar)")
        print("- يتم استخراج الملفات النصية فقط")
        print("- سيتم إنشاء ملف نصي منفصل لكل ملف/مجلد معالج")
        print("\n📌 خاصية جديدة: ملفات مجلدات models/")
        print("- سيتم تسجيل أسماء الملفات في مجلدات models/ فقط")
        print("- لن يتم استخراج محتويات هذه الملفات (لتجنب الملفات الكبيرة)")
        print("\n📌 خاصية الملفات المتجاهلة:")
        print("- سيتم طباعة أسماء الملفات المتجاهلة على الشاشة فورًا مع سبب التجاهل.")
        print("- كما يتم تسجيلها في ملف الإخراج النهائي.")
        print("\nملاحظات حول ملفات RAR:")
        print("- إذا كان unrar أو 7-Zip مثبتًا، سيتم استخدامه لتحسين النتائج")
        print("- على Windows، قد يحاول البرنامج تثبيت unrar تلقائيًا")
        print("\nاضغط Enter للخروج...")
        input()
        return
    
    total_items = len(sys.argv) - 1
    all_results = []
    
    print(f"🎯 تم سحب {total_items} عنصرًا للمعالجة:")
    for i, item_path in enumerate(sys.argv[1:], 1):
        print(f"\n[{i}/{total_items}] معالجة: {item_path}")
        results = process_single_item(item_path)
        all_results.extend(results)
    
    print("\n" + "=" * 60)
    print("📊 ملخص المعالجة النهائي:")
    print("=" * 60)
    
    total_files_processed = sum(r[1] for r in all_results if r)
    total_files_skipped = sum(r[2] for r in all_results if r)
    total_output_files = len(all_results)
    
    print(f"📁 عدد الملفات النصية المنشأة: {total_output_files}")
    print(f"📄 إجمالي الملفات النصية المعالجة: {total_files_processed:,}")
    print(f"🚫 إجمالي الملفات المتجاهلة: {total_files_skipped:,}")
    
    if all_results:
        print(f"\n📋 قائمة الملفات الناتجة:")
        for i, (output_file, processed, skipped) in enumerate(all_results, 1):
            if output_file and os.path.exists(output_file):
                try:
                    file_size = os.path.getsize(output_file)
                    size_str = f"{file_size:,} بايت"
                    if file_size > 1024*1024*1024:
                        size_str = f"{file_size/(1024*1024*1024):.1f} GB"
                    elif file_size > 1024*1024:
                        size_str = f"{file_size/(1024*1024):.1f} MB"
                    elif file_size > 1024:
                        size_str = f"{file_size/1024:.1f} KB"
                    print(f"  {i:2d}. {os.path.basename(output_file)} ({size_str}) - {processed:,} ملفًا معالجًا، {skipped:,} متجاهل")
                except:
                    print(f"  {i:2d}. {os.path.basename(output_file)} - {processed:,} ملفًا معالجًا، {skipped:,} متجاهل")
    
    print("\n✅ اكتملت المعالجة!")
    print("📅 التاريخ: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if RAR_SUPPORT:
        rar_files = [r for r in all_results if r[0] and '_rar_contents' in r[0]]
        if rar_files:
            print("\n💡 نصائح لتحسين نتائج ملفات RAR:")
            print("- قم بتثبيت WinRAR من: https://www.win-rar.com/")
            print("- أو قم بتثبيت 7-Zip من: https://www.7-zip.org/")
            print("- بعد التثبيت، أعد تشغيل السكريبت للحصول على نتائج أفضل")
    
    print("\n📌 ملاحظة: ملفات مجلدات models/")
    print("- تم تسجيل أسماء الملفات في مجلدات models/ فقط")
    print("- لم يتم استخراج محتويات هذه الملفات (لتجنب الملفات الكبيرة)")
    print("\n📌 الملفات المتجاهلة:")
    print("- تم طباعة جميع الملفات المتجاهلة على الشاشة أثناء المعالجة.")
    print("- كما يمكنك الاطلاع على القائمة الكاملة داخل كل ملف ناتج.")
    
    print("\nاضغط Enter للخروج...")
    input()

if __name__ == "__main__":
    main()