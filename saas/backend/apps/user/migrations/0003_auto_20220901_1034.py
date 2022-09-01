# Generated by Django 2.2.28 on 2022-09-01 02:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_userpermissioncleanuprecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpermissioncleanuprecord',
            name='retry_count',
            field=models.IntegerField(default=0, verbose_name='检查次数'),
        ),
        migrations.AlterField(
            model_name='userpermissioncleanuprecord',
            name='status',
            field=models.CharField(choices=[('created', '已创建'), ('running', '正在清理'), ('succeed', '清理成功'), ('failed', '清理失败')], default='created', max_length=32, verbose_name='单据状态'),
        ),
    ]
