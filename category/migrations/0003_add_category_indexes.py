# Generated migration for category indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0002_category_is_show_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, db_index=True, null=True, on_delete=models.deletion.CASCADE, related_name='children', to='category.category'),
        ),
        migrations.AlterField(
            model_name='category',
            name='is_popular_category',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='category',
            name='is_show_category',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['parent', 'is_show_category'], name='category_ca_parent_show_idx'),
        ),
    ]
