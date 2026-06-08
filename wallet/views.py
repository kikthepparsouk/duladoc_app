from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from decimal import Decimal
import os
from django.db.models import F
from django_ratelimit.decorators import ratelimit

from .models import Wallet, TopUpRequest, Purchase, WalletTransaction, Payment_banks
from .forms import TopUpRequestForm
from documents.models import Document, NewsFlash
from category.models import Category


# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────

def get_or_create_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def get_platform_wallet():
    """กระเป๋าของระบบ — ใช้ superuser คนแรก"""
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        wallet, _ = Wallet.objects.get_or_create(user=admin_user)
        return wallet
    return None


def _serve_file(document):
    """ส่งไฟล์ให้ผู้ใช้ดาวน์โหลด"""
    
    # ✅ เพิ่ม download count (กัน concurrent)
    Document.objects.filter(pk=document.pk).update(
        downloads=F('downloads') + 1
    )
    
    file_path = document.file.path
    if not os.path.exists(file_path):
        raise Http404('ໍ່ບໍ່ພົບໄຟລ໌')
    
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response

    

    # file_path = document.file.path
    # if not os.path.exists(file_path):
    #     raise Http404('ໍ່ບໍ່ພົບໄຟລ໌')

    # response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    # response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    # return response


def is_staff(user):
    return user.is_staff


# ─────────────────────────────────────────────────────────
#  DASHBOARD / WALLET HOME
# ─────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    # ✅ OPTIMIZED: Remove duplicate queries, use context from processor
    news_list = NewsFlash.objects.filter(is_active=True)

    wallet = get_or_create_wallet(request.user)

    # ✅ Paginate transactions — 10 per page
    transactions_qs = wallet.transactions.order_by('-created_at')

    tx_page_num = request.GET.get('tx_page', 1)
    tx_paginator = Paginator(transactions_qs, 10)
    transactions = tx_paginator.get_page(tx_page_num)

    topup_requests = TopUpRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    return render(request, 'pages/dashboard.html', {
        'wallet': wallet,
        'transactions': transactions,
        'topup_requests': topup_requests,
        'news_list': news_list,
        'active_tab': 'dashboard',
    })
    
# @login_required
# def dashboard(request):
#     news_list = NewsFlash.objects.filter(is_active=True)
#     categories_menu = Category.objects.filter(
#         parent__isnull=True
#     ).prefetch_related('children__children')

#     wallet = get_or_create_wallet(request.user)
#     transactions = wallet.transactions.order_by('-created_at')[:20]
#     topup_requests = TopUpRequest.objects.filter(
#         user=request.user
#     ).order_by('-created_at')[:5]

#     return render(request, 'pages/dashboard.html', {
#         'wallet': wallet,
#         'transactions': transactions,
#         'topup_requests': topup_requests,
#         'news_list': news_list,
#         'categories_menu': categories_menu,
#         'active_tab': 'dashboard',
#     })


# ─────────────────────────────────────────────────────────
#  เติมเงิน
# ─────────────────────────────────────────────────────────

@login_required
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def topup_request_view(request):
   
    wallet = get_or_create_wallet(request.user)
    payment_bank = Payment_banks.objects.filter(is_active=True)

    if request.method == 'POST':
        form = TopUpRequestForm(request.POST, request.FILES)
        if form.is_valid():
            topup = form.save(commit=False)
            topup.user = request.user
            topup.save()
            messages.success(request, '✅ ສົ່ງຄຳຂໍຕື່ມເງິນແລ້ວ ລໍຖ້າ Admin ກວດສອບ')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ ກະລຸນາກວດສອບຂໍ້ມູນ')
    else:
        form = TopUpRequestForm()

    return render(request, 'pages/topup_request.html', {
        'form': form,
        'wallet': wallet,
        'payment_bank': payment_bank,
        'active_tab': 'topup',
        
    })


# ─────────────────────────────────────────────────────────
#  ซื้อ + ดาวน์โหลดเอกสาร  ← จุดหลัก
# ─────────────────────────────────────────────────────────

# @login_required
# @require_POST
# @transaction.atomic
# def buy_and_download(request, doc_id):
#     """
#     Flow เดียวจบ:
#       1. login แล้ว (จัดการโดย @login_required)
#       2. เคยซื้อแล้ว / เอกสารฟรี → ดาวน์โหลดทันที
#       3. ตรวจเงินในกระเป๋า
#       4. หักเงิน + แบ่งให้ seller + admin → ดาวน์โหลด
#     """
#     document = get_object_or_404(Document, pk=doc_id, is_active=True)

#     if document.seller == request.user or request.user.is_staff:
#         return _serve_file(document)

#     # ── Step 2a: เคยซื้อแล้ว ──────────────────────────────
#     already_purchased = Purchase.objects.filter(
#         user=request.user, document=document
#     ).exists()

#     if already_purchased:
#         return _serve_file(document)

#     # ── Step 2b: เอกสารฟรี ───────────────────────────────
#     if document.is_free:
#         # บันทึกว่า "ซื้อ" ไว้เพื่อไม่ต้องเช็คซ้ำ
#         Purchase.objects.get_or_create(
#             user=request.user,
#             document=document,
#             defaults={
#                 'amount_paid': Decimal('0'),
#                 'seller_received': Decimal('0'),
#                 'platform_received': Decimal('0'),
#             }
#         )
#         return _serve_file(document)

#     # ── Step 3: ตรวจกระเป๋าเงิน ──────────────────────────
#     wallet = get_or_create_wallet(request.user)

#     wallet = Wallet.objects.select_for_update().get(user=request.user)

#     if Purchase.objects.filter(user=request.user, document=document).exists():
#         return _serve_file(document)

#     if not wallet.has_enough(document.price):
#         shortage = document.price - wallet.balance
#         messages.warning(
#             request,
#             f'💰 ຍອດເງິນໃນກະເປົ໋າບໍ່ພໍ ຕ້ອງຕື່ມເງິນອີກ {shortage:,.0f} ກີບ'
#         )
#         # redirect ไปเติมเงิน พร้อม next= เพื่อกลับมาดาวน์โหลดหลังเติม
#         return redirect(f'/wallet/topup/?next=/document/{doc_id}/')

#     # ── Step 4: หักเงิน + แบ่งให้ seller + admin ─────────
#     seller_amount   = document.seller_amount()
#     platform_amount = document.platform_amount()

#     # หักเงินผู้ซื้อ
#     wallet.balance -= document.price
#     wallet.save(update_fields=['balance', 'updated_at'])

#     # บันทึกการซื้อ
#     purchase = Purchase.objects.create(
#         user=request.user,
#         document=document,
#         amount_paid=document.price,
#         seller_received=seller_amount,
#         platform_received=platform_amount,
#     )

#     # Transaction ผู้ซื้อ
#     WalletTransaction.objects.create(
#         wallet=wallet,
#         transaction_type='purchase',
#         amount=document.price,
#         description=f'ຊື້ເອກະສານ: {document.title}',
#         reference=str(purchase.pk)
#     )

#     # โอนให้ seller  ← ✅ ใช้ document.seller ไม่ใช่ document.owner
#     if document.seller and seller_amount > 0:
#         get_or_create_wallet(document.seller)
#         seller_wallet = Wallet.objects.select_for_update().get(user=document.seller)
#         seller_wallet.balance += seller_amount
#         seller_wallet.save(update_fields=['balance', 'updated_at'])
#         WalletTransaction.objects.create(
#             wallet=seller_wallet,
#             transaction_type='revenue',
#             amount=seller_amount,
#             description=f'ລາຍໄດ້ຈາກ: {document.title} (ຜູ້ຊື້: {request.user.username})',
#             reference=str(purchase.pk)
#         )

#     # โอนให้ admin/platform
#     if platform_amount > 0:
#         platform_wallet = get_platform_wallet()
#         if platform_wallet:
#             platform_wallet = Wallet.objects.select_for_update().get(pk=platform_wallet.pk)
#             platform_wallet.balance += platform_amount
#             platform_wallet.save(update_fields=['balance', 'updated_at'])
#             WalletTransaction.objects.create(
#                 wallet=platform_wallet,
#                 transaction_type='platform_fee',
#                 amount=platform_amount,
#                 description=f'ຄ່າທຳນຽມ: {document.title}',
#                 reference=str(purchase.pk)
#             )

#     # ส่งไฟล์ทันที
    
#     return _serve_file(document)


@login_required
@require_POST
@transaction.atomic
@ratelimit(key='user', rate='20/h', method='POST', block=True)
def buy_and_download(request, doc_id):
    
    document = get_object_or_404(Document, pk=doc_id, is_active=True)

    if document.seller == request.user or request.user.is_staff:
        return _serve_file(document)

    # ── Step 2b: เอกสารฟรี ───────────────────────────────
    if document.is_free:
        Purchase.objects.get_or_create(
            user=request.user,
            document=document,
            defaults={
                'amount_paid': Decimal('0'),
                'seller_received': Decimal('0'),
                'platform_received': Decimal('0'),
            }
        )
        return _serve_file(document)

    # ✅ Check if user has a purchase with downloads remaining
    active_purchase = Purchase.objects.filter(
        user=request.user,
        document=document,
        download_count__lt=Purchase.MAX_DOWNLOADS
    ).order_by('-purchased_at').first()

    if active_purchase:
        # ✅ Increment download count
        Purchase.objects.filter(pk=active_purchase.pk).update(
            download_count=F('download_count') + 1
        )
        return _serve_file(document)

    # ✅ Check if they bought before but used all downloads
    exhausted_purchase = Purchase.objects.filter(
        user=request.user,
        document=document
    ).exists()

    if exhausted_purchase:
        # ❌ Must buy again
        shortage = Decimal('0')
        wallet = get_or_create_wallet(request.user)
        if not wallet.has_enough(document.price):
            shortage = document.price - wallet.balance
            messages.warning(request, f'💰 ດາວໂຫຼດຄົບ 5 ຄັ້ງແລ້ວ ແລະ ຍອດເງິນໃນກະເປົ໋າບໍ່ພໍ ຕ້ອງຕື່ມເງິນອີກ {shortage:,.0f} ກີບ')
            return redirect(f'/wallet/topup/?next=/document/{doc_id}/')
        # Fall through to buy again below

    # ── Step 3: ตรวจกระเป๋าเงิน ──────────────────────────
    wallet = Wallet.objects.select_for_update().get(user=request.user)

    if not wallet.has_enough(document.price):
        shortage = document.price - wallet.balance
        messages.warning(request, f'💰 ຍອດເງິນໃນກະເປົ໋າບໍ່ພໍ ຕ້ອງຕື່ມເງິນອີກ {shortage:,.0f} ກີບ')
        return redirect(f'/wallet/topup/?next=/document/{doc_id}/')

    # ── Step 4: หักเงิน + แบ่งให้ seller + admin ─────────
    seller_amount   = document.seller_amount()
    platform_amount = document.platform_amount()

    wallet.balance -= document.price
    wallet.save(update_fields=['balance', 'updated_at'])

    # ✅ Always create a NEW purchase (allows re-buying after limit)
    purchase = Purchase.objects.create(
        user=request.user,
        document=document,
        amount_paid=document.price,
        seller_received=seller_amount,
        platform_received=platform_amount,
        download_count=1,  # ✅ Count this download immediately
    )

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='purchase',
        amount=document.price,
        description=f'ຊື້ເອກະສານ: {document.title}',
        reference=str(purchase.pk)
    )

    if document.seller and seller_amount > 0:
        get_or_create_wallet(document.seller)
        seller_wallet = Wallet.objects.select_for_update().get(user=document.seller)
        seller_wallet.balance += seller_amount
        seller_wallet.save(update_fields=['balance', 'updated_at'])
        WalletTransaction.objects.create(
            wallet=seller_wallet,
            transaction_type='revenue',
            amount=seller_amount,
            description=f'ລາຍໄດ້ຈາກ: {document.title} (ຜູ້ຊື້: {request.user.username})',
            reference=str(purchase.pk)
        )

    if platform_amount > 0:
        platform_wallet = get_platform_wallet()
        if platform_wallet:
            platform_wallet = Wallet.objects.select_for_update().get(pk=platform_wallet.pk)
            platform_wallet.balance += platform_amount
            platform_wallet.save(update_fields=['balance', 'updated_at'])
            WalletTransaction.objects.create(
                wallet=platform_wallet,
                transaction_type='platform_fee',
                amount=platform_amount,
                description=f'ຄ່າທຳນຽມ: {document.title}',
                reference=str(purchase.pk)
            )

    return _serve_file(document)


# ─────────────────────────────────────────────────────────
#  API: ตรวจสอบสถานะก่อนคลิก Download (ใช้ใน JS)
# ─────────────────────────────────────────────────────────

# @login_required
# def check_download_status(request, doc_id):
#     """
#     GET /wallet/check/<doc_id>/
#     Return JSON สำหรับ frontend ตัดสินใจว่าจะแสดง popup หรือ redirect
#     """
#     document = get_object_or_404(Document, pk=doc_id, is_active=True)
#     wallet = get_or_create_wallet(request.user)

#     already_purchased = Purchase.objects.filter(
#         user=request.user, document=document
#     ).exists()

#     return JsonResponse({
#         'is_free': bool(document.is_free),
#         'already_purchased': already_purchased,
#         'price': float(document.price),
#         'balance': float(wallet.balance),
#         'can_afford': wallet.has_enough(document.price),
#         'shortage': float(max(document.price - wallet.balance, Decimal('0'))),
#     })

# @login_required
# def check_download_status(request, doc_id):
#     document = get_object_or_404(Document, pk=doc_id, is_active=True)
#     wallet   = get_or_create_wallet(request.user)

#     # ✅ เพิ่ม: seller และ admin ดาวน์โหลดฟรี
#     if document.seller == request.user or request.user.is_superuser:
#         return JsonResponse({
#             'is_free': True,
#             'already_purchased': True,
#             'price': 0,
#             'balance': float(wallet.balance),
#             'can_afford': True,
#             'shortage': 0,
#         })

#     already_purchased = Purchase.objects.filter(
#         user=request.user, document=document
#     ).exists()

#     return JsonResponse({
#         'is_free':          bool(document.is_free),
#         'already_purchased': already_purchased,
#         'price':            float(document.price),
#         'balance':          float(wallet.balance),
#         'can_afford':       wallet.has_enough(document.price),
#         'shortage':         float(max(document.price - wallet.balance, Decimal('0'))),
#     })


@login_required
def check_download_status(request, doc_id):
    document = get_object_or_404(Document, pk=doc_id, is_active=True)
    wallet = get_or_create_wallet(request.user)

    if document.seller == request.user or request.user.is_superuser:
        return JsonResponse({
            'is_free': True, 'already_purchased': True,
            'price': 0, 'balance': float(wallet.balance),
            'can_afford': True, 'shortage': 0,
        })

    # ✅ Check active purchase (has downloads remaining)
    active_purchase = Purchase.objects.filter(
        user=request.user,
        document=document,
        download_count__lt=Purchase.MAX_DOWNLOADS
    ).first()

    already_purchased = active_purchase is not None

    return JsonResponse({
        'is_free':           bool(document.is_free),
        'already_purchased': already_purchased,  # ✅ False when limit reached
        'price':             float(document.price),
        'balance':           float(wallet.balance),
        'can_afford':        wallet.has_enough(document.price),
        'shortage':          float(max(document.price - wallet.balance, Decimal('0'))),
    })
# ─────────────────────────────────────────────────────────
#  ADMIN: อนุมัติ/ปฏิเสธเติมเงิน
# ─────────────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_superuser)
def admin_topup_list(request):
    pending  = TopUpRequest.objects.filter(status='pending').order_by('-created_at')
    approved = TopUpRequest.objects.filter(status='approved').order_by('-reviewed_at')[:10]
    rejected = TopUpRequest.objects.filter(status='rejected').order_by('-reviewed_at')[:10]
    return render(request, 'wallet/admin_topup_list.html', {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
    })


@user_passes_test(lambda u: u.is_superuser)
def admin_topup_detail(request, pk):
    topup = get_object_or_404(TopUpRequest, pk=pk)
    return render(request, 'wallet/admin_topup_detail.html', {'topup': topup})


@user_passes_test(lambda u: u.is_superuser)
def admin_topup_slip(request, pk):
    """Serve slip image to authorized admins only"""
    topup = get_object_or_404(TopUpRequest, pk=pk)
    if not request.user.is_superuser:
        return redirect('admin_topup_list')
    if not topup.slip_image:
        raise Http404
    file_path = topup.slip_image.path
    if not os.path.exists(file_path):
        raise Http404
    return FileResponse(open(file_path, 'rb'), as_attachment=False)



@user_passes_test(lambda u: u.is_superuser)
@require_POST
@transaction.atomic
def admin_topup_approve(request, pk):
    if request.method != 'POST':
        return redirect('admin_topup_list')

    try:
        topup = TopUpRequest.objects.select_for_update().get(pk=pk, status='pending')
    except TopUpRequest.DoesNotExist:
        messages.warning(request, '⚠️ ຄຳຂໍນີ້ຖືກຈັດການແລ້ວ')
        return redirect('admin_topup_list')

    action = request.POST.get('action')

    if action == 'approve':
        # Lock wallet row before modifying to avoid double-credit
        try:
            wallet = Wallet.objects.select_for_update().get(user=topup.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=topup.user, balance=Decimal('0'))
        # use F-expression to avoid race on balance
        Wallet.objects.filter(pk=wallet.pk).update(balance=F('balance') + topup.amount)
        wallet.refresh_from_db()
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='topup',
            amount=topup.amount,
            description=f'ຕື່ມເງິນ (ອະນຸມັດໂດຍ {request.user.username})',
            reference=str(topup.pk)
        )
        topup.status = 'approved'
        messages.success(request, f'✅ ອະນຸມັດຕື່ມເງິນ {topup.amount:,} ກີບ ໃຫ້ {topup.user.username}')

    elif action == 'reject':
        topup.status = 'rejected'
        messages.warning(request, f'⚠️ ປະຕິເສດຄຳຂໍຂອງ {topup.user.username}')

    topup.reviewed_at = timezone.now()
    topup.reviewed_by = request.user
    topup.save()
    return redirect('admin_topup_list')


# ─────────────────────────────────────────────────────────
#  SELLER DASHBOARD
# ─────────────────────────────────────────────────────────

@login_required
def seller_dashboard(request):
    categories_menu = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children__children')
    categories = Category.objects.filter(parent__isnull=True)
    
    owned_docs = Document.objects.filter(seller=request.user, is_active=True)

    doc_stats = []
    for doc in owned_docs:
        stats = Purchase.objects.filter(document=doc).aggregate(
            total_revenue=Sum('seller_received'),
            total_sales=Count('id')
        )
        doc_stats.append({
            'document':      doc,
            'total_revenue': stats['total_revenue'] or Decimal('0'),
            'total_sales':   stats['total_sales']   or 0,
        })
    doc_stats.sort(key=lambda x: x['total_revenue'], reverse=True)

    total_earned = Purchase.objects.filter(
        document__seller=request.user
    ).aggregate(total=Sum('seller_received'))['total'] or Decimal('0')

    wallet = get_or_create_wallet(request.user)

    # ✅ Remove [:15] slice — Paginator handles limiting
    recent_revenues_qs = wallet.transactions.filter(
        transaction_type='revenue'
    ).order_by('-created_at')

    # ── doc_stats pagination (list, 5 per page) ──
    doc_page_num = request.GET.get('doc_page', 1)
    doc_paginator = Paginator(doc_stats, 5)
    doc_stats_page = doc_paginator.get_page(doc_page_num)

    # ── recent revenues pagination (queryset, 10 per page) ──
    rev_page_num = request.GET.get('rev_page', 1)
    rev_paginator = Paginator(recent_revenues_qs, 5)
    recent_revenues = rev_paginator.get_page(rev_page_num)

    return render(request, 'pages/seller_dashboard.html', {
        'doc_stats':       doc_stats_page,       # ✅ now a page object
        'total_earned':    total_earned,
        'wallet':          wallet,
        'recent_revenues': recent_revenues,       # ✅ now a page object
        'active_tab': 'seller',
        'categories_menu':categories_menu,
        'categories':categories,
    })
    
    
# @login_required
# def seller_dashboard(request):
#     owned_docs = Document.objects.filter(seller=request.user, is_active=True)

#     doc_stats = []
#     for doc in owned_docs:
#         stats = Purchase.objects.filter(document=doc).aggregate(
#             total_revenue=Sum('seller_received'),
#             total_sales=Count('id')
#         )
#         doc_stats.append({
#             'document':      doc,
#             'total_revenue': stats['total_revenue'] or Decimal('0'),
#             'total_sales':   stats['total_sales']   or 0,
#         })
#     doc_stats.sort(key=lambda x: x['total_revenue'], reverse=True)

#     total_earned = Purchase.objects.filter(
#         document__seller=request.user
#     ).aggregate(total=Sum('seller_received'))['total'] or Decimal('0')

#     wallet = get_or_create_wallet(request.user)
#     recent_revenues = wallet.transactions.filter(
#         transaction_type='revenue'
#     ).order_by('-created_at')[:15]

#     return render(request, 'pages/seller_dashboard.html', {
#         'doc_stats':       doc_stats,
#         'total_earned':    total_earned,
#         'wallet':          wallet,
#         'recent_revenues': recent_revenues,
#         'active_tab': 'seller',
#     })


# ─────────────────────────────────────────────────────────
#  ADMIN REVENUE DASHBOARD
# ─────────────────────────────────────────────────────────

# @user_passes_test(lambda u: u.is_staff)
# def admin_revenue_dashboard(request):
#     agg = Purchase.objects.aggregate(
#         total_gmv=Sum('amount_paid'),
#         total_platform=Sum('platform_received'),
#         total_seller=Sum('seller_received'),
#         total_transactions=Count('id'),
#     )
#     total_gmv           = agg['total_gmv']         or Decimal('0')
#     total_platform_fee  = agg['total_platform']     or Decimal('0')
#     total_seller_payout = agg['total_seller']       or Decimal('0')
#     total_transactions  = agg['total_transactions'] or 0

#     top_documents = []
#     for doc in Document.objects.filter(is_active=True):
#         stats = Purchase.objects.filter(document=doc).aggregate(
#             total_sales=Count('id'),
#             gmv=Sum('amount_paid'),
#             platform_fee=Sum('platform_received'),
#             seller_payout=Sum('seller_received'),
#         )
#         if stats['total_sales']:
#             top_documents.append({
#                 'document':      doc,
#                 'total_sales':   stats['total_sales']    or 0,
#                 'gmv':           stats['gmv']             or Decimal('0'),
#                 'platform_fee':  stats['platform_fee']    or Decimal('0'),
#                 'seller_payout': stats['seller_payout']   or Decimal('0'),
#             })
#     top_documents.sort(key=lambda x: x['gmv'], reverse=True)

#     recent_purchases = Purchase.objects.select_related(
#         'user', 'document'
#     ).order_by('-purchased_at')[:20]

#     return render(request, 'wallet/admin_revenue.html', {
#         'total_gmv':           total_gmv,
#         'total_platform_fee':  total_platform_fee,
#         'total_seller_payout': total_seller_payout,
#         'total_transactions':  total_transactions,
#         'top_documents':       top_documents,
#         'recent_purchases':    recent_purchases,
#     })
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import datetime, timedelta
import json
from wallet.models import Purchase
from documents.models import Document

@user_passes_test(lambda u: u.is_staff)
def admin_revenue_dashboard(request):
    agg = Purchase.objects.aggregate(
        total_gmv=Sum('amount_paid'),
        total_platform=Sum('platform_received'),
        total_seller=Sum('seller_received'),
        total_transactions=Count('id'),
    )
    total_gmv           = agg['total_gmv']         or Decimal('0')
    total_platform_fee  = agg['total_platform']     or Decimal('0')
    total_seller_payout = agg['total_seller']       or Decimal('0')
    total_transactions  = agg['total_transactions'] or 0

    # ✅ Daily Revenue (ทั่ว 30 วัน)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    daily_data = {}
    for day in range(31):
        date = start_date + timedelta(days=day)
        daily_data[date] = {
            'platform': 0,
            'gmv': 0,
            'seller': 0,
        }

    purchases = Purchase.objects.filter(
        purchased_at__date__gte=start_date
    ).values('purchased_at__date').annotate(
        platform=Sum('platform_received'),
        gmv=Sum('amount_paid'),
        seller=Sum('seller_received'),
    )

    for p in purchases:
        date = p['purchased_at__date']
        if date in daily_data:
            daily_data[date]['platform'] = float(p['platform'] or 0)
            daily_data[date]['gmv'] = float(p['gmv'] or 0)
            daily_data[date]['seller'] = float(p['seller'] or 0)

    labels = [d.strftime('%d/%m') for d in sorted(daily_data.keys())]
    platform_revenue = [daily_data[d]['platform'] for d in sorted(daily_data.keys())]
    gmv_revenue = [daily_data[d]['gmv'] for d in sorted(daily_data.keys())]
    seller_payout = [daily_data[d]['seller'] for d in sorted(daily_data.keys())]

    daily_revenue = {
        'labels': labels,
        'platform_revenue': platform_revenue,
        'gmv_revenue': gmv_revenue,
        'seller_payout': seller_payout,
    }

    # ✅ Top Documents (with pagination)
    top_documents_list = []
    for doc in Document.objects.filter(is_active=True):
        stats = Purchase.objects.filter(document=doc).aggregate(
            total_sales=Count('id'),
            gmv=Sum('amount_paid'),
            platform_fee=Sum('platform_received'),
            seller_payout=Sum('seller_received'),
        )
        if stats['total_sales']:
            top_documents_list.append({
                'document':      doc,
                'total_sales':   stats['total_sales']    or 0,
                'gmv':           stats['gmv']             or Decimal('0'),
                'platform_fee':  stats['platform_fee']    or Decimal('0'),
                'seller_payout': stats['seller_payout']   or Decimal('0'),
            })
    top_documents_list.sort(key=lambda x: x['gmv'], reverse=True)

    # ✅ Paginate top documents (10 per page)
    doc_page_num = request.GET.get('doc_page', 1)
    doc_paginator = Paginator(top_documents_list, 4)
    top_documents = doc_paginator.get_page(doc_page_num)

    # ✅ Recent purchases (with pagination)
    recent_purchases_qs = Purchase.objects.select_related(
        'user', 'document'
    ).order_by('-purchased_at')

    # ✅ Paginate recent purchases (15 per page)
    tx_page_num = request.GET.get('tx_page', 1)
    tx_paginator = Paginator(recent_purchases_qs, 5)
    recent_purchases = tx_paginator.get_page(tx_page_num)

    return render(request, 'wallet/admin_revenue.html', {
        'total_gmv':           total_gmv,
        'total_platform_fee':  total_platform_fee,
        'total_seller_payout': total_seller_payout,
        'total_transactions':  total_transactions,
        'top_documents':       top_documents,
        'recent_purchases':    recent_purchases,
        'daily_revenue':       json.dumps(daily_revenue),
    })
    
    
    
# ── เพิ่มใน wallet/views.py ──────────────────────────────
# อย่าลืม import WithdrawRequest ด้วย:
from .models import Wallet, TopUpRequest, Purchase, WalletTransaction, Payment_banks, WithdrawRequest

from django.db import transaction as db_transaction


# ─────────────────────────────────────────────────────────
#  SELLER: ขอถอนเงิน
# ─────────────────────────────────────────────────────────

MIN_WITHDRAW = Decimal('50000')   # ขั้นต่ำ 50,000 ກີບ


# @login_required
# def withdraw_request_view(request):
#     """Seller ยื่นคำขอถอนเงิน"""
#     wallet = get_or_create_wallet(request.user)

#     # ตรวจสอบว่า user เป็น seller (มีเอกสารขายอยู่)
#     from documents.models import Document
#     is_seller = Document.objects.filter(seller=request.user, is_active=True).exists()

#     if not is_seller:
#         messages.error(request, '❌ ສະເພາະ Seller ທີ່ມີເອກະສານຂາຍເທົ່ານັ້ນ')
#         return redirect('dashboard')

#     if request.method == 'POST':
#         amount_raw   = request.POST.get('amount', '').strip()
#         bank_name    = request.POST.get('bank_name', '').strip()
#         account_number = request.POST.get('account_number', '').strip()
#         account_name   = request.POST.get('account_name', '').strip()
#         note         = request.POST.get('note', '').strip()

#         # ── Validation ────────────────────────────────────
#         try:
#             amount = Decimal(amount_raw)
#             if amount <= 0:
#                 raise ValueError
#         except Exception:
#             messages.error(request, '❌ ຈຳນວນເງິນບໍ່ຖືກຕ້ອງ')
#             return redirect('withdraw_request')

#         if amount < MIN_WITHDRAW:
#             messages.error(request, f'❌ ຖອນຂັ້ນຕ່ຳ {MIN_WITHDRAW:,.0f} ກີບ')
#             return redirect('withdraw_request')

#         if not wallet.has_enough(amount):
#             messages.error(request, f'❌ ຍອດເງິນໃນກະເປົ໋າບໍ່ພໍ (ມີ {wallet.balance:,.0f} ກີບ)')
#             return redirect('withdraw_request')

#         if not bank_name or not account_number or not account_name:
#             messages.error(request, '❌ ກະລຸນາໃສ່ຂໍ້ມູນບັນຊີທະນາຄານໃຫ້ຄົບ')
#             return redirect('withdraw_request')

#         # ── ตรวจว่ามีคำขอ pending อยู่แล้วหรือเปล่า ──────
#         if WithdrawRequest.objects.filter(user=request.user, status='pending').exists():
#             messages.warning(request, '⚠️ ທ່ານມີຄຳຂໍຖອນເງິນທີ່ລໍຖ້າດຳເນີນການຢູ່ແລ້ວ')
#             return redirect('withdraw_request')

#         # ── หักเงินจาก wallet ทันที (จอง) ───────────────
#         with db_transaction.atomic():
#             wallet.deduct(amount)

#             withdraw = WithdrawRequest.objects.create(
#                 user=request.user,
#                 amount=amount,
#                 bank_name=bank_name,
#                 account_number=account_number,
#                 account_name=account_name,
#                 note=note,
#             )

#             WalletTransaction.objects.create(
#                 wallet=wallet,
#                 transaction_type='withdraw',
#                 amount=amount,
#                 description=f'ຖອນເງິນ → {bank_name} {account_number}',
#                 reference=str(withdraw.pk)
#             )

#         messages.success(request, f'✅ ສົ່ງຄຳຂໍຖອນເງິນ {amount:,.0f} ກີບ ແລ້ວ ລໍຖ້າ Admin ດຳເນີນການ')
#         return redirect('seller_dashboard')

#     # ประวัติคำขอถอนเงิน
#     withdraw_history = WithdrawRequest.objects.filter(
#         user=request.user
#     ).order_by('-created_at')[:10]

#     return render(request, 'wallet/withdraw_request.html', {
#         'wallet':           wallet,
#         'min_withdraw':     MIN_WITHDRAW,
#         'withdraw_history': withdraw_history,
#         'active_tab':       'withdraw',
#     })

from django.db.models import Sum
from decimal import Decimal

@login_required
def withdraw_request_view(request):
    categories_menu = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children__children')
    categories = Category.objects.filter(parent__isnull=True)
    
    wallet = get_or_create_wallet(request.user)

    from documents.models import Document
    is_seller = Document.objects.filter(
        seller=request.user,
        is_active=True
    ).exists()

    if not is_seller:
        messages.warning(request,'📄 ກະລຸນາອັບໂຫຼດເອກະສານກ່ອນ ເພື່ອໃຊ້ງານລະບົບຖອນເງິນ')
        return redirect('dashboard')

    # ✅ รายได้ทั้งหมด
    revenue_total = Purchase.objects.filter(
        document__seller=request.user
    ).aggregate(total=Sum('seller_received'))['total'] or Decimal('0')

    # ✅ ถอนแล้ว
    withdrawn_total = WalletTransaction.objects.filter(
        wallet=wallet,
        transaction_type='withdraw'
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    # ✅ เงินที่ถอนได้จริง
    withdrawable = revenue_total - withdrawn_total

    # 🔥 กันติดลบ
    if withdrawable < 0:
        withdrawable = Decimal('0')

    # 🔥 กัน mismatch กับ wallet จริง
    withdrawable = min(wallet.balance, withdrawable)

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
        except:
            messages.error(request, '❌ invalid amount')
            return redirect('withdraw_request')

        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        account_name = request.POST.get('account_name')
        note = request.POST.get('note')
        qrcode_image = request.FILES.get('qrcode_image')

        # ✅ validation
        if amount <= 0:
            messages.error(request, '❌ amount invalid')
            return redirect('withdraw_request')

        if amount < MIN_WITHDRAW:
            messages.error(request, f'❌ min {MIN_WITHDRAW}')
            return redirect('withdraw_request')

        if amount > withdrawable:
            messages.error(request, f'❌ max {withdrawable}')
            return redirect('withdraw_request')

        if not all([bank_name, account_number, account_name]):
            messages.error(request, '❌ bank info required')
            return redirect('withdraw_request')

        if WithdrawRequest.objects.filter(
            user=request.user,
            status='pending'
        ).exists():
            messages.warning(request, '⚠️ pending exists')
            return redirect('withdraw_request')

        # 🔥 LOCK + DOUBLE CHECK
        with transaction.atomic():
            wallet_locked = Wallet.objects.select_for_update().get(user=request.user)

            # Re-check pending withdrawal inside the lock to avoid double-submit
            if WithdrawRequest.objects.filter(user=request.user, status='pending').exists():
                messages.warning(request, '⚠️ pending exists')
                return redirect('withdraw_request')

            if wallet_locked.balance < amount:
                messages.error(request, '❌ insufficient balance')
                return redirect('withdraw_request')

            # ✅ หักเงินจริง
            wallet_locked.balance -= amount
            wallet_locked.save()

            withdraw = WithdrawRequest.objects.create(
                user=request.user,
                amount=amount,
                bank_name=bank_name,
                account_number=account_number,
                account_name=account_name,
                qrcode_image=qrcode_image,
                note=note,
                status='pending'
            )
            # if qrcode_image:
            #     withdraw.qrcode_image = qrcode_image  # ── ໃໝ່
            #     withdraw.save()

            
            WalletTransaction.objects.create(
                wallet=wallet_locked,
                transaction_type='withdraw',
                amount=amount,
                description=f'Withdraw request #{withdraw.id}',
                reference=str(withdraw.id)
            )

        messages.success(request, f'✅ Withdraw {amount:,.0f}')
        return redirect('seller_dashboard')

    # withdraw_history = WithdrawRequest.objects.filter(
    #     user=request.user
    # ).order_by('-created_at')[:10]
    withdraw_history_qs = WithdrawRequest.objects.filter(
    user=request.user
    ).order_by('-created_at')

    paginator = Paginator(withdraw_history_qs, 5)
    page_number = request.GET.get('page', 1)
    withdraw_history = paginator.get_page(page_number)

    
    
    return render(request, 'pages/withdraw_request.html', {
    'wallet': wallet,
    'withdrawable': withdrawable,
    'min_withdraw': MIN_WITHDRAW,
    'withdraw_history': withdraw_history,
    'revenue_total': revenue_total,
    'withdrawn_total': withdrawn_total,
    'active_tab': 'withdraw_request',
    'categories_menu':categories_menu,
    'categories':categories,
})
# ─────────────────────────────────────────────────────────
#  ADMIN: รายการคำขอถอนเงิน
# ─────────────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_superuser)
def admin_withdraw_list(request):
    pending  = WithdrawRequest.objects.filter(status='pending').order_by('-created_at')

    approved_qs = WithdrawRequest.objects.filter(status='approved').order_by('-reviewed_at')
    approved_paginator = Paginator(approved_qs, 10)
    approved = approved_paginator.get_page(request.GET.get('approved_page', 1))

    rejected_qs = WithdrawRequest.objects.filter(status='rejected').order_by('-reviewed_at')
    rejected_paginator = Paginator(rejected_qs, 10)
    rejected = rejected_paginator.get_page(request.GET.get('rejected_page', 1))

    return render(request, 'wallet/admin_withdraw_list.html', {
        'pending':  pending,
        'approved': approved,
        'rejected': rejected,
    })
# @user_passes_test(lambda u: u.is_superuser)
# def admin_withdraw_list(request):
#     pending  = WithdrawRequest.objects.filter(status='pending').order_by('-created_at')
#     approved = WithdrawRequest.objects.filter(status='approved').order_by('-reviewed_at')[:20]
#     rejected = WithdrawRequest.objects.filter(status='rejected').order_by('-reviewed_at')[:10]
#     return render(request, 'wallet/admin_withdraw_list.html', {
#         'pending':  pending,
#         'approved': approved,
#         'rejected': rejected,
#     })


# @user_passes_test(lambda u: u.is_superuser)
# @require_POST
# @transaction.atomic
# def admin_withdraw_approve(request, pk):
#     """Admin อนุมัติ หรือ ปฏิเสธคำขอถอนเงิน"""
#     if request.method != 'POST':
#         return redirect('admin_withdraw_list')

#     try:
#         withdraw = WithdrawRequest.objects.select_for_update().get(pk=pk, status='pending')
#     except WithdrawRequest.DoesNotExist:
#         messages.warning(request, '⚠️ ຄຳຂໍນີ້ຖືກຈັດການແລ້ວ')
#         return redirect('admin_withdraw_list')

#     action   = request.POST.get('action')

#     if action == 'approve':
#         # เงินถูกหักไปแล้วตอน seller ยื่นคำขอ — Admin แค่ยืนยัน
#         withdraw.status     = 'approved'
#         withdraw.slip_image = request.FILES.get('slip_image')
#         messages.success(request, f'✅ ອະນຸມັດການຖອນເງິນ {withdraw.amount:,} ກີບ ໃຫ້ {withdraw.user.username}')

#     elif action == 'reject':
#         # คืนเงินให้ seller — lock wallet and withdraw row to avoid double-refund
#         try:
#             wallet = Wallet.objects.select_for_update().get(user=withdraw.user)
#         except Wallet.DoesNotExist:
#             wallet = Wallet.objects.create(user=withdraw.user, balance=Decimal('0'))
#         wallet.deposit(withdraw.amount)
#         WalletTransaction.objects.create(
#             wallet=wallet,
#             transaction_type='topup',
#             amount=withdraw.amount,
#             description=f'ຄືນເງິນ: ຄຳຂໍຖອນ #{withdraw.pk} ຖືກປະຕິເສດ',
#             reference=str(withdraw.pk)
#         )
#         withdraw.status = 'rejected'
#         messages.warning(request, f'⚠️ ປະຕິເສດ ແລະ ຄືນເງິນ {withdraw.amount:,} ກີບ ໃຫ້ {withdraw.user.username}')

#     withdraw.reviewed_at = timezone.now()
#     withdraw.reviewed_by = request.user
#     withdraw.save()
#     return redirect('admin_withdraw_list')

@user_passes_test(lambda u: u.is_superuser)
@require_POST
@transaction.atomic
def admin_withdraw_approve(request, pk):
    try:
        withdraw = WithdrawRequest.objects.select_for_update().get(pk=pk, status='pending')
    except WithdrawRequest.DoesNotExist:
        messages.warning(request, '⚠️ ຄຳຂໍນີ້ຖືກຈັດການແລ້ວ')
        return redirect('admin_withdraw_list')

    action = request.POST.get('action')

    if action == 'approve':
        withdraw.status = 'approved'

        # ✅ อัปเดต slip_image เฉพาะเมื่อมีไฟล์แนบมาจริงๆ
        slip_file = request.FILES.get('slip_image')
        if slip_file:
            withdraw.slip_image = slip_file

        messages.success(request, f'✅ ອະນຸມັດການຖອນເງິນ {withdraw.amount:,} ກີບ ໃຫ້ {withdraw.user.username}')

    elif action == 'reject':
        try:
            wallet = Wallet.objects.select_for_update().get(user=withdraw.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=withdraw.user, balance=Decimal('0'))

        wallet.deposit(withdraw.amount)

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='topup',
            amount=withdraw.amount,
            description=f'ຄືນເງິນ: ຄຳຂໍຖອນ #{withdraw.pk} ຖືກປະຕິເສດ',
            reference=str(withdraw.pk)
        )
        withdraw.status = 'rejected'
        messages.warning(request, f'⚠️ ປະຕິເສດ ແລະ ຄືນເງິນ {withdraw.amount:,} ກີບ ໃຫ້ {withdraw.user.username}')

    withdraw.reviewed_at = timezone.now()
    withdraw.reviewed_by = request.user
    withdraw.save()
    return redirect('admin_withdraw_list')


# @login_required
# def My_documrnt(request):

#     # เอกสารที่ user อัปโหลด
#     my_uploads = Document.objects.filter(
#         seller=request.user
#     ).order_by('-created_at')

#     # เอกสารที่ user ซื้อ
#     purchased_items = Purchase.objects.filter(
#         user=request.user
#     ).select_related('document').order_by('-purchased_at')

#     # สถิติ
#     total_uploads = my_uploads.count()

#     total_downloads = sum(
#         d.downloads for d in my_uploads
#     )

#     total_purchased = purchased_items.count()

#     total_earned = Purchase.objects.filter(
#         document__seller=request.user
#     ).aggregate(
#         total=Sum('seller_received')
#     )['total'] or Decimal('0')

#     context = {
#         'my_uploads': my_uploads,
#         'purchased_items': purchased_items,
#         'total_uploads': total_uploads,
#         'total_downloads': total_downloads,
#         'total_purchased': total_purchased,
#         'total_earned': total_earned,
#         'active_tab': request.GET.get('tab', 'uploads'),
#     }

#     return render(
#         request,
#         'pages/my_documents.html',
#         context
#     )


from django.db.models import Sum
from wallet.models import Purchase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def My_documrnt(request):

    my_uploads_qs = Document.objects.filter(
        seller=request.user
    ).order_by('-created_at')

    purchased_qs = Purchase.objects.filter(
        user=request.user
    ).select_related('document').order_by('-purchased_at')

    # --- Uploads pagination (5 per page) ---
    upload_page_num = request.GET.get('upload_page', 1)
    upload_paginator = Paginator(my_uploads_qs, 3)
    my_uploads = upload_paginator.get_page(upload_page_num)

    # --- Purchased pagination (5 per page) ---
    purchase_page_num = request.GET.get('purchase_page', 1)
    purchase_paginator = Paginator(purchased_qs, 3)
    purchased_items = purchase_paginator.get_page(purchase_page_num)

    # Annotate downloads_remaining on the current page only
    for item in purchased_items:
        item.downloads_remaining = (
            item.MAX_DOWNLOADS - item.download_count
        )

    # Totals still come from the full querysets
    total_uploads   = my_uploads_qs.count()
    total_downloads = sum(d.downloads for d in my_uploads_qs)
    total_purchased = purchased_qs.count()
    total_earned = Purchase.objects.filter(
        document__seller=request.user
    ).aggregate(total=Sum('seller_received'))['total'] or 0

    context = {
        'my_uploads': my_uploads,
        'purchased_items': purchased_items,
        'total_uploads': total_uploads,
        'total_downloads': total_downloads,
        'total_purchased': total_purchased,
        'total_earned': total_earned,
        'active_tab': 'my-documents',
    }

    return render(request, 'pages/my_documents.html', context)



# ─────────────────────────────────────────────
# UPDATE DOCUMENT
# ─────────────────────────────────────────────

@login_required
def update_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, seller=request.user)
    categories = Category.objects.filter(parent__isnull=True)

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        pages       = request.POST.get('pages')
        price_type  = request.POST.get('price_type', 'paid')
        price       = request.POST.get('price', 0)
        cat_id      = request.POST.get('level3') or request.POST.get('level2') or request.POST.get('level1')

        if len(title) < 1:
            messages.error(request, 'ຊື່ເອກະສານຕ້ອງມີຢ່າງໜ້ອຍ 1 ຕົວອັກສອນ')
            return redirect('update_document', doc_id=doc_id)

        doc.title       = title
        doc.description = description
        doc.pages       = pages or doc.pages
        doc.price       = 0 if price_type == 'free' else (int(float(price)) if price else doc.price)

        if cat_id:
            try:
                doc.category = Category.objects.get(id=cat_id)
            except Category.DoesNotExist:
                pass

        new_file = request.FILES.get('file')
        if new_file:
            doc.file = new_file

        new_preview = request.FILES.get('preview_file')
        if new_preview:
            doc.preview_file = new_preview

        new_image = request.FILES.get('preview_image')
        if new_image:
            doc.preview_image = new_image

        new_zip = request.FILES.get('attached_file')
        if new_zip:
            doc.attached_file = new_zip

        attach_name = request.POST.get('name_attached_file', '').strip()
        if attach_name:
            doc.name_attached_file = attach_name

        doc.save()
        messages.success(request, '✅ ອັບເດດເອກະສານສຳເລັດແລ້ວ!')
        return redirect('my-documents')

    # ── GET: build category chain for pre-selecting dropdowns ──
    ids = [None, None, None]
    cat = doc.category
    if cat:
        chain = []
        node = cat
        while node:
            chain.append(node)
            node = node.parent
        chain.reverse()  # [root, child, grandchild]
        for i, node in enumerate(chain[:3]):
            ids[i] = node.id

    context = {
        'doc': doc,
        'categories': categories,
        'active_tab': 'my-documents',
        'current_category_chain': json.dumps(ids),
    }
    return render(request, 'pages/update_document.html', context)


# ─────────────────────────────────────────────
# DELETE DOCUMENT
# ─────────────────────────────────────────────
@login_required
def delete_document(request, doc_id):
    """Delete the seller's own document (POST only for safety)."""
    doc = get_object_or_404(Document, id=doc_id, seller=request.user)

    if request.method == 'POST':
        doc.delete()
        messages.success(request, '🗑️ ລຶບເອກະສານສຳເລັດແລ້ວ!')
        return redirect('my-documents')

    # GET → show a simple confirm page
    return render(request, 'pages/delete_document_confirm.html', {
        'doc': doc,
        'active_tab': 'my-documents',
    })
    

