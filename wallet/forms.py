from django import forms
from .models import TopUpRequest


class TopUpRequestForm(forms.ModelForm):
    class Meta:
        model = TopUpRequest
        fields = ['amount', 'slip_image', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'step': '1',
                'placeholder': 'ເຊັ່ນ: 500000',
            }),
            'slip_image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
                'id': 'slip_image_input',
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'ເຊັ່ນ: ໂອນຈາກບັນຊີທະນາຄານ BCEL ເວລາ 14:30',
            }),
        }
        labels = {
            'amount': 'ຈຳນວນເງນທີ່ຕ້ອງການຕື່ມ (KIP)',
            'slip_image': 'ແນບສະຣິບການໂອນເງິນ',
            'note': 'ໝາຍເຫດເພິ່ມຕື່ມ (ບໍ່ບັງຄັບ)',
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_slip_image(self):
        image = self.cleaned_data.get('slip_image')
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Slip image is too large. Max size is 5MB.")
        return image
