from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name="post",
            index=GinIndex(
                fields=["title"],
                name="post_title_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="post",
            index=GinIndex(
                fields=["body"],
                name="post_body_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
