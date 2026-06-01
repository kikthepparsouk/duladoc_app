from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from documents.models import Document
from django.utils import timezone


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.balance} ฿"

    def has_enough(self, amount):
        return self.balance >= amount

    def deduct(self, amount):
        if not self.has_enough(amount):
            raise ValidationError("ຍອກເງິນບໍ່ພຽງພໍ")
        self.balance -= amount
        self.save()
        
    # ✅ เพิ่ม method นี้
    def deposit(self, amount):
        self.balance += Decimal(str(amount))
        self.save()


class TopUpRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'ລໍຖ້າກວດສອບ'),
        ('approved', 'ອະນຸມັດ'),
        ('rejected', 'ປະຕິເສດ'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topup_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    slip_image = models.ImageField(upload_to='slips/%Y/%m/')
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_topups'
    )

    def __str__(self):
        return f"{self.user.username} - {self.amount}฿ ({self.get_status_display()})"


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='purchases')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2) 
    
    # บันทึกว่าแบ่งเงินอย่างไร
    seller_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    purchased_at = models.DateTimeField(auto_now_add=True)
    download_count = models.IntegerField(default=0)  # ✅ Add this
    
    MAX_DOWNLOADS = 5  # ✅ Add this constant
    

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['user', 'document'],
    #             name='unique_user_document_purchase'
    #         )
    #     ]

    def has_downloads_remaining(self):
        return self.download_count < self.MAX_DOWNLOADS
    
    def downloads_remaining(self):
        return max(0, self.MAX_DOWNLOADS - self.download_count)
    
    def __str__(self):
        return f"{self.user.username} ຊື້ {self.document.title}"


# class PurchaseRecord(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
#     document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='purchases')
#     amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
#     # บันทึกว่าแบ่งเงินอย่างไร
#     seller_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     platform_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     purchased_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'document')

#     def __str__(self):
#         return f"{self.user.username} ซื้อ {self.document.title}"
    
    
    
# class WalletTransaction(models.Model):
#     TYPE_CHOICES = [
#         ('topup', 'ຕື່ມເງິນ'),
#         ('purchase', 'ຊື້ເອກະສານ'),
#     ]
#     wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
#     transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     description = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)
#     reference = models.CharField(max_length=100, blank=True)
    
    
class Payment_banks(models.Model):
    name_banks = models.CharField(max_length=255)
    name_account = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=255, blank=True, null=True)
    image_qrccode = models.ImageField(upload_to='wallet/qr_code/%Y/%m/')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    is_active = models.BooleanField(default=True)
    
    
    def __str__(self):
        return self.name_banks
    
       
    
# ── เพิ่มใน wallet/models.py ──────────────────────────────

# 1. เพิ่ม TYPE_CHOICES ใน WalletTransaction ให้รองรับ withdraw
class WalletTransaction(models.Model):
    TYPE_CHOICES = [
        ('topup',        'ຕື່ມເງິນ'),
        ('purchase',     'ຊື້ເອກະສານ'),
        ('revenue',      'ລາຍໄດ້ຈາກການຂາຍ'),      # ← เพิ่ม
        ('platform_fee', 'ຄ່າທຳນຽມລະບົບ'),          # ← เพิ่ม
        ('withdraw',     'ຖອນເງິນ'),                # ← เพิ่ม
    ]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    image_qrcode=models.ImageField(upload_to='wallet/qr_codeuser_withdraw/%Y/%m/',blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True)


class WithdrawRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'ລໍຖ້າດຳເນີນການ'),
        ('approved', 'ອະນຸມັດແລ້ວ'),
        ('rejected', 'ປະຕິເສດ'),
    ]

    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdraw_requests')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    bank_name      = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_name   = models.CharField(max_length=100)
    note           = models.TextField(blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at     = models.DateTimeField(auto_now_add=True)
    reviewed_at    = models.DateTimeField(null=True, blank=True)
    reviewed_by    = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_withdrawals'
    )
    slip_image     = models.ImageField(upload_to='withdraw_slips/%Y/%m/', null=True, blank=True)

    # ── ໃໝ່: QR Code ຂອງບັນຊີທະນາຄານ ──
    qrcode_image   = models.ImageField(
        upload_to='withdraw_qrcodes/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='QR Code ບັນຊີທະນາຄານ',
        help_text='ອັບໂຫລດ QR Code ຂອງບັນຊີທະນາຄານທີ່ຈະຮັບເງິນ'
    )

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.get_status_display()})"