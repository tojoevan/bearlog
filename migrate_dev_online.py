#!/usr/bin/env python
"""
为 dev_online.db 数据库执行迁移
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line

# 临时修改数据库配置指向 dev_online.db
original_db_name = settings.DATABASES['default']['NAME']
settings.DATABASES['default']['NAME'] = os.path.join(settings.BASE_DIR, 'dev_online.db')

print(f"原始数据库: {original_db_name}")
print(f"目标数据库: {settings.DATABASES['default']['NAME']}")
print("\n开始执行迁移...\n")

# 执行迁移
sys.argv = ['manage.py', 'migrate', '--run-syncdb']
execute_from_command_line(sys.argv)

print("\n✅ 迁移完成！")
