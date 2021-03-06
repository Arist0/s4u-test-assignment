# Generated by Django 3.0.8 on 2020-08-03 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(unique=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=18)),
            ],
        ),
    ]
