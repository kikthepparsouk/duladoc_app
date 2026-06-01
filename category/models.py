from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True
    )
    photo = models.ImageField(upload_to='category_photos/', null=True, blank=True)
    
    is_popular_category = models.BooleanField(default=False, db_index=True)
    is_show_category = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_root(self):
        return self.parent is None

    def get_children(self):
        return self.children.all()
    
    def has_children(self):
        return self.children.exists()

    def get_ancestors(self):
        ancestors = []
        category = self
        while category:
            ancestors.insert(0, category)
            category = category.parent
        return ancestors

    def get_all_descendants(self):
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['parent', 'is_show_category']),
        ]

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Returns the URL to access a particular category instance."""
        from django.urls import reverse
        return reverse('documents:doc_by_category', args=[self.id])



