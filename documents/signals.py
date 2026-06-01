# signals.py
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
from .models import Document
from .services.preview_generator import create_preview_images

@receiver(post_save, sender=Document)
def auto_generate_preview_image(sender, instance, created, **kwargs):
    # ทำแค่ตอน create ใหม่เท่านั้น ไม่ทำตอน update
    if not created:
        return

    # ถ้ามี preview_image แล้ว ข้ามไป
    if instance.preview_image:
        return

    # ถ้าไม่ใช่ PDF ข้ามไป
    if not instance.file or not instance.is_pdf():
        return

    try:
        image_paths = create_preview_images(instance)

        if image_paths and os.path.exists(image_paths[0]):
            with open(image_paths[0], "rb") as f:
                # ใช้ update_fields เพื่อไม่ trigger signal ซ้ำ
                instance.preview_image.save(
                    f"preview_{instance.id}.jpg",
                    File(f),
                    save=False  # ไม่ save ตรงนี้
                )
            # update เฉพาะ field นี้ field เดียว
            Document.objects.filter(pk=instance.pk).update(
                preview_image=instance.preview_image
            )
            print(f"✅ สร้าง preview_image สำเร็จ doc id={instance.id}")

    except Exception as e:
        # ไม่ให้ error นี้ break upload process
        print(f"❌ สร้าง preview_image ล้มเหลว doc id={instance.id}: {e}")