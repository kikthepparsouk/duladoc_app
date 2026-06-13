from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from category.models import Category
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.
import os
from django.core.validators import MinValueValidator, MaxValueValidator
from .services.image_compression import compress_image

# Model สำหรับแบนเนอร์ในหน้าแรก
class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    subtitle2 = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='banners/')
    button_text = models.CharField(max_length=100, default="Learn More")
    button_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    
# Model สำหรับแบนเนอร์ในหน้าแรก
class SmallBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle_one = models.CharField(max_length=200, blank=True)
    subtitle_two = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='small_banners/')
    button_text = models.CharField(max_length=100, default="Shop Now")
    button_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

def validate_file_size(value):
    limit = 100 * 1024 * 1024  # 20 MB
    if value.size > limit:
        raise ValidationError('File too large. Max size is 100MB.')


class Document(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_documents', db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    slug = models.SlugField(unique=True, null=True, blank=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='documents', db_index=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf', 'doc', 'docx', 'ppt', 'txt',
                    'pptx', 'pot', 'potx', 'xls',
                    'xlsx', 'pps', 'ppsx','pub'
                ]  
            ),
            validate_file_size
        ]
    )
    pages = models.IntegerField(default=0)

    preview_file = models.FileField(
        upload_to='previews/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    
    preview_image = models.ImageField(
    upload_to='preview_images/%Y/%m/%d/',
    null=True,
    blank=True
    )

    
    attached_file = models.FileField(
        upload_to='attached_files/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['zip', 'rar'])]
    )
    
    # % ที่เจ้าของได้รับ (0.00 - 1.00)  เช่น 0.80 = 80%
    seller_revenue_rate = models.DecimalField(
        max_digits=4, decimal_places=2,
        default=Decimal('0.80'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        help_text='ສ່ວນທີ່ເຈົ້າຂອງເອກກະສານຈະໄດ້ຮັບເຊັ່ນ 0.80 = 80%'
    )

    
    name_attached_file = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_featured_book = models.BooleanField(default=False, db_index=True)
    is_popular_book = models.BooleanField(default=False, db_index=True)
    is_new_book = models.BooleanField(default=False, db_index=True)
    
    downloads = models.PositiveIntegerField(default=0)  # นับจำนวนดาวน์โหลด
    preview_count = models.PositiveIntegerField(default=0)      # นับจำนวนการ preview

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['is_featured_book', 'is_active']),
            models.Index(fields=['is_popular_book', 'is_active']),
            models.Index(fields=['is_new_book', 'is_active']),
        ]

    @property
    def is_free(self):
        return self.price == 0

    @property
    def is_paid(self):
        return self.price > 0

    def is_pdf(self):
        return self.file.name.lower().endswith('.pdf')


    
    
    def get_file_type(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower().replace('.', '')
    
    
    def get_file_icon(self):
        ext = self.get_file_type()

        if ext == 'pdf':
            return 'pdf.png'
        elif ext in ['doc', 'docx']:
            return 'word.png'
        elif ext in ['xls', 'xlsx']:
            return 'excel.png'
        elif ext in ['ppt', 'pptx']:
            return 'ppt.png'
        else:
            return 'file-icon.png'

   

    def seller_amount(self):
        if not self.price:
            return Decimal('0.00')
        return (self.price * self.seller_revenue_rate).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title) or "document"
            slug = base_slug
            counter = 2
            queryset = Document.objects.filter(slug=slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.exists():
                slug = f"{base_slug}-{counter}"
                queryset = Document.objects.filter(slug=slug)
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)
                counter += 1
            self.slug = slug
        
        # ✅ Auto-compress preview image on upload
        if self.preview_image:
            self.preview_image = compress_image(self.preview_image, quality=85)
        
        super().save(*args, **kwargs)

    def platform_amount(self):
        """ຄຳນວນສ່ວນແບ່ງຂອງລະບົບ"""
        return self.price - self.seller_amount()

    def get_absolute_url(self):
        """Returns the URL to access a particular document instance."""
        from django.urls import reverse
        return reverse('documents:document_detail', args=[self.pk])

    def __str__(self):
        return f"{self.title} - {self.price} kip"
    
    
    @property
    def seller_revenue_percent(self):
        return int(self.seller_revenue_rate * 100)
    @property
    def platform_revenue_percent(self):
        return int((1 - self.seller_revenue_rate) * 100)
    

class HeroSlider(models.Model):
    subtitle = models.CharField(
        max_length=100,
        verbose_name="ຂໍ້ຄວາມສັ້ນ (Trade-in offer)"
    )
    title = models.CharField(
        max_length=150,
        verbose_name="ຫົວຂໍ້ (Supper value deals)"
    )
    highlight_title = models.CharField(
        max_length=150,
        verbose_name="ຫົວຂໍ້ເນັ້ນ (On all products)"
    )
    description = models.TextField(
        verbose_name="ລາຍລະອຽດ"
    )
    button_text = models.CharField(
        max_length=50,
        default="ຊື້ເລີຍ",
        verbose_name="ຂໍ້ຄວາມປຸ່ມ"
    )
    button_link = models.URLField(
        verbose_name="ລິ້ງປຸ່ມ"
    )
    image = models.ImageField(
        upload_to="hero_slider/",
        verbose_name="ຮູບ Slider"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="ເປີດໃຊ້"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hero Slider"
        verbose_name_plural = "Hero Sliders"

    def __str__(self):
        return self.title



class NewsFlash(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    link_text = models.CharField(max_length=100, blank=True, null=True)
    link_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

class CategoryJobDocument(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
        

class WorkDocument(models.Model):
    # ຊື່ວຽກ (Job Title)
    title = models.CharField(max_length=255)

    # ໝວດໝູ່ (Category)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    # ລັກສະນະຈ້າງ (Job Type: Full-time, Part-time, Freelance)
    JOB_TYPE_CHOICES = [
        ('full_time', 'ວຽກເຕັມເວລາ'),
        ('part_time', 'ວຽກພາດທາມ'),
        ('freelance', 'ວຽກສັນຍາຈ້າງ'),
    ]
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)

    # ງົບປະມານ (Budget in Kip)
    budget = models.DecimalField(max_digits=12, decimal_places=2)

    # ລົງປະກາດມື້ (Posted Date)
    posted_date = models.DateTimeField(auto_now_add=True)

    # ສົ່ງວຽກພາຍໃນ (Deadline)
    deadline = models.DateField()

    # ຕິດຕໍ່ເຈົ້າຂອງວຽກ (Contact Info)
    contact_info = models.CharField(max_length=255)

    # Owner (User who created job)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # Optional: description
    description = RichTextUploadingField()
    status = models.BooleanField(default=True)  # True = Open, False = Closed


    def __str__(self):
        return self.title  





class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
