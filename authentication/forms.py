from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    username = forms.CharField(
        label=_("ຊື່ຜູ້ໃຊ້"),
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "ຊື່ຜູ້ໃຊ້",
            "class": "form-control",
            "autofocus": True,
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        label=_("ລະຫັດຜ່ານ"),
        widget=forms.PasswordInput(attrs={
            "placeholder": "ລະຫັດຜ່ານ",
            "class": "form-control",
            "autocomplete": "current-password",
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if not username or not password:
            raise forms.ValidationError(_("ກະລຸນາປ້ອນຊື່ຜູ້ໃຊ້ ແລະ ລະຫັດຜ່ານ"))

        # authenticate ใน clean — เพื่อ raise error ได้ทันที
        self._user = authenticate(
            request=self.request,
            username=username,
            password=password,
        )

        if self._user is None:
            raise forms.ValidationError(_("ຊື່ຜູ້ໃຊ້ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ"))

        if not self._user.is_active:
            raise forms.ValidationError(_("ບັນຊີນີ້ຖືກລະງັບການໃຊ້ງານ"))

        return cleaned_data

    def get_user(self):
        """ใช้ใน views.py แทนการ authenticate ซ้ำ"""
        return self._user
    
    


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "ຊື່ຜູ້ໃຊ້",
            "class": "form-control"
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": "ອີເມວ",
            "class": "form-control"
        })
    )
    password1 = forms.CharField(
        label="ລະຫັດຜ່ານ",
        widget=forms.PasswordInput(attrs={
            "placeholder": "ລະຫັດຜ່ານ",
            "class": "form-control"
        })
    )
    password2 = forms.CharField(
        label="ຢືນຢັນລະຫັດຜ່ານ",
        widget=forms.PasswordInput(attrs={
            "placeholder": "ຢືນຢັນລະຫັດຜ່ານ",
            "class": "form-control"
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("ຊື່ຜູ້ໃຊ້ນີ້ ໄດ້ຖືກນຳໃຊ້ແລ້ວ")
        
        return username

    def clean_password1(self):
        """ตรวจสอบ password และแสดง error ภาษาลาວ"""
        password1 = self.cleaned_data.get("password1")
        try:
            validate_password(password1, self.instance)
        except ValidationError:
            errors = []
            if len(password1) < 8:
                errors.append("ລະຫັດຜ່ານສັ້ນເກີນໄປ ຕ້ອງມີຢ່າງໜ້ອຍ 8 ຕົວອັກສອນ")
            if password1.isnumeric():
                errors.append("ລະຫັດຜ່ານຕ້ອງບໍ່ເປັນຕົວເລກທັງໝົດ")
            if len(password1) >= 8 and not password1.isnumeric():
                errors.append("ລະຫັດຜ່ານງ່າຍເກີນໄປ ກະລຸນາໃຊ້ລະຫັດທີ່ຊັບຊ້ອນກວ່ານີ້")
            raise ValidationError(errors)
        return password1
    
    def clean_password2(self):
        """ตรวจสอบ password และแสดง error ภาษาลาວ"""
        password2 = self.cleaned_data.get("password2")
        try:
            validate_password(password2, self.instance)
        except ValidationError:
            errors = []
            if len(password2) < 8:
                errors.append("ລະຫັດຜ່ານສັ້ນເກີນໄປ ຕ້ອງມີຢ່າງໜ້ອຍ 8 ຕົວອັກສອນ")
            if password2.isnumeric():
                errors.append("ລະຫັດຜ່ານຕ້ອງບໍ່ເປັນຕົວເລກທັງໝົດ")
            if len(password2) >= 8 and not password2.isnumeric():
                errors.append("ລະຫັດຜ່ານງ່າຍເກີນໄປ ກະລຸນາໃຊ້ລະຫັດທີ່ຊັບຊ້ອນກວ່ານີ້")
            raise ValidationError(errors)
        return password2

    # ✅ ลบ clean_password2 ออกทั้งหมด — Django จัดการ confirm เองอยู่แล้ว

    def clean(self):
        """ตรวจสอบว่า password1 และ password2 ตรงกัน"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "ລະຫັດຜ່ານທັງສອງບໍ່ກົງກັນ")

        # ✅ ลบ mapping password/re_password ออก — ไม่มี field เหล่านั้น
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("ອີເມວນີ້ໄດ້ຖືກນຳໃຊ້ແລ້ວ")
        return email
    
    
    

# class SignUpForm(UserCreationForm):
#     username = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "placeholder": "Username",
#                 "class": "form-control"
#             }
#         ))
#     email = forms.EmailField(
#         widget=forms.EmailInput(
#             attrs={
#                 "placeholder": "Email",
#                 "class": "form-control"
#             }
#         ))
#     password = forms.CharField(
#         widget=forms.PasswordInput(
#             attrs={
#                 "placeholder": "Password",
#                 "class": "form-control"
#             }
#         ))
#     re_password = forms.CharField(
#         widget=forms.PasswordInput(
#             attrs={
#                 "placeholder": "Password confirmation",
#                 "class": "form-control"
#             }
#         ))

#     class Meta:
#         model = User
#         fields = ('username', 'email')
        
        
#     def clean(self):
#         cleaned_data = super().clean()
#         cleaned_data['password1'] = cleaned_data.get('password')
#         cleaned_data['password2'] = cleaned_data.get('re_password')
#         return cleaned_data


