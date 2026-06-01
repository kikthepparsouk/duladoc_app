from django.core.management.base import BaseCommand
from documents.models import Document
from documents.services.preview_generator import create_preview_images
from django.core.files import File
import os

class Command(BaseCommand):
    help = 'Generate preview images for existing documents'

    def add_arguments(self, parser):
        parser.add_argument('--document-id', type=int, help='Generate for specific document')

    def handle(self, *args, **options):
        documents = Document.objects.filter(
            file__isnull=False,
            preview_image__isnull=True
        )
        
        if options['document_id']:
            documents = documents.filter(id=options['document_id'])
        
        for document in documents:
            if document.is_pdf():
                self.stdout.write(f"Processing document {document.id}: {document.title}")
                try:
                    image_paths = create_preview_images(document)
                    if image_paths:
                        with open(image_paths[0], "rb") as f:
                            document.preview_image.save(
                                f"preview_{document.id}.jpg",
                                File(f),
                                save=True
                            )
                        self.stdout.write(self.style.SUCCESS(f"✓ Generated preview for {document.id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Failed for {document.id}: {e}"))