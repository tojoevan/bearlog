#!/usr/bin/env python
"""
Todo功能测试脚本
用于验证Todo模型和基本功能是否正常工作
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from blogs.models import Blog, Todo
import json

def test_todo_functionality():
    print("=" * 60)
    print("Todo 功能测试")
    print("=" * 60)
    
    # 1. 创建测试用户和Blog（如果不存在）
    print("\n1. 检查测试数据...")
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"   ✓ 创建测试用户: {user.username}")
    else:
        print(f"   ✓ 使用现有用户: {user.username}")
    
    blog, created = Blog.objects.get_or_create(
        subdomain='testblog',
        defaults={
            'user': user,
            'title': 'Test Blog',
            'content': 'Test content'
        }
    )
    if created:
        print(f"   ✓ 创建测试Blog: {blog.title}")
    else:
        print(f"   ✓ 使用现有Blog: {blog.title}")
    
    # 2. 测试创建普通待办事项
    print("\n2. 测试创建普通待办事项...")
    todo1 = Todo.objects.create(
        blog=blog,
        title='Test Todo 1',
        description='This is a test todo item',
        priority='high',
        status='pending',
        due_date=timezone.now() + timezone.timedelta(days=7),
        tags=json.dumps(['test', 'important'])
    )
    print(f"   ✓ 创建待办事项: {todo1.title}")
    print(f"     - 状态: {todo1.get_status_display()}")
    print(f"     - 优先级: {todo1.get_priority_display()}")
    print(f"     - 标签: {todo1.tag_list}")
    
    # 3. 测试创建周期性待办事项
    print("\n3. 测试创建周期性待办事项...")
    todo2 = Todo.objects.create(
        blog=blog,
        title='Weekly Review',
        description='Weekly blog review task',
        priority='medium',
        status='pending',
        is_recurring=True,
        recurring_type='weekly',
        recurring_interval=1,
        due_date=timezone.now() + timezone.timedelta(days=7),
        tags=json.dumps(['review', 'weekly'])
    )
    print(f"   ✓ 创建周期性待办事项: {todo2.title}")
    print(f"     - 周期类型: {todo2.get_recurring_type_display()}")
    print(f"     - 间隔: {todo2.recurring_interval}")
    
    # 4. 测试完成任务
    print("\n4. 测试完成任务...")
    todo1.status = 'completed'
    todo1.completed_date = timezone.now()
    todo1.save()
    print(f"   ✓ 完成任务: {todo1.title}")
    print(f"     - 新状态: {todo1.get_status_display()}")
    print(f"     - 完成时间: {todo1.completed_date}")
    
    # 5. 测试周期性任务完成（应自动创建下一个）
    print("\n5. 测试周期性任务完成...")
    initial_count = Todo.objects.filter(blog=blog, title='Weekly Review').count()
    print(f"     - 完成前任务数量: {initial_count}")
    
    todo2.complete()
    
    new_count = Todo.objects.filter(blog=blog, title='Weekly Review').count()
    print(f"     - 完成后任务数量: {new_count}")
    
    if new_count > initial_count:
        print(f"   ✓ 周期性任务成功创建下一个实例")
        next_todo = Todo.objects.filter(blog=blog, title='Weekly Review', status='pending').last()
        print(f"     - 新任务截止日期: {next_todo.due_date}")
    else:
        print(f"   ✗ 周期性任务未创建新实例")
    
    # 6. 测试查询和统计
    print("\n6. 测试查询和统计...")
    all_todos = Todo.objects.filter(blog=blog)
    pending_todos = Todo.objects.filter(blog=blog, status='pending')
    completed_todos = Todo.objects.filter(blog=blog, status='completed')
    
    print(f"   ✓ 总任务数: {all_todos.count()}")
    print(f"   ✓ 待处理: {pending_todos.count()}")
    print(f"   ✓ 已完成: {completed_todos.count()}")
    
    # 7. 测试筛选功能
    print("\n7. 测试筛选功能...")
    high_priority = Todo.objects.filter(blog=blog, priority='high')
    print(f"   ✓ 高优先级任务: {high_priority.count()}")
    
    recurring_tasks = Todo.objects.filter(blog=blog, is_recurring=True)
    print(f"   ✓ 周期性任务: {recurring_tasks.count()}")
    
    # 8. 测试更新操作
    print("\n8. 测试更新操作...")
    todo_to_update = Todo.objects.filter(blog=blog, status='pending').first()
    if todo_to_update:
        old_title = todo_to_update.title
        todo_to_update.title = f"{old_title} (Updated)"
        todo_to_update.priority = 'urgent'
        todo_to_update.save()
        print(f"   ✓ 更新任务标题: {todo_to_update.title}")
        print(f"     - 新优先级: {todo_to_update.get_priority_display()}")
    
    # 9. 清理测试数据（可选）
    print("\n9. 清理测试数据...")
    cleanup = input("   是否删除测试数据？(y/n): ").strip().lower()
    if cleanup == 'y':
        Todo.objects.filter(blog=blog).delete()
        if created:
            blog.delete()
            user.delete()
        print("   ✓ 测试数据已清理")
    else:
        print("   ℹ 测试数据保留，可在Django Admin中查看")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print("\n提示:")
    print("- 访问 http://127.0.0.1:8000/testblog/dashboard/todo/ 查看Todo页面")
    print("- 访问 http://127.0.0.1:8000/admin/ 在管理后台查看和管理任务")
    print("- 测试用户: testuser / testpass123")

if __name__ == '__main__':
    try:
        test_todo_functionality()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
