
import os
import platform

import fitz
from django.conf import settings
from pdf2image import convert_from_path
from PIL import Image


WATERMARK_TEXT = "PREVIEW ONLY - BUY TO DOWNLOAD"
MAX_PREVIEW_PAGES = 15

# บน Windows ใช้ path ที่ระบุ, บน Linux/PythonAnywhere ใช้ที่อยู่ใน PATH อยู่แล้ว
POPPLER_PATH = r"./media/app/media" if platform.system() == "Windows" else None


def _poppler_kwargs():
    if POPPLER_PATH:
        return {"poppler_path": POPPLER_PATH}
    return {}


def _source_signature(path):
    stat = os.stat(path)
    return f"{os.path.abspath(path)}|{stat.st_mtime_ns}|{stat.st_size}"


def _reset_cache_if_source_changed(output_dir, source_path, prefix, extension):
    os.makedirs(output_dir, exist_ok=True)
    marker_name = prefix.strip("_").replace(os.sep, "_") or "preview"
    marker_path = os.path.join(output_dir, f".{marker_name}.source_signature")
    signature = _source_signature(source_path)

    try:
        with open(marker_path, "r", encoding="utf-8") as marker:
            if marker.read() == signature:
                return
    except FileNotFoundError:
        pass

    for filename in os.listdir(output_dir):
        if filename.startswith(prefix) and filename.endswith(extension):
            os.remove(os.path.join(output_dir, filename))

    with open(marker_path, "w", encoding="utf-8") as marker:
        marker.write(signature)


def pdf_to_images(pdf_path, output_dir, max_pages=MAX_PREVIEW_PAGES):
    _reset_cache_if_source_changed(output_dir, pdf_path, "page_", ".png")

    image_paths = []
    for i in range(1, max_pages + 1):
        path = os.path.join(output_dir, f"page_{i}.png")

        if os.path.exists(path):
            image_paths.append(path)
            continue

        try:
            pages = convert_from_path(
                pdf_path,
                dpi=150,
                first_page=i,
                last_page=i,
                **_poppler_kwargs(),
            )
            if not pages:
                break
            pages[0].save(path, "PNG")
            image_paths.append(path)
        except Exception as exc:
            print(f"Preview page conversion failed for page {i}: {exc}")
            break

    return image_paths


def create_preview(document):
    """สร้าง PDF preview แบบมี watermark จากไม่กี่หน้าแรกของเอกสาร"""
    input_path = document.file.path
    preview_path = os.path.join(
        settings.MEDIA_ROOT,
        "previews",
        f"preview_{document.id}.pdf",
    )
    marker_path = preview_path + ".source_signature"
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)

    signature = _source_signature(input_path)
    try:
        with open(marker_path, "r", encoding="utf-8") as marker:
            if os.path.exists(preview_path) and marker.read() == signature:
                return preview_path
    except FileNotFoundError:
        pass

    if os.path.exists(preview_path):
        os.remove(preview_path)

    doc = fitz.open(input_path)
    preview_doc = fitz.open()
    pages_to_keep = min(5, len(doc))

    for i in range(pages_to_keep):
        preview_doc.insert_pdf(doc, from_page=i, to_page=i)

    preview_doc.save(preview_path)
    preview_doc.close()
    doc.close()

    add_watermark(preview_path)

    with open(marker_path, "w", encoding="utf-8") as marker:
        marker.write(signature)

    return preview_path


def add_watermark(pdf_path):
    """ใส่ watermark ที่มองเห็นได้ในทุกหน้าของ PDF preview"""
    doc = fitz.open(pdf_path)

    for page in doc:
        rect = page.rect
        page.insert_text(
            (rect.width / 2 - 150, rect.height / 2),
            WATERMARK_TEXT,
            fontsize=36,
            rotate=45,
            color=(0.6, 0.6, 0.6),
            overlay=True,
        )

    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()


def create_preview_images(document, max_pages=MAX_PREVIEW_PAGES):
    """สร้างรูปภาพ JPG preview จาก PDF ของเอกสาร"""
    input_path = document.file.path
    output_dir = os.path.join(settings.MEDIA_ROOT, "preview_images")
    _reset_cache_if_source_changed(output_dir, input_path, f"preview_{document.id}_page_", ".jpg")

    preview_images = []
    for i in range(1, max_pages + 1):
        img_filename = f"preview_{document.id}_page_{i}.jpg"
        img_path = os.path.join(output_dir, img_filename)

        if os.path.exists(img_path):
            preview_images.append(img_path)
            continue

        try:
            pages = convert_from_path(
                input_path,
                dpi=150,
                first_page=i,
                last_page=i,
                **_poppler_kwargs(),
            )
            if not pages:
                break

            img = pages[0]
            img.thumbnail((800, 1200), Image.Resampling.LANCZOS)
            img.save(img_path, "JPEG", quality=85)
            preview_images.append(img_path)
        except Exception as exc:
            print(f"Preview image creation failed for page {i}: {exc}")
            break

    return preview_images


# import os
# import platform

# import fitz
# from django.conf import settings
# from pdf2image import convert_from_path
# from PIL import Image


# WATERMARK_TEXT = "PREVIEW ONLY - BUY TO DOWNLOAD"
# MAX_PREVIEW_PAGES = 15

# # Use poppler path only on Windows (local dev); Linux/PythonAnywhere has it in PATH
# POPPLER_PATH = r"C:\poppler\Library\bin" if platform.system() == "Windows" else None


# def _poppler_kwargs():
#     """Return poppler_path kwarg only when needed (Windows dev)."""
#     if POPPLER_PATH:
#         return {"poppler_path": POPPLER_PATH}
#     return {}


# def _source_signature(path):
#     stat = os.stat(path)
#     return f"{os.path.abspath(path)}|{stat.st_mtime_ns}|{stat.st_size}"


# def _reset_cache_if_source_changed(output_dir, source_path, prefix, extension):
#     os.makedirs(output_dir, exist_ok=True)
#     marker_name = prefix.strip("_").replace(os.sep, "_") or "preview"
#     marker_path = os.path.join(output_dir, f".{marker_name}.source_signature")
#     signature = _source_signature(source_path)

#     try:
#         with open(marker_path, "r", encoding="utf-8") as marker:
#             if marker.read() == signature:
#                 return
#     except FileNotFoundError:
#         pass

#     for filename in os.listdir(output_dir):
#         if filename.startswith(prefix) and filename.endswith(extension):
#             os.remove(os.path.join(output_dir, filename))

#     with open(marker_path, "w", encoding="utf-8") as marker:
#         marker.write(signature)
        
        
# def pdf_to_images(pdf_path, output_dir, max_pages=MAX_PREVIEW_PAGES):
#     _reset_cache_if_source_changed(output_dir, pdf_path, "page_", ".png")

#     image_paths = []
#     for i in range(1, max_pages + 1):
#         path = os.path.join(output_dir, f"page_{i}.png")

#         if os.path.exists(path):
#             image_paths.append(path)
#             continue

#         try:
#             pages = convert_from_path(
#                 pdf_path,
#                 dpi=150,
#                 first_page=i,
#                 last_page=i,
#                 **_poppler_kwargs(),   # ← changed
#             )
#             if not pages:
#                 break
#             pages[0].save(path, "PNG")
#             image_paths.append(path)
#         except Exception as exc:
#             print(f"Preview page conversion failed for page {i}: {exc}")
#             break

#     return image_paths


# def create_preview_images(document, max_pages=MAX_PREVIEW_PAGES):
#     input_path = document.file.path
#     output_dir = os.path.join(settings.MEDIA_ROOT, "preview_images")
#     _reset_cache_if_source_changed(output_dir, input_path, f"preview_{document.id}_page_", ".jpg")

#     preview_images = []
#     for i in range(1, max_pages + 1):
#         img_filename = f"preview_{document.id}_page_{i}.jpg"
#         img_path = os.path.join(output_dir, img_filename)

#         if os.path.exists(img_path):
#             preview_images.append(img_path)
#             continue

#         try:
#             pages = convert_from_path(
#                 input_path,
#                 dpi=150,
#                 first_page=i,
#                 last_page=i,
#                 **_poppler_kwargs(),   # ← changed
#             )
#             if not pages:
#                 break

#             img = pages[0]
#             img.thumbnail((800, 1200), Image.Resampling.LANCZOS)
#             img.save(img_path, "JPEG", quality=85)
#             preview_images.append(img_path)
#         except Exception as exc:
#             print(f"Preview image creation failed for page {i}: {exc}")
#             break

#     return preview_images


# def add_watermark(pdf_path):
#     """Add a visible watermark to every page in the preview PDF."""
#     doc = fitz.open(pdf_path)

#     for page in doc:
#         rect = page.rect
#         page.insert_text(
#             (rect.width / 2 - 150, rect.height / 2),
#             WATERMARK_TEXT,
#             fontsize=36,
#             rotate=45,
#             color=(0.6, 0.6, 0.6),
#             overlay=True,
#         )

#     doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
#     doc.close()


# def create_preview_images(document, max_pages=MAX_PREVIEW_PAGES):
#     """Create cached JPG preview images from the document PDF."""
#     input_path = document.file.path
#     output_dir = os.path.join(settings.MEDIA_ROOT, "preview_images")
#     _reset_cache_if_source_changed(output_dir, input_path, f"preview_{document.id}_page_", ".jpg")

#     preview_images = []
#     for i in range(1, max_pages + 1):
#         img_filename = f"preview_{document.id}_page_{i}.jpg"
#         img_path = os.path.join(output_dir, img_filename)

#         if os.path.exists(img_path):
#             preview_images.append(img_path)
#             continue

#         try:
#             pages = convert_from_path(
#                 input_path,
#                 dpi=150,
#                 poppler_path=POPPLER_PATH,
#                 first_page=i,
#                 last_page=i,
#             )
#             if not pages:
#                 break

#             img = pages[0]
#             img.thumbnail((800, 1200), Image.Resampling.LANCZOS)
#             img.save(img_path, "JPEG", quality=85)
#             preview_images.append(img_path)
#         except Exception as exc:
#             print(f"Preview image creation failed for page {i}: {exc}")
#             break

#     return preview_images




# def pdf_to_images(pdf_path, output_dir, max_pages=MAX_PREVIEW_PAGES):
#     """Convert a PDF preview into cached page images for detail/preview pages."""
#     _reset_cache_if_source_changed(output_dir, pdf_path, "page_", ".png")

#     image_paths = []
#     for i in range(1, max_pages + 1):
#         path = os.path.join(output_dir, f"page_{i}.png")

#         if os.path.exists(path):
#             image_paths.append(path)
#             continue

#         try:
#             pages = convert_from_path(
#                 pdf_path,
#                 dpi=150,
#                 poppler_path=POPPLER_PATH,
#                 first_page=i,
#                 last_page=i,
#             )
#             if not pages:
#                 break
#             pages[0].save(path, "PNG")
#             image_paths.append(path)
#         except Exception as exc:
#             print(f"Preview page conversion failed for page {i}: {exc}")
#             break

#     return image_paths


# def create_preview(document):
#     """Create a watermarked PDF preview from the first pages of a document."""
#     input_path = document.file.path
#     preview_path = os.path.join(
#         settings.MEDIA_ROOT,
#         "previews",
#         f"preview_{document.id}.pdf",
#     )
#     marker_path = preview_path + ".source_signature"
#     os.makedirs(os.path.dirname(preview_path), exist_ok=True)

#     signature = _source_signature(input_path)
#     try:
#         with open(marker_path, "r", encoding="utf-8") as marker:
#             if os.path.exists(preview_path) and marker.read() == signature:
#                 return preview_path
#     except FileNotFoundError:
#         pass

#     if os.path.exists(preview_path):
#         os.remove(preview_path)

#     doc = fitz.open(input_path)
#     preview_doc = fitz.open()
#     pages_to_keep = min(5, len(doc))

#     for i in range(pages_to_keep):
#         preview_doc.insert_pdf(doc, from_page=i, to_page=i)

#     preview_doc.save(preview_path)
#     preview_doc.close()
#     doc.close()

#     add_watermark(preview_path)

#     with open(marker_path, "w", encoding="utf-8") as marker:
#         marker.write(signature)

#     return preview_path

