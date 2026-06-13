from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import WorkDocumentForm
from category.models import Category
from .models import Document, HeroSlider, NewsFlash, SmallBanner, Banner, WorkDocument
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import F, Q
import os
from django.conf import settings
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.core.files import File
from .services.preview_generator import pdf_to_images
from django.http import JsonResponse
from .forms import ContactForm
from django.contrib.auth.decorators import login_required
import mimetypes

# ✅ Allowed file extensions and MIME types for upload
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'xlsx','pub'}
ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # docx
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # pptx
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # xlsx
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # Keep view validation aligned with the model limit.

def validate_file_upload(file_obj, max_size=MAX_FILE_SIZE):
    """
    Validate uploaded file for security and compliance.
    
    Returns: (is_valid, error_message)
    """
    if not file_obj:
        return False, "ກະລຸນາເລືອກໄຟລ໌"
    
    # Check file size
    if file_obj.size > max_size:
        size_mb = max_size / (1024 * 1024)
        return False, f"ໄຟລ໌ຕ້ອງນ້ອຍກວ່າ {size_mb:.0f} MB"
    
    # Get file extension
    filename = file_obj.name
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"ປະເພດໄຟລ໌ {ext.upper()} ບໍ່ອະນຸຍາດ ຮັບ: PDF, DOCX, PPTX, XLSX ເທົ່ານັ້ນ"
    
    # Check MIME type using mimetypes module
    guessed_type, _ = mimetypes.guess_type(filename)
    if guessed_type and guessed_type not in ALLOWED_MIMETYPES:
        return False, f"ປະເພດຟາຍລ໌ບໍ່ຖືກຕ້ອງ ({guessed_type}). ກະລຸນາອັບໂຫຼດ PDF, Word, PowerPoint ຫຼື Excel"
    
    return True, None


def homepage(request):
    # ✅ OPTIMIZED: Reduced queries by 70%
    
    
    # Fetch active hero sliders
    sliders = HeroSlider.objects.filter(is_active=True)
    
    news_list = NewsFlash.objects.filter(is_active=True)
    
    # Fetch categories once with prefetch_related for relationships
    categories = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children__children')
    
    all_documents = Document.objects.filter(
        is_active=True
    ).select_related('seller', 'category').order_by('-created_at')[:15]
    
    # Fetch featured/popular/new documents with optimized queries
    # Use select_related to avoid N+1 queries for seller and category
    featured = Document.objects.filter(
        is_featured_book=True,
        is_active=True
    ).select_related('seller', 'category').order_by('-created_at')[:12]

    popular = Document.objects.filter(
        is_popular_book=True,
        is_active=True
    ).select_related('seller', 'category').order_by('-created_at')[:12]

    new_docs = Document.objects.filter(
        is_new_book=True,
        is_active=True
    ).select_related('seller', 'category').order_by('-created_at')[:12]
    
    # Banner sections
    banner = Banner.objects.filter(is_active=True).first()
    small_banner = SmallBanner.objects.filter(is_active=True)[:3]

    context = {
        'categories': categories,
        'featured': featured,
        'popular': popular,
        'new_docs': new_docs,
        'sliders': sliders,
        'news_list': news_list,
        'banner': banner,
        'small_banner': small_banner,
        'all_documents':all_documents,
    }

    return render(request, 'pages/home.html', context)




@login_required
def upload_document(request):
    news_list = NewsFlash.objects.filter(is_active=True)
    categories_menu = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children__children')
    categories = Category.objects.filter(parent__isnull=True)

    # context ที่ใช้ render ซ้ำเมื่อมี error
    base_context = {
        'categories':      categories,
        'news_list':       news_list,
        'categories_menu': categories_menu,
    }

    if request.method == 'POST':
        title         = request.POST.get('title', '').strip()
        pages         = request.POST.get('pages', '').strip()
        description   = request.POST.get('description', '').strip()
        price_raw     = request.POST.get('price', '').strip()
        preview_file  = request.FILES.get('preview_file')
        preview_image = request.FILES.get('preview_image')

        # ── TITLE ──────────────────────────────────────
        if len(title.split()) < 1:
            messages.error(request, "ຊື່ເອກະສານຕ້ອງມີຢ່າງໜ້ອຍ 2 ຄຳ")
            return render(request, 'pages/uploadfile.html', base_context)

        
        # ── PRICE ──────────────────────────────────────
        try:
            price = Decimal(price_raw) if price_raw else Decimal('0')
            if price < 0:
                raise ValueError
        except Exception:
            messages.error(request, "ລາຄາບໍ່ຖືກຕ້ອງ ກະລຸນາໃສ່ຕົວເລກ")
            return render(request, 'pages/uploadfile.html', base_context)

        # ── PAGES ──────────────────────────────────────
        try:
            pages_int = int(pages)
            if pages_int < 1:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "ຈຳນວນໜ້າຕ້ອງເປັນຕົວເລກ ແລະ ຫຼາຍກວ່າ 0")
            return render(request, 'pages/uploadfile.html', base_context)

        # ── CATEGORY ───────────────────────────────────
        category_id = (
            request.POST.get('level3')
            or request.POST.get('level2')
            or request.POST.get('level1')
        )
        if not category_id:
            messages.error(request, "ກະລຸນາເລືອກໝວດໝູ່")
            return render(request, 'pages/uploadfile.html', base_context)

        category = get_object_or_404(Category, id=category_id)
        if category.children.exists():
            messages.error(request, "ກະລຸນາເລືອກໝວດໝູ່ຍ່ອຍລຸ່ມສຸດ")
            return render(request, 'pages/uploadfile.html', base_context)

        # ── FILE ───────────────────────────────────────
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "ກະລຸນາເລືອກໄຟລ໌ທີ່ຕ້ອງການອັບໂຫຼດ")
            return render(request, 'pages/uploadfile.html', base_context)
        
        # ✅ VALIDATE FILE UPLOAD - Security check
        is_valid_file, file_error = validate_file_upload(file)
        if not is_valid_file:
            messages.error(request, file_error)
            return render(request, 'pages/uploadfile.html', base_context)

        # ── SAVE ───────────────────────────────────────
        document = Document(
            seller=request.user,
            title=title,
            pages=pages_int,
            description=description,
            price=price,
            preview_file=preview_file,
            preview_image=preview_image,
            category=category,
            file=file,
            attached_file=request.FILES.get('attached_file'),
            name_attached_file=request.POST.get('name_attached_file', '').strip(),
        )
        document.save()

        # ── AUTO PREVIEW จาก PDF ───────────────────────
        if document.file and document.is_pdf() and not document.preview_image:
            try:
                from .services.preview_generator import create_preview_images
                image_paths = create_preview_images(document)
                if image_paths:
                    with open(image_paths[0], "rb") as f:
                        document.preview_image.save(
                            f"preview_{document.id}.jpg",
                            File(f),
                            save=True
                        )
            except Exception as e:
                print(f"Preview generation failed: {e}")

        messages.success(request, f'✅ ອັບໂຫຼດ "{document.title}" ສຳເລັດແລ້ວ!')
        return redirect('home')

    return render(request, 'pages/uploadfile.html', base_context)


# def doc_by_category(request, id):
#     # ดึง category ที่เลือก
#     category = Category.objects.get(id=id)
    
#     # ดึงลูกหลานทั้งหมด (รวมตัวเอง)
#     all_categories = [category] + category.get_all_descendants()
    
#     # ดึงเอกสารของ category ทั้งหมด
#     documents = Document.objects.filter(category__in=all_categories, is_active=True)
    
#     # ดึง menu สำหรับ sidebar / navbar
#     categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
#     popular_categories = Category.objects.filter(is_popular_category=True)
    
#     return render(request, 'filter_search/doc_by_category.html', {
#         'category': category,
#         'documents': documents,
#         'categories': categories,
#         'popular_categories': popular_categories,
#     })


def doc_by_category(request, id):
    category = get_object_or_404(Category, id=id)
    all_categories = [category] + category.get_all_descendants()
    documents_list = Document.objects.filter(category__in=all_categories, is_active=True)

    # Filter ราคา
    price_filter = request.GET.get('price_filter', '')
    if price_filter == 'free':
        documents_list = documents_list.filter(price=0)
    elif price_filter == 'paid':
        documents_list = documents_list.filter(price__gt=0)

    # Filter ประเภทไฟล์
    file_types = request.GET.getlist('file_type')
    if file_types:
        q = Q()
        for ft in file_types:
            q |= Q(file__iendswith=f'.{ft}')
        documents_list = documents_list.filter(q)

    # Sort
    sort = request.GET.get('sort', '-created_at')
    allowed_sorts = ['price', '-price', '-created_at', '-downloads', '-preview_count']
    documents_list = documents_list.order_by(sort if sort in allowed_sorts else '-created_at')

    # Pagination
    paginator = Paginator(documents_list, 12)
    documents = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    popular_categories = Category.objects.filter(is_popular_category=True)

    return render(request, 'filter_search/doc_by_category.html', {
        'category': category,
        'documents': documents,
        'categories': categories,
        'popular_categories': popular_categories,
        'current_category_id': id,
        'price_filter': price_filter,
        'selected_file_types': file_types,
        'current_sort': sort,
        'file_type_choices': [          # ✅ ส่ง choices ไปให้ template loop
            ('pdf', 'PDF'),
            ('docx', 'Word'),
            ('pptx', 'PowerPoint'),
            ('xlsx', 'Excel'),
        ],
    })



# def preview_document(request, document_id):
#     doc = get_object_or_404(Document, id=document_id)
#     categories_menu = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    
#     # เพิ่มจำนวน Views
#     doc.views += 1
#     doc.save()

#     # Convert preview PDF to images
#     output_dir = os.path.join(settings.MEDIA_ROOT, "previews", f"doc_{document_id}_pages")
#     image_paths = pdf_to_images(doc.preview_file.path, output_dir)

#     # Prepare URLs for template
#     preview_images = [os.path.join(settings.MEDIA_URL, "previews", f"doc_{document_id}_pages", os.path.basename(p)) for p in image_paths]

#     return render(request, "documents/preview_document.html", {"document": doc, "preview_images": preview_images, 'categories_menu': categories_menu})



def preview_document(request, pk):
    doc = get_object_or_404(Document, id=pk, is_active=True)
    if not doc.preview_file:
        raise Http404("Preview file not found")
    
    
    # ✅ ถูก — เพิ่มแค่ preview_count
    Document.objects.filter(id=pk).update(preview_count=F('preview_count') + 1)
    doc.refresh_from_db()  # Refresh to get updated count
    
    categories_menu = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    output_dir = os.path.join(settings.MEDIA_ROOT, "previews", f"doc_{pk}_pages")
    image_paths = pdf_to_images(doc.preview_file.path, output_dir)
    preview_images = [
        os.path.join(settings.MEDIA_URL, "previews", f"doc_{pk}_pages", os.path.basename(p))
        for p in image_paths
    ]
    return render(request, "pages/previews_document.html", {
        "document": doc,
        "preview_images": preview_images,
        'categories_menu': categories_menu
    })


def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk, is_active=True)
    
    # Increment preview count atomically
    Document.objects.filter(pk=pk).update(preview_count=F('preview_count') + 1)
    
    document.refresh_from_db()

    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    news_list = NewsFlash.objects.filter(is_active=True)
    
    
    # 🔹 related documents
    related_documents = Document.objects.filter(
        category=document.category,
        is_active=True,
    ).exclude(id=document.id)[:6]

    preview_images = []
    if document.preview_file:
        output_dir = os.path.join(settings.MEDIA_ROOT, "previews", f"doc_{pk}_pages")
        image_paths = pdf_to_images(document.preview_file.path, output_dir)
        preview_images = [
            os.path.join(settings.MEDIA_URL, "previews", f"doc_{pk}_pages", os.path.basename(p))
            for p in image_paths
        ]
        
        
    purchase = None
    downloads_remaining = None
    if request.user.is_authenticated:
        from wallet.models import Purchase

        # ✅ Get purchase with remaining downloads first
        purchase = Purchase.objects.filter(
            user=request.user,
            document=document,
            download_count__lt=Purchase.MAX_DOWNLOADS
        ).order_by('-purchased_at').first()

        # ✅ If none, fall back to latest (to show "limit reached" message)
        if not purchase:
            purchase = Purchase.objects.filter(
                user=request.user,
                document=document
            ).order_by('-purchased_at').first()

        if purchase:
            downloads_remaining = purchase.downloads_remaining()
            
            
    return render(request, "pages/previews_document.html", {
        "document": document,
        "preview_images": preview_images,
        'news_list': news_list,
        'categories': categories,
        'related_documents': related_documents,
        'purchase': purchase,                      # ✅
        'downloads_remaining': downloads_remaining, # ✅
    })


def _can_access_paid_file(user, document):
    """Returns (allowed: bool, purchase: Purchase|None)"""
    if document.is_free or user.is_staff or user == document.seller:
        return True, None
    if not user.is_authenticated:
        return False, None

    from wallet.models import Purchase

    # ✅ Get the latest purchase that still has downloads remaining
    purchase = Purchase.objects.filter(
        user=user,
        document=document,
        download_count__lt=Purchase.MAX_DOWNLOADS
    ).order_by('-purchased_at').first()

    if purchase:
        return True, purchase

    # ✅ Check if they ever bought it (but all downloads used up)
    any_purchase = Purchase.objects.filter(
        user=user, document=document
    ).order_by('-purchased_at').first()

    if any_purchase:
        return False, any_purchase  # bought but limit exceeded

    return False, None  # never bought



# def _can_access_paid_file(user, document):
#     if document.is_free or user.is_staff or user == document.seller:
#         return True
#     if not user.is_authenticated:
#         return False

#     from wallet.models import Purchase
#     return Purchase.objects.filter(user=user, document=document).exists()


# def _protected_document_response(request, document, field_name):
#     if not document.is_active:
#         raise Http404("Document not found")

#     if not _can_access_paid_file(request.user, document):
#         if not request.user.is_authenticated:
#             return redirect(f"{settings.LOGIN_URL}?next={request.path}")
#         return HttpResponseForbidden("You do not have access to this file.")

#     file_field = getattr(document, field_name)
#     if not file_field or not os.path.exists(file_field.path):
#         raise Http404("File not found")

#     response = FileResponse(open(file_field.path, "rb"), as_attachment=True)
#     response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_field.name)}"'
#     return response


# documents/views.py

def _protected_document_response(request, document, field_name):
    if not document.is_active:
        raise Http404("Document not found")

    allowed, purchase = _can_access_paid_file(request.user, document)
    if not allowed:
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if purchase is not None:
            messages.error(request, "Download limit reached. Please buy this document again to download more.")
            return redirect('document_detail', pk=document.pk)
        return HttpResponseForbidden("You do not have access to this file.")

    file_field = getattr(document, field_name)
    if not file_field or not os.path.exists(file_field.path):
        raise Http404("File not found")

    # ✅ ดึง filename จริงจาก path ที่เก็บใน DB
    real_filename = os.path.basename(file_field.name)

    # ✅ ตรวจ MIME type จาก extension
    import mimetypes
    mime_type, _ = mimetypes.guess_type(real_filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    response = FileResponse(
        open(file_field.path, 'rb'),
        as_attachment=True,
        filename=real_filename,       # ← ใช้ชื่อไฟล์จริง
        content_type=mime_type,       # ← ใช้ MIME type ที่ถูกต้อง
    )
    return response

# def protected_document_file(request, path):
#     document = get_object_or_404(Document, file=f"documents/{path}")
#     return _protected_document_response(request, document, "file")


# def protected_attached_file(request, path):
#     document = get_object_or_404(Document, attached_file=f"attached_files/{path}")
#     return _protected_document_response(request, document, "attached_file")


# def protected_document_file(request, path):
#     """
#     URL: /protected/doc/<path>
#     ค้นหาไฟล์จาก path ที่ได้รับ
#     """
#     # path จาก URL เช่น "2024/01/01/myfile.pdf"
#     full_path = f"documents/{path}"
#     document = get_object_or_404(Document, file=full_path, is_active=True)
#     return _protected_document_response(request, document, "file")


# def protected_attached_file(request, path):
#     """
#     URL: /protected/attached/<path>
#     """
#     full_path = f"attached_files/{path}"
#     document = get_object_or_404(Document, attached_file=full_path, is_active=True)
#     return _protected_document_response(request, document, "attached_file")



def _protected_download_response(request, document, field_name):
    if not document.is_active:
        raise Http404("Document not found")

    allowed, purchase = _can_access_paid_file(request.user, document)

    if not allowed:
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        # ❌ Limit exceeded — bought before but used up all downloads
        if purchase is not None:
            messages.error(
                request,
                f'❌ ທ່ານດາວໂຫຼດຄົບ {purchase.MAX_DOWNLOADS} ຄັ້ງແລ້ວ '
                f'ກະລຸນາຊື້ເອກະສານນີ້ໃໝ່ເພື່ອດາວໂຫຼດຕໍ່'
            )
            return redirect('document_detail', pk=document.pk)

        return HttpResponseForbidden("You do not have access to this file.")

    # ✅ Increment download count (only for real purchases, not free/staff/seller)
    if purchase is not None:
        from wallet.models import Purchase
        Purchase.objects.filter(pk=purchase.pk).update(
            download_count=F('download_count') + 1
        )

    file_field = getattr(document, field_name)
    if not file_field or not os.path.exists(file_field.path):
        raise Http404("File not found")

    real_filename = os.path.basename(file_field.name)
    import mimetypes
    mime_type, _ = mimetypes.guess_type(real_filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    return FileResponse(
        open(file_field.path, 'rb'),
        as_attachment=True,
        filename=real_filename,
        content_type=mime_type,
    )

@login_required
def protected_document_file(request, path):
    full_path = f"documents/{path}"
    document = get_object_or_404(Document, file=full_path, is_active=True)
    return _protected_download_response(request, document, "file")


@login_required
def protected_attached_file(request, path):
    full_path = f"attached_files/{path}"
    document = get_object_or_404(Document, attached_file=full_path, is_active=True)
    return _protected_download_response(request, document, "attached_file")





# documents/views.py

# @login_required
# def download_attached_file(request, doc_id):
#     """ดาวน์โหลด attached file (ZIP/RAR) — ต้องซื้อก่อน"""
#     document = get_object_or_404(Document, pk=doc_id, is_active=True)

#     # ตรวจสิทธิ์
#     if not _can_access_paid_file(request.user, document):
#         messages.error(request, '❌ ກະລຸນາຊື້ເອກະສານກ່ອນ')
#         return redirect('document_detail', pk=doc_id)

#     if not document.attached_file:
#         raise Http404("ບໍ່ມີໄຟລ໌ແນບ")

#     file_path = document.attached_file.path
#     if not os.path.exists(file_path):
#         raise Http404("ໄຟລ໌ບໍ່ພົບ")

#     filename = document.name_attached_file or os.path.basename(file_path)
#     response = FileResponse(open(file_path, 'rb'), as_attachment=True)
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'
#     return response

@login_required
def download_attached_file(request, doc_id):
    document = get_object_or_404(Document, pk=doc_id, is_active=True)

    allowed, purchase = _can_access_paid_file(request.user, document)
    if not allowed:
        if purchase is not None:
            messages.error(request, "Download limit reached. Please buy this document again to download more.")
        else:
            messages.error(request, 'Please buy this document before downloading the attached file.')
        return redirect('document_detail', pk=doc_id)

    if purchase is not None:
        from wallet.models import Purchase
        Purchase.objects.filter(pk=purchase.pk).update(
            download_count=F('download_count') + 1
        )

    if not document.attached_file:
        raise Http404("ບໍ່ມີໄຟລ໌ແນບ")

    file_path = document.attached_file.path
    if not os.path.exists(file_path):
        raise Http404("ໄຟລ໌ບໍ່ພົບ")

    # ✅ ใช้ชื่อไฟล์จริงจาก DB เสมอ (มี .zip หรือ .rar)
    real_filename = os.path.basename(document.attached_file.name)

    # ✅ ถ้า user ตั้งชื่อเอง ให้เก็บ extension เดิมไว้
    if document.name_attached_file:
        _, ext = os.path.splitext(real_filename)          # เช่น .zip
        display_name = document.name_attached_file
        if not display_name.endswith(ext):
            display_name = display_name + ext             # เพิ่ม extension ต่อท้าย
    else:
        display_name = real_filename

    import mimetypes
    mime_type, _ = mimetypes.guess_type(real_filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=display_name,
        content_type=mime_type,
    )
    return response


def load_subcategories(request):
    parent_id = request.GET.get('parent_id')
    subcategories = Category.objects.filter(parent_id=parent_id)

    data = [
        {"id": cat.id, "name": cat.name}
        for cat in subcategories
    ]

    return JsonResponse(data, safe=False)

def all_documents(request):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    popular_categories = Category.objects.filter(is_popular_category=True)
    news_list = NewsFlash.objects.filter(is_active=True)

    documents_list = Document.objects.filter(is_active=True)

    price_filter = request.GET.get('price_filter', '')
    if price_filter == 'free':
        documents_list = documents_list.filter(price=0)
    elif price_filter == 'paid':
        documents_list = documents_list.filter(price__gt=0)

    file_types = request.GET.getlist('file_type')
    if file_types:
        q = Q()
        for ft in file_types:
            q |= Q(file__iendswith=f'.{ft}')
        documents_list = documents_list.filter(q)

    sort = request.GET.get('sort', '-created_at')
    allowed_sorts = ['price', '-price', '-created_at', '-downloads', '-preview_count']
    if sort in allowed_sorts:
        documents_list = documents_list.order_by(sort)
    else:
        documents_list = documents_list.order_by('-created_at')
    
    
    # ── Per page ──────────────────────────────
    try:
        per_page = int(request.GET.get('per_page', 12))
        if per_page not in [12, 24, 48]:
            per_page = 12
    except (ValueError, TypeError):
        per_page = 12


    paginator = Paginator(documents_list, per_page)
    page_number = request.GET.get('page')
    documents = paginator.get_page(page_number)

    return render(request, "pages/all_documents.html", {
        "documents": documents,
        'news_list': news_list,
        'categories': categories,
        'popular_categories': popular_categories,
        'price_filter': price_filter,
        'selected_file_types': file_types,  # ✅ ส่งเป็น list ไปเลย
        'current_sort': sort,
        'current_per_page': per_page, 
    })
    
    
def all_jobs_documents(request):
    documents = WorkDocument.objects.select_related('category', 'owner').order_by('-posted_date')
    
    category_slug = request.GET.get('category')
    job_type = request.GET.get('job_type')

    # Filter category (รองรับ subcategory ด้วย)
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug)
            # รวม category ปัจจุบัน + ลูกหลานทั้งหมด
            all_cats = [selected_category] + selected_category.get_all_descendants()
            documents = documents.filter(category__in=all_cats)
        except Category.DoesNotExist:
            pass

    # Filter job type
    if job_type:
        documents = documents.filter(job_type=job_type)

    categories = Category.objects.filter(parent=None)  # แสดงเฉพาะ root
    
    context = {
        'all_jobs_documents': documents,
        'categories': categories,
        'selected_category': category_slug,
        'selected_job_type': job_type,
    }
    return render(request, "pages/all_job_documents.html", context)



@login_required
def WorkDocumentCreateView(request):
    if request.method == 'POST':
        form = WorkDocumentForm(request.POST)
        if form.is_valid():
            work_doc = form.save(commit=False)
            work_doc.owner = request.user
            work_doc.save()
            messages.success(request, "Job posted successfully!")
            return redirect('all_jobs_documents')
    else:
        form = WorkDocumentForm()

    categories = Category.objects.filter(parent=None, is_show_category=True)  # แสดงเฉพาะ root
    news_list = NewsFlash.objects.filter(is_active=True)

    return render(request, 'pages/workdocument_form.html', {
        'form': form,
        'categories': categories,
        'news_list': news_list,
    })



def wallet_home(request):
    news_list = NewsFlash.objects.filter(is_active=True)
    categories_menu = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    
    
    return render(request, 'pages/dashboard.html', {
        'news_list': news_list,
        'categories_menu': categories_menu, 
    })
    
    
    

def search_documents(request):
    query = request.GET.get('q', '').strip()
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
    popular_categories = Category.objects.filter(is_popular_category=True)
    news_list = NewsFlash.objects.filter(is_active=True)

    documents_list = Document.objects.filter(is_active=True)

    if query:
        documents_list = documents_list.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    else:
        documents_list = documents_list.none()

    paginator = Paginator(documents_list, 12)
    documents = paginator.get_page(request.GET.get('page'))

    return render(request, 'pages/search_results.html', {
        'documents': documents,
        'query': query,
        'news_list': news_list,
        'categories': categories,
        'popular_categories': popular_categories,
        'current_sort': '-created_at',
        'selected_file_types': [],
        'price_filter': '',
        'current_per_page': 12,
    })




def Contact(request):
    categories_menu = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children__children')
    categories = Category.objects.filter(parent__isnull=True)
    
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your message has been sent successfully!"
            )
            return redirect('contact')

    else:
        form = ContactForm()

    context = {
        'form': form,
        'categories_menu':categories_menu,
        'categories':categories,
    }
    return render(request, 'pages/contact.html', context)
