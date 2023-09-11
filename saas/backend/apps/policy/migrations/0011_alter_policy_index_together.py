# Generated by Django 3.2.16 on 2023-09-11 03:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('policy', '0010_remove_policy_policy_id'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='policy',
            index_together={('subject_id', 'subject_type', 'system_id'), ('action_id', 'system_id', 'subject_type', 'subject_id')},
        ),
    ]
