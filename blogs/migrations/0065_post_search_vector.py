import django.contrib.postgres.search
from django.db import migrations, connection


class Migration(migrations.Migration):

    dependencies = [
        ("blogs", "0064_remove_blog_optimise_images"),
    ]

    operations = [
        # Add the search_vector field
        migrations.AddField(
            model_name="post",
            name="search_vector",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        # Add GIN index on the field (PostgreSQL only)
        migrations.RunSQL(
            sql="""
                CREATE INDEX blogs_post_search_vector_gin ON blogs_post USING GIN (search_vector);
            """ if connection.vendor == 'postgresql' else """
                -- SQLite doesn't support GIN indexes, skip index creation
            """,
            reverse_sql="DROP INDEX IF EXISTS blogs_post_search_vector_gin;" if connection.vendor == 'postgresql' else "",
        ),
    ]
