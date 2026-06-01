from django import forms
from .models import Document,WorkDocument
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import ContactMessage




class DocumentForm(forms.ModelForm):

    class Meta:
        model = Document
        fields = [
            'title', 'description', 'category',
            'price', 'file','pages', 'attached_file', 'name_attached_file','preview_file', 'preview_image'
        ]

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Price cannot be negative")
        return price

    def clean_category(self):
        category = self.cleaned_data.get('category')

        if category:
            # ⭐ ตรวจสอบว่าเป็น leaf หรือไม่
            if category.children.exists():
                raise forms.ValidationError(
                    "Please select the lowest level category."
                )

        return category


from .models import WorkDocument, Category
from datetime import date

class WorkDocumentForm(forms.ModelForm):
    
    class Meta:
        model = WorkDocument
        fields = [
            'title', 'category', 'job_type', 'budget', 
            'deadline', 'contact_info', 'description', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Web Developer Needed'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5000000',
                'step': '0.01'
            }),
            'contact_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone: 020XXXXXXXX or Email: example@email.com'
            }),
            'status': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': CKEditorUploadingWidget(attrs={
                'class': 'form-control',
                'placeholder': 'Provide detailed information about the job requirements'
            }),

        }
        labels = {
            'title': 'ຊື່ວຽກ (Job Title)',
            'category': 'ໝວດໝູ່ (Category)',
            'job_type': 'ລັກສະນະຈ້າງ (Job Type)',
            'budget': 'ງົບປະມານ (Budget - KIP)',
            'deadline': 'ສົ່ງວຽກພາຍໃນ (Deadline)',
            'contact_info': 'ຕິດຕໍ່ເຈົ້າຂອງວຽກ (Contact Info)',
            'description': 'ລາຍລະອຽດວຽກ (Description)',
            'status': 'ສະຖານະ (Status)'
        }
        help_texts = {
            'budget': 'ກະລຸນາປ້ອນງົບປະມານເປັນກີບ (Please enter budget in KIP)',
            'contact_info': 'ກະລຸນາໃສ່ຂໍ້ມູນຕິດຕໍ່ (Please provide contact information)',
            'status': 'ເປີດຮັບສະໝັກ (Open for applications)'
        }
    
    def clean_budget(self):
        """Validate budget is positive"""
        budget = self.cleaned_data.get('budget')
        if budget <= 0:
            raise forms.ValidationError("ງົບປະມານຕ້ອງຫຼາຍກວ່າ 0 (Budget must be greater than 0)")
        return budget
    
    def clean_deadline(self):
        """Validate deadline is not in the past"""
        deadline = self.cleaned_data.get('deadline')
        if deadline < date.today():
            raise forms.ValidationError("ວັນສົ່ງວຽກບໍ່ສາມາດຜ່ານມາແລ້ວ (Deadline cannot be in the past)")
        return deadline
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom classes and attributes
        for field in self.fields:
            if field not in ['description', 'status', 'deadline']:
                self.fields[field].widget.attrs['class'] = 'form-control'
                
        # Filter category to only popular root categories
        self.fields['category'].queryset = Category.objects.filter(
            is_popular_category=True
        )
        

class WorkDocumentSearchForm(forms.Form):
    """Form for searching/filtering jobs"""
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    job_type = forms.ChoiceField(
        choices=[('', 'All')] + WorkDocument.JOB_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_budget = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Budget'
        })
    )
    max_budget = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Budget'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Open'), ('false', 'Closed')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    



from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage

        fields = [
            'name',
            'email',
            'telephone',
            'subject',
            'message'
        ]

        widgets = {

            'name': forms.TextInput(attrs={
                'placeholder': 'ຊື່ ແລະ ນາມສະກຸນ:',
            }),

            'email': forms.EmailInput(attrs={
                'placeholder': 'Email:',
            }),

            'telephone': forms.TextInput(attrs={
                'placeholder': 'ເບີໂທລະສັບ:',
            }),

            'subject': forms.TextInput(attrs={
                'placeholder': 'ຫົວຂໍ້:',
            }),

            'message': forms.Textarea(attrs={
                'placeholder': 'ຂໍ້ຄວາມ...',
                'rows': 5,
            }),

        }