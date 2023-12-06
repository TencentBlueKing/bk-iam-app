# Generated by Django 3.2.16 on 2023-11-17 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('role', '0020_roleconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolerelatedobject',
            name='object_type',
            field=models.CharField(choices=[('template', '权限模板'), ('group', '用户组'), ('subject_template', '人员模版')], max_length=32, verbose_name='对象类型'),
        ),
        migrations.CreateModel(
            name='RoleGroupMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_id', models.IntegerField(verbose_name='角色ID')),
                ('subset_id', models.IntegerField(default=0, verbose_name='二级角色ID')),
                ('group_id', models.IntegerField(db_index=True, verbose_name='用户组ID')),
                ('subject_template_id', models.IntegerField(db_index=True, default=0, verbose_name='用户模板ID')),
                ('subject_type', models.CharField(choices=[('user', '用户'), ('group', '用户组'), ('department', '部门')], max_length=32, verbose_name='用户类型')),
                ('subject_id', models.CharField(max_length=32, verbose_name='用户ID')),
            ],
            options={
                'verbose_name': '角色用户组成员',
                'verbose_name_plural': '角色用户组成员',
                'unique_together': {('role_id', 'subject_type', 'subject_id', 'group_id', 'subject_template_id')},
            },
        ),
    ]