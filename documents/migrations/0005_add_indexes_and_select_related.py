# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_contactmessage'),
    ]

    operations = [
        # Add db_index to frequently queried fields
        migrations.AlterField(
            model_name='document',
            name='seller',
            field=models.ForeignKey(db_index=True, on_delete=models.deletion.CASCADE, related_name='owned_documents', to='auth.user'),
        ),
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='document',
            name='category',
            field=models.ForeignKey(db_index=True, null=True, on_delete=models.deletion.SET_NULL, related_name='documents', to='category.category'),
        ),
        migrations.AlterField(
            model_name='document',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='is_featured_book',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='document',
            name='is_popular_book',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='document',
            name='is_new_book',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='document',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        # Add composite indexes for common query patterns
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['is_active', '-created_at'], name='documents_d_is_activ_created_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['is_featured_book', 'is_active'], name='documents_d_is_feat_is_activ_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['is_popular_book', 'is_active'], name='documents_d_is_pop_is_activ_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['is_new_book', 'is_active'], name='documents_d_is_new_is_activ_idx'),
        ),
    ]
