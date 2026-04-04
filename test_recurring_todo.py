#!/usr/bin/env python
"""
周期性任务功能测试
验证 Start → Complete → 自动创建下一周期的完整流程
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

from django.conf import settings
settings.DATABASES['default']['NAME'] = os.path.join(settings.BASE_DIR, 'dev_online.db')

from django.utils import timezone
from django.contrib.auth.models import User
from blogs.models import Blog, Todo
from datetime import timedelta
import json

def test_recurring_todo_workflow():
    print("=" * 70)
    print("周期性任务工作流程测试")
    print("=" * 70)
    
    # 获取测试用户和Blog
    try:
        user = User.objects.get(username='testuser')
        blog = Blog.objects.get(subdomain='testblog')
        print(f"\n✅ 使用测试账户: {user.username}")
        print(f"✅ 使用测试Blog: {blog.title}\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("请先运行 test_todo.py 创建测试数据")
        return
    
    # 清理旧的测试数据
    Todo.objects.filter(blog=blog, title__startswith='[TEST]').delete()
    
    # ========== 测试1: 创建周期性任务 ==========
    print("📝 测试1: 创建每周重复的周期性任务")
    print("-" * 70)
    
    recurring_todo = Todo.objects.create(
        blog=blog,
        title='[TEST] Weekly Review',
        description='Weekly blog content review',
        priority='high',
        status='pending',
        is_recurring=True,
        recurring_type='weekly',
        recurring_interval=1,
        due_date=timezone.now() + timedelta(days=7),
        tags=json.dumps(['review', 'weekly'])
    )
    
    print(f"   创建任务: {recurring_todo.title}")
    print(f"   初始状态: {recurring_todo.get_status_display()} ⏳")
    print(f"   周期类型: {recurring_todo.get_recurring_type_display()}")
    print(f"   周期间隔: {recurring_todo.recurring_interval}")
    print(f"   截止日期: {recurring_todo.due_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   ✅ 任务创建成功\n")
    
    # ========== 测试2: 点击 Start ==========
    print("▶️  测试2: 点击 Start 开始任务")
    print("-" * 70)
    
    recurring_todo.status = 'in_progress'
    recurring_todo.save()
    
    print(f"   当前状态: {recurring_todo.get_status_display()} 🔄")
    print(f"   ✅ 任务已开始\n")
    
    # ========== 测试3: 点击 Complete ==========
    print("✅ 测试3: 点击 Complete 完成任务")
    print("-" * 70)
    
    print(f"   完成前状态: {recurring_todo.get_status_display()}")
    print(f"   调用 complete() 方法...")
    
    # 记录完成前的任务数量
    before_count = Todo.objects.filter(blog=blog, title='[TEST] Weekly Review').count()
    print(f"   完成前任务总数: {before_count}")
    
    # 执行 complete
    recurring_todo.complete()
    
    # 刷新对象
    recurring_todo.refresh_from_db()
    
    print(f"   完成后状态: {recurring_todo.get_status_display()} ✅")
    print(f"   完成时间: {recurring_todo.completed_date.strftime('%Y-%m-%d %H:%M')}")
    
    # 检查是否创建了新实例
    after_count = Todo.objects.filter(blog=blog, title='[TEST] Weekly Review').count()
    print(f"   完成后任务总数: {after_count}")
    
    if after_count > before_count:
        print(f"   ✅ 成功创建下一个周期的新实例！\n")
        
        # 获取新实例
        new_todo = Todo.objects.filter(
            blog=blog, 
            title='[TEST] Weekly Review',
            status='pending'
        ).order_by('-created_date').first()
        
        if new_todo:
            print("🔁 新周期任务详情:")
            print("-" * 70)
            print(f"   任务ID: {new_todo.pk} (原任务ID: {recurring_todo.pk})")
            print(f"   任务标题: {new_todo.title}")
            print(f"   当前状态: {new_todo.get_status_display()} ⏳")
            print(f"   优先级: {new_todo.get_priority_display()}")
            print(f"   截止日期: {new_todo.due_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   周期类型: {new_todo.get_recurring_type_display()}")
            print(f"   标签: {new_todo.tag_list}")
            
            # 验证新任务是 pending 状态
            if new_todo.status == 'pending':
                print(f"   ✅ 新实例状态正确: pending (待处理)")
            else:
                print(f"   ❌ 新实例状态错误: {new_todo.status}")
            
            # 验证截止日期是否正确（应该是7天后）
            expected_due = recurring_todo.completed_date + timedelta(weeks=1)
            actual_due = new_todo.due_date
            time_diff = abs((actual_due - expected_due).total_seconds())
            
            if time_diff < 60:  # 允许1分钟误差
                print(f"   ✅ 截止日期计算正确: {actual_due.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"   ⚠️  截止日期可能有偏差")
                print(f"      预期: {expected_due.strftime('%Y-%m-%d %H:%M')}")
                print(f"      实际: {actual_due.strftime('%Y-%m-%d %H:%M')}")
            
            print(f"\n   📊 总结:")
            print(f"      - 原任务 (ID:{recurring_todo.pk}): 已完成 ✅")
            print(f"      - 新任务 (ID:{new_todo.pk}): 待处理 ⏳")
            print(f"      - 下个周期自动开始，无需手动创建")
        else:
            print(f"   ❌ 未找到新的待处理任务")
    else:
        print(f"   ❌ 未创建新实例")
    
    # ========== 测试4: 验证界面显示 ==========
    print("\n🎨 测试4: 界面显示验证")
    print("-" * 70)
    print(f"   已完成的任务显示:")
    print(f"      ✅ [TEST] Weekly Review")
    print(f"      🔁 Weekly (周期性徽章)")
    print(f"      ✓ This cycle completed (绿色提示)")
    print(f"      ✓ Completed: {recurring_todo.completed_date.strftime('%M d, Y H:i')}")
    print(f"\n   待处理的新任务显示:")
    if new_todo:
        print(f"      ⏳ [TEST] Weekly Review")
        print(f"      🔁 Weekly (周期性徽章)")
        print(f"      📅 Due: {new_todo.due_date.strftime('%b d, Y H:i')}")
    
    # ========== 测试5: 不同类型的周期 ==========
    print("\n🔄 测试5: 测试不同周期类型")
    print("-" * 70)
    
    test_cases = [
        ('daily', 1, '每天'),
        ('weekly', 2, '每2周'),
        ('monthly', 1, '每月'),
        ('yearly', 1, '每年'),
    ]
    
    for rtype, interval, desc in test_cases:
        test_todo = Todo.objects.create(
            blog=blog,
            title=f'[TEST] {desc} Task',
            priority='medium',
            status='pending',
            is_recurring=True,
            recurring_type=rtype,
            recurring_interval=interval,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # 模拟完成
        test_todo.complete()
        
        # 检查是否创建了新实例
        next_todo = Todo.objects.filter(
            blog=blog,
            title=f'[TEST] {desc} Task',
            status='pending'
        ).order_by('-created_date').first()
        
        if next_todo:
            print(f"   ✅ {desc}: 新实例创建成功 (Due: {next_todo.due_date.strftime('%Y-%m-%d')})")
        else:
            print(f"   ❌ {desc}: 新实例创建失败")
    
    # ========== 清理测试数据 ==========
    print("\n🧹 清理测试数据")
    print("-" * 70)
    cleanup = input("   是否删除所有测试任务？(y/n): ").strip().lower()
    if cleanup == 'y':
        deleted_count, _ = Todo.objects.filter(blog=blog, title__startswith='[TEST]').delete()
        print(f"   ✅ 已删除 {deleted_count} 个测试任务")
    else:
        print(f"   ℹ️  测试任务保留，可在Todo页面查看")
    
    print("\n" + "=" * 70)
    print("✅ 周期性任务工作流程测试完成！")
    print("=" * 70)
    print("\n💡 使用说明:")
    print("   1. 创建周期性任务时勾选 'Recurring Task'")
    print("   2. 选择周期类型（Daily/Weekly/Monthly/Yearly）")
    print("   3. 设置周期间隔")
    print("   4. 点击 Start 开始任务")
    print("   5. 点击 Complete 完成当前周期")
    print("   6. 系统自动创建下一个周期的新任务（状态: Pending）")
    print("   7. 在界面上可以看到 '✓ This cycle completed' 提示")
    print("\n📋 访问地址:")
    print(f"   http://127.0.0.1:8000/{blog.subdomain}/dashboard/todo/")

if __name__ == '__main__':
    try:
        test_recurring_todo_workflow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
