# from django.shortcuts import render, redirect
# from django.contrib import auth, messages
# from django.contrib.auth import authenticate, login
# from .forms import LoginForm, SignUpForm
# from category.models import Category
 
 
# def login_view(request):
#     categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')
 
#     # ✅ ส่ง request= เข้า LoginForm เพื่อให้ authenticate ใน clean() ทำงานได้
#     form = LoginForm(request=request, data=request.POST or None)
 
#     if request.method == "POST":
#         if form.is_valid():
#             user = form.get_user()   # ✅ ไม่ต้อง authenticate ซ้ำ — form จัดการแล้ว
#             login(request, user)
#             return redirect("/")
#         # ❌ ลบ msg ออก — error อยู่ใน form.non_field_errors แล้ว
 
#     context = {
#         'form': form,
#         'categories': categories,
#     }
#     return render(request, "accounts/login.html", context)
 
 
def register_user(request):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children__children')

    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            msg = 'User created successfully!'
            success = True
            return redirect("/")
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    context = {
        'form': form,
        'msg': msg,
        'success': success,
        'categories': categories,
    }
    return render(request, "accounts/register.html", context)


# def logout(request):
#     auth.logout(request)
#     messages.success(request, 'You are now logged out.')    # ✅ ใช้งานได้แล้ว
#     return redirect('home')


import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import LoginForm, SignUpForm
from .models import EmailVerificationToken
from category.models import Category
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django_ratelimit.decorators import ratelimit

# ✅ Rate limit: 5 login attempts per hour per IP
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def login_view(request):
    categories = Category.objects.filter(
        parent__isnull=True
    ).prefetch_related('children__children')

    form = LoginForm(request=request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, '❌ ກະລຸນາຢືນຢັນອີເມວກ່ອນເຂົ້າສູ່ລະບົບ')
                return redirect('login_view')
            login(request, user)
            return redirect("/")

    return render(request, "accounts/login.html", {'form': form, 'categories': categories})


# def register_user(request):
#     categories = Category.objects.filter(
#         parent__isnull=True
#     ).prefetch_related('children__children')

#     if request.method == "POST":
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             # ✅ ສ້າງ user ແຕ່ປິດການໃຊ້ງານກ່ອນ
#             user = form.save(commit=False)
#             user.is_active = False
#             user.save()

#             token_obj = EmailVerificationToken.objects.create(user=user)
#             activate_url = f"{settings.SITE_URL}/accounts/activate/{token_obj.token}/"

#             # ✅ ใช้ HTML email
#             html_message = render_to_string('accounts/email_verification.html', {
#                 'username': user.username,
#                 'activate_url': activate_url,
#             })
#             plain_message = strip_tags(html_message)

#             send_mail(
#                 subject='✅ ຢືນຢັນອີເມວຂອງທ່ານ - Duladoc',
#                 message=plain_message,
#                 html_message=html_message,  # ✅ เพิ่ม HTML
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[user.email],
#                 fail_silently=False,
#             )
#             # ✅ ส่ง email ไปให้ verify page
#             return render(request, 'accounts/verify_email.html', {
#                 'email': user.email,
#                 'categories': categories,
#             })
#             # messages.success(
#             #     request,
#             #     f'✅ ສົ່ງລິ້ງຢືນຢັນໄປທີ່ {user.email} ແລ້ວ ກະລຸນາກວດເບິ່ງອີເມວ'
#             # )
#         else:
#             messages.error(request, '❌ ກະລຸນາກວດສອບຂໍ້ມູນ')
#     else:
#         form = SignUpForm()

#     return render(request, "accounts/register.html", {
#         'form': form,
#         'categories': categories,
#     })



# def activate_account(request, token):
#     # ✅ แปลง string กลับเป็น UUID
#     try:
#         token_uuid = uuid.UUID(token)
#     except ValueError:
#         messages.error(request, '❌ ລິ້ງບໍ່ຖືກຕ້ອງ')
#         return redirect('login_view')
    
#     # ✅ หา token ใน database
#     token_obj = get_object_or_404(EmailVerificationToken, token=token_uuid)
#     user = token_obj.user

#     if user.is_active:
#         messages.info(request, '✅ ບັນຊີນີ້ຢືນຢັນແລ້ວ')
#         return redirect('login_view')

#     # ✅ เปิดใช้งาน account
#     user.is_active = True
#     user.save()

#     # ✅ ลบ token ที่ใช้แล้ว
#     token_obj.delete()

#     messages.success(request, '✅ ຢືນຢັນສຳເລັດ! ສາມາດເຂົ້າສູ່ລະບົບໄດ້ເລີຍ')
#     return redirect('login_view')


def logout(request):
    auth.logout(request)
    messages.success(request, 'You are now logged out.')
    return redirect('home')