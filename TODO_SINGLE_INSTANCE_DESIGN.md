# 周期性任务单实例设计

## 📋 设计理念

### 核心思想
**一个周期性任务 = 一条数据库记录**

- ❌ **不再创建新实例**：每次完成不创建新的任务记录
- ✅ **状态自动流转**：同一个任务在不同周期间切换状态
- ✅ **简洁高效**：避免数据冗余，易于管理

---

## 🎯 工作流程

### 完整的周期循环

```
时刻 T0: 创建周期性任务
  → 数据库: 1条记录
  → 状态: Pending ⏳
  → due_date: 2026-04-11

时刻 T1: 用户点击 Complete
  → 数据库: 仍是1条记录（未新增）
  → 状态: Completed ✅
  → completed_date: 2026-04-04 18:20
  → due_date: 2026-04-11 (下一周期的截止日期)
  → 显示: "✓ This cycle completed"

时刻 T2: 到达下一周期 (2026-04-11)
  → 数据库: 仍是1条记录
  → 系统自动检测: now >= due_date
  → 状态自动重置: Completed → Pending ⏳
  → completed_date: 清空
  → 显示: 待处理状态，可以再次开始

时刻 T3: 用户再次点击 Complete
  → 状态: Completed ✅
  → completed_date: 2026-04-11 18:20
  → due_date: 2026-04-18 (再下一周期)
  → 循环继续...
```

---

## 🔧 技术实现

### 1. 模型方法更新

#### `complete()` - 完成任务

**文件**: `blogs/models.py`

```python
def complete(self):
    """
    完成任务
    
    行为说明：
    - 非周期性任务：标记为 completed（永久）
    - 周期性任务：
      1. 当前实例标记为 completed
      2. 记录完成时间
      3. 计算下一个周期的截止日期
      4. **不创建新实例**，等待下次查询时自动重置状态
    """
    from django.utils import timezone
    
    # 标记当前任务为已完成
    self.status = 'completed'
    self.completed_date = timezone.now()
    
    # 如果是周期性任务，计算下一个周期的截止日期
    if self.is_recurring and self.recurring_type:
        self.calculate_next_due_date()
    
    self.save()
    print(f"✅ Task '{self.title}' completed (Recurring: {self.is_recurring})")
```

**关键点：**
- ✅ 只更新现有记录
- ✅ 调用 `calculate_next_due_date()` 计算下一周期
- ✅ 不创建新对象

---

#### `calculate_next_due_date()` - 计算下一周期截止日期

```python
def calculate_next_due_date(self):
    """
    计算下一个周期的截止日期
    
    根据当前完成时间和周期类型，计算下一个周期的截止日期
    不创建新实例，只更新当前任务的 due_date
    """
    from django.utils import timezone
    from datetime import timedelta
    
    if not self.completed_date:
        return
    
    # 基于完成时间计算下一个周期
    completed = self.completed_date
    
    if self.recurring_type == 'daily':
        delta = timedelta(days=self.recurring_interval)
        self.due_date = completed + delta
    elif self.recurring_type == 'weekly':
        delta = timedelta(weeks=self.recurring_interval)
        self.due_date = completed + delta
    elif self.recurring_type == 'monthly':
        # 按月增加，处理月末日期
        month = completed.month + self.recurring_interval
        year = completed.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        try:
            self.due_date = completed.replace(year=year, month=month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            self.due_date = completed.replace(year=year, month=month, day=last_day)
    elif self.recurring_type == 'yearly':
        try:
            self.due_date = completed.replace(year=completed.year + self.recurring_interval)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(completed.year + self.recurring_interval, completed.month)[1]
            self.due_date = completed.replace(year=completed.year + self.recurring_interval, day=last_day)
    else:
        # 默认按天计算
        delta = timedelta(days=self.recurring_interval)
        self.due_date = completed + delta
    
    print(f"🔁 Next cycle due date: {self.due_date}")
```

**计算逻辑：**
- 基于 `completed_date`（完成时间）而非当前时间
- 支持 Daily/Weekly/Monthly/Yearly
- 处理月末、闰年等边界情况

---

#### `check_and_reset_cycle()` - 检查并重置周期

```python
def check_and_reset_cycle(self):
    """
    检查是否进入新周期，如果是则重置状态为 pending
    
    应该在查询任务时调用此方法
    Returns:
        bool: 是否重置了状态
    """
    from django.utils import timezone
    
    if not self.is_recurring or self.status != 'completed':
        return False
    
    if not self.due_date:
        return False
    
    # 如果当前时间已超过下一个周期的截止日期，说明进入新周期
    now = timezone.now()
    if now >= self.due_date:
        # 重置为待处理状态
        self.status = 'pending'
        self.completed_date = None
        self.save()
        print(f"🔄 Task '{self.title}' reset to pending for new cycle")
        return True
    
    return False
```

**触发时机：**
- 每次查询Todo列表时调用
- 自动检测是否进入新周期
- 符合条件时自动重置状态

---

### 2. 视图层集成

#### `todo_list()` - Todo列表视图

**文件**: `blogs/views/studio.py`

```python
@login_required
def todo_list(request, id):
    # ... 获取blog ...
    
    # 基础查询集
    todos = Todo.objects.filter(blog=blog)
    
    # 检查并重置周期性任务的状态
    for todo in todos:
        if todo.is_recurring:
            todo.check_and_reset_cycle()
    
    # ... 应用过滤和排序 ...
```

**执行流程：**
1. 查询所有任务
2. **遍历每个任务**，检查是否需要重置周期
3. 如果需要，自动将状态从 Completed 改为 Pending
4. 返回更新后的列表

---

### 3. 显示逻辑

#### 模板中的显示

**文件**: `templates/studio/todo_list.html`

**刚完成的任务（24小时内）：**
```html
✅ Weekly Review 🔁 Weekly ✓ This cycle completed
   High | Completed
   📅 Due: Apr 11, 2026 18:20  ← 下一周期的截止日期
   ✓ Completed: Apr 04, 2026 18:20
```

**进入新周期后：**
```html
⏳ Weekly Review 🔁 Weekly
   High | Pending
   📅 Due: Apr 18, 2026 18:20  ← 再下一周期的截止日期
```

---

## 📊 数据对比

### 旧设计（多实例）vs 新设计（单实例）

| 特性 | 旧设计 | 新设计 |
|------|--------|--------|
| 数据库记录 | 每次完成创建新记录 | 始终只有1条记录 |
| 历史追溯 | 保留所有历史实例 | 只保留最近一次完成时间 |
| 数据量 | 随时间增长 | 恒定不变 |
| 查询复杂度 | 需要区分新旧实例 | 简单直接 |
| 状态管理 | 多个实例不同状态 | 单个实例状态流转 |
| 用户体验 | 列表中可能有多个同名任务 | 列表中只有一个任务 |

---

## 💡 使用场景示例

### 场景1: 每周审查任务

**第1周 - 周一：**
```
数据库记录:
{
  id: 1,
  title: "Weekly Review",
  status: "pending",
  is_recurring: true,
  recurring_type: "weekly",
  due_date: "2026-04-11"
}

界面显示:
⏳ Weekly Review 🔁 Weekly | Pending
```

**第1周 - 周三（完成任务）：**
```
用户操作: Click Complete

数据库记录:
{
  id: 1,  ← 同一条记录
  title: "Weekly Review",
  status: "completed",  ← 状态变更
  completed_date: "2026-04-06 15:30",  ← 记录完成时间
  due_date: "2026-04-13",  ← 计算下一周期（7天后）
  is_recurring: true,
  recurring_type: "weekly"
}

界面显示:
✅ Weekly Review 🔁 Weekly ✓ This cycle completed
   Completed: Apr 06, 2026 15:30
   Due: Apr 13, 2026 (下一周期)
```

**第2周 - 周一（进入新周期）：**
```
用户访问Todo页面

系统检测:
  now (Apr 13) >= due_date (Apr 13) → True
  触发: check_and_reset_cycle()

数据库记录:
{
  id: 1,  ← 仍是同一条记录
  title: "Weekly Review",
  status: "pending",  ← 自动重置
  completed_date: null,  ← 清空
  due_date: "2026-04-13",  ← 保持不变
  is_recurring: true,
  recurring_type: "weekly"
}

界面显示:
⏳ Weekly Review 🔁 Weekly | Pending
   Due: Apr 13, 2026
```

**第2周 - 周二（再次完成）：**
```
用户操作: Click Complete

数据库记录:
{
  id: 1,  ← 还是同一条记录
  title: "Weekly Review",
  status: "completed",
  completed_date: "2026-04-14 10:00",  ← 新的完成时间
  due_date: "2026-04-21",  ← 新的下一周期
  is_recurring: true,
  recurring_type: "weekly"
}

循环继续...
```

---

### 场景2: 每日备份任务

**Day 1:**
```
创建任务 → Pending
完成 → Completed (due_date: Day 2)
显示: ✓ This cycle completed
```

**Day 2:**
```
访问页面 → 自动检测进入新周期
状态重置 → Pending
可以再次开始
```

**Day 3:**
```
重复 Day 2 的流程
```

**始终只有1条数据库记录！**

---

## ✨ 优势

### 1. 数据简洁
- ✅ 避免数据冗余
- ✅ 数据库大小恒定
- ✅ 易于维护和备份

### 2. 性能优化
- ✅ 查询速度快
- ✅ 无需JOIN或复杂过滤
- ✅ 索引效率高

### 3. 用户体验
- ✅ 列表中不会出现多个同名任务
- ✅ 清晰的状态流转
- ✅ 直观的周期提示

### 4. 逻辑清晰
- ✅ 单一职责：一个任务管理自己的周期
- ✅ 状态机模式：Pending → Completed → Pending
- ✅ 自动化：无需手动干预

---

## 🔍 注意事项

### 1. 历史记录限制

**问题**: 无法查看完整的完成历史

**解决方案**:
- 如需完整历史，可添加单独的日志表
- 或在任务描述中手动记录关键时间点

**示例日志表设计**:
```python
class TodoLog(models.Model):
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)  # 'completed', 'reset'
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
```

### 2. 周期检测频率

**当前实现**: 每次查询Todo列表时检测

**优点**:
- ✅ 实时性好
- ✅ 无需后台任务

**缺点**:
- ⚠️ 频繁查询可能影响性能

**优化建议**:
- 如果任务数量很大，考虑缓存检测结果
- 或使用Celery定时任务批量更新

### 3. 时区处理

**当前实现**: 使用Django的timezone.now()

**注意**:
- ✅ 已正确处理时区
- ✅ 支持用户自定义时区
- ⚠️ 确保服务器时区配置正确

---

## 📝 配置选项

### 调整"刚完成"的显示时长

**编辑 `blogs/views/studio.py`:**

```python
# 第835行附近
recent_completed_cutoff = tz.now() - tz.timedelta(hours=24)

# 改为其他时长：
recent_completed_cutoff = tz.now() - tz.timedelta(hours=12)  # 12小时
recent_completed_cutoff = tz.now() - tz.timedelta(days=2)    # 2天
recent_completed_cutoff = tz.now() - tz.timedelta(days=7)    # 7天
```

**作用**: 控制完成后的任务在列表中显示多久

---

## 🚀 快速测试

### 测试步骤

1. **创建周期性任务**
   ```
   标题: Test Single Instance
   周期: Daily
   截止日期: 明天
   ```

2. **完成任务**
   ```
   点击: ✅ Complete
   验证: 
     - 状态变为 Completed
     - 显示 "✓ This cycle completed"
     - due_date 更新为后天
   ```

3. **模拟时间跳转**
   ```python
   # 在Django shell中
   from blogs.models import Todo
   from django.utils import timezone
   from datetime import timedelta
   
   todo = Todo.objects.get(title='Test Single Instance')
   # 手动将 due_date 设置为过去
   todo.due_date = timezone.now() - timedelta(hours=1)
   todo.save()
   ```

4. **刷新页面**
   ```
   验证:
     - 状态自动变回 Pending
     - completed_date 被清空
     - 可以再次点击 Complete
   ```

5. **检查数据库**
   ```sql
   SELECT COUNT(*) FROM blogs_todo WHERE title = 'Test Single Instance';
   -- 应该返回 1
   ```

---

## 📚 相关文档

- [TODO_RECURRING_WORKFLOW.md](TODO_RECURRING_WORKFLOW.md) - 周期性任务工作流（旧版）
- [TODO_COMPLETED_DISPLAY_FIX.md](TODO_COMPLETED_DISPLAY_FIX.md) - 完成状态显示
- [TODO_EDIT_RECURRING_UPDATE.md](TODO_EDIT_RECURRING_UPDATE.md) - 编辑周期性属性

---

**更新日期**: 2026-04-05  
**版本**: v2.0 (单实例设计)  
**状态**: ✅ 已实现并测试
