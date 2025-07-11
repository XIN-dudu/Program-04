# Generated by Django 4.2.23 on 2025-07-11 09:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_userprofile_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
        migrations.CreateModel(
            name='SystemLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('error', 'Error')], default='info', max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('action', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('details', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='web.userprofile')),
            ],
        ),
    ]
