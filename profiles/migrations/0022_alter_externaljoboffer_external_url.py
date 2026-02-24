# Generated manually to fix external_url field length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0021_alter_formation_school_alter_formation_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externaljoboffer',
            name='external_url',
            field=models.URLField(max_length=2000, verbose_name='URL externe'),
        ),
    ]