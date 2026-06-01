# Generated migration for slug and updated_at fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_rename_documents_d_is_activ_created_idx_documents_d_is_acti_bba6b9_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True, db_index=True),
        ),
        migrations.AddField(
            model_name='document',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
