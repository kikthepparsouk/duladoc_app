from django.contrib import admin
from .models import Wallet, TopUpRequest, Document, Purchase, WalletTransaction, Payment_banks,WithdrawRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'updated_at']
    # search_fields = ['user__username']
    readonly_fields = ['updated_at']


@admin.register(TopUpRequest)
class TopUpRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status']
    # search_fields = ['user__username']
    readonly_fields = ['created_at', 'reviewed_at']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'document', 'amount_paid', 'purchased_at']
    # search_fields = ['user__username', 'document__title']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type']
    readonly_fields = ['created_at']
    
    
@admin.register(Payment_banks)
class PaymentBankAdmin(admin.ModelAdmin):
    list_display = ['name_banks','name_account','image_qrccode','created_at','updated_at']
    
    
@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    # ✅ ใช้ fields ของ WithdrawRequest ไม่ใช่ Payment_banks
    list_display = ['user', 'amount', 'bank_name', 'account_number', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'bank_name', 'account_number']
    readonly_fields = ['created_at', 'reviewed_at']
    
    