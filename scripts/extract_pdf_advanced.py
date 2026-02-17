#!/usr/bin/env bash
# extract_pdf_advanced - استخراج متقدم من PDF (نصوص، صور، جداول) مع OCR
# يعتمد على بيئة conda medical-ai

PDF_FILE="$1"
if [ ! -f "$PDF_FILE" ]; then
    echo "❌ الملف غير موجود: $PDF_FILE"
    exit 1
fi

# تحديد المسارات
PDF_DIR=$(dirname "$PDF_FILE")
PDF_BASENAME=$(basename "$PDF_FILE")
PDF_NAME_NO_EXT="${PDF_BASENAME%.*}"
OUTPUT_DIR="${PDF_DIR}/${PDF_NAME_NO_EXT}_pdf_extracted"
IMAGES_DIR="${OUTPUT_DIR}/images"
TABLES_DIR="${OUTPUT_DIR}/tables"

# إنشاء المجلدات المطلوبة
mkdir -p "$OUTPUT_DIR" "$IMAGES_DIR" "$TABLES_DIR"

echo "📄 معالجة ملف PDF: $PDF_BASENAME"
echo "📁 مجلد الإخراج: $(basename "$OUTPUT_DIR")"

# تفعيل بيئة conda (افتراضياً هي مفعلة، لكن نضمن استخدام بايثون الصحيح)
CONDA_PYTHON="/home/xorthomson/miniconda3/envs/medical-ai/bin/python"

# إنشاء سكريبت بايثون مؤقت للقيام بالمهام المعقدة
PYTHON_SCRIPT=$(mktemp)

cat > "$PYTHON_SCRIPT" << 'EOF'
import sys
import os
import json
from pathlib import Path

# استيراد المكتبات المطلوبة
try:
    import pdfplumber
    from PIL import Image
    import pytesseract
    import pandas as pd
    from tabulate import tabulate
except ImportError as e:
    print(f"❌ مكتبة مفقودة: {e}")
    print("الرجاء تثبيتها في بيئة medical-ai: pip install pdfplumber pytesseract pillow pandas tabulate")
    sys.exit(1)

def extract_images_from_page(page, page_num, images_dir, base_name):
    """استخراج الصور من الصفحة وحفظها مع بيانات وصفية"""
    images = page.images
    image_files = []
    for i, img in enumerate(images):
        try:
            # استخراج الصورة باستخدام pdfplumber (قد لا يعمل دائماً)
            # بديل: استخدام pdfimages خارجياً (سنفعله لاحقاً في Bash)
            # سنقوم فقط بتسجيل معلومات الصورة
            x0, top, x1, bottom = img['x0'], img['top'], img['x1'], img['bottom']
            width = x1 - x0
            height = bottom - top
            alt_text = img.get('alt', '')  # التسمية التوضيحية إن وجدت
            # حفظ معلومات الصورة في ملف JSON
            img_info = {
                'page': page_num,
                'index': i,
                'bbox': [x0, top, x1, bottom],
                'width': width,
                'height': height,
                'alt_text': alt_text
            }
            img_filename = f"{base_name}_page{page_num:04d}_img{i:02d}.json"
            img_path = os.path.join(images_dir, img_filename)
            with open(img_path, 'w', encoding='utf-8') as f:
                json.dump(img_info, f, indent=2)
            image_files.append(img_path)
        except Exception as e:
            print(f"⚠️ خطأ في استخراج معلومات الصورة في صفحة {page_num}: {e}")
    return image_files

def extract_tables_from_page(page, page_num, tables_dir):
    """استخراج الجداول من الصفحة وحفظها كـ CSV و Markdown"""
    tables = page.extract_tables()
    table_files = []
    for i, table in enumerate(tables):
        if not table or all(not any(row) for row in table):
            continue
        # تحويل إلى DataFrame
        df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
        # حفظ كـ CSV
        csv_filename = f"table_page{page_num:04d}_{i:02d}.csv"
        csv_path = os.path.join(tables_dir, csv_filename)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        # حفظ كـ Markdown
        md_filename = f"table_page{page_num:04d}_{i:02d}.md"
        md_path = os.path.join(tables_dir, md_filename)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(tabulate(df, headers='keys', tablefmt='pipe', showindex=False))
        table_files.append((csv_path, md_path))
    return table_files

def main(pdf_path, output_dir, images_dir, tables_dir):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    full_text_path = os.path.join(output_dir, 'full_text.txt')
    summary_path = os.path.join(output_dir, 'summary.txt')

    total_pages = 0
    total_images = 0
    total_tables = 0
    pages_with_ocr = 0

    with open(full_text_path, 'w', encoding='utf-8') as txt_out:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, 1):
                txt_out.write(f"\n{'='*80}\n")
                txt_out.write(f"الصفحة {page_num}\n")
                txt_out.write(f"{'='*80}\n\n")

                # استخراج النص
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    txt_out.write(page_text)
                    txt_out.write("\n\n")
                else:
                    # الصفحة قد تكون صورة - نستخدم OCR
                    print(f"🖼️ الصفحة {page_num} تحتوي على صور - تشغيل OCR...")
                    # تحويل الصفحة إلى صورة
                    im = page.to_image(resolution=300)
                    img_path = os.path.join(images_dir, f"page_{page_num:04d}.png")
                    im.save(img_path, format="PNG")
                    # تشغيل Tesseract
                    ocr_text = pytesseract.image_to_string(Image.open(img_path), lang='ara+eng')
                    txt_out.write(ocr_text)
                    txt_out.write("\n\n")
                    pages_with_ocr += 1
                    total_images += 1  # عد الصفحة كصورة

                # استخراج الصور المضمنة (إن وجدت)
                img_files = extract_images_from_page(page, page_num, images_dir, base_name)
                total_images += len(img_files)

                # استخراج الجداول
                table_files = extract_tables_from_page(page, page_num, tables_dir)
                total_tables += len(table_files)
                if table_files:
                    txt_out.write("\n[جداول مستخرجة موجودة في مجلد tables]\n")

    # كتابة الملخص
    with open(summary_path, 'w', encoding='utf-8') as summ:
        summ.write(f"ملخص استخراج PDF: {os.path.basename(pdf_path)}\n")
        summ.write(f"إجمالي الصفحات: {total_pages}\n")
        summ.write(f"صفحات تم استخدام OCR فيها: {pages_with_ocr}\n")
        summ.write(f"إجمالي الصور المستخرجة: {total_images}\n")
        summ.write(f"إجمالي الجداول المستخرجة: {total_tables}\n")
        summ.write(f"\nالمخرجات موجودة في:\n")
        summ.write(f"  - النص الكامل: {os.path.basename(full_text_path)}\n")
        summ.write(f"  - الصور: images/\n")
        summ.write(f"  - الجداول: tables/\n")

    print(f"\n✅ تم الانتهاء بنجاح!")
    print(f"📄 النص الكامل: {os.path.basename(full_text_path)}")
    print(f"🖼️ الصور: {total_images} صورة (في images/)")
    print(f"📊 الجداول: {total_tables} جدول (في tables/)")
    print(f"📝 التقرير: {os.path.basename(summary_path)}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: script.py <pdf_path> <output_dir> <images_dir> <tables_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
EOF

# تشغيل سكريبت بايثون داخل بيئة conda
"$CONDA_PYTHON" "$PYTHON_SCRIPT" "$PDF_FILE" "$OUTPUT_DIR" "$IMAGES_DIR" "$TABLES_DIR"

# حذف السكريبت المؤقت
rm "$PYTHON_SCRIPT"

# بعد ذلك، نقوم باستخراج الصور الفعلية باستخدام pdfimages (أفضل)
if command -v pdfimages &> /dev/null; then
    echo "🖼️ استخراج الصور الفعلية باستخدام pdfimages..."
    pdfimages -all "$PDF_FILE" "$IMAGES_DIR/image"
    # إعادة تسمية الصور بأسماء ذات معنى
    cd "$IMAGES_DIR"
    for f in image-*; do
        if [ -f "$f" ]; then
            mv "$f" "embedded_$f"
        fi
    done
    cd - > /dev/null
else
    echo "⚠️ pdfimages غير مثبت. لتثبيته: sudo pacman -S poppler"
fi

# محاولة استخراج التسميات التوضيحية من البيانات الوصفية للصور (إذا كانت موجودة)
if command -v exiftool &> /dev/null; then
    echo "🏷️ استخراج التسميات التوضيحية للصور..."
    exiftool -Description -ImageDescription -XMP:Description -XMP:Title -csv "$IMAGES_DIR" > "$IMAGES_DIR/image_metadata.csv"
else
    echo "⚠️ exiftool غير مثبت. لتثبيته: sudo pacman -S exiftool"
fi

echo ""
echo "✅ اكتملت معالجة PDF. المخرجات في: $OUTPUT_DIR"
