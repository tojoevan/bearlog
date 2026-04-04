# 周期性任务智能状态管理

## 📋 功能概述

周期性任务现在支持完整的生命周期管理：

```
创建 (Pending) → Start (In Progress) → Complete (Completed) 
                                              ↓
                                    自动创建下一周期 (Pending)
```

---

## 🎯 工作流程

### 1️⃣ 创建周期性任务

**步骤：**
1. 点击 "➕ Add New Todo"
2. 填写任务信息
3. ✅ 勾选 "Recurring Task"
4. 选择周期类型：
   - Daily (每天)
   - Weekly (每周)
   - Monthly (每月)
   - Yearly (每年)
5. 设置周期间隔（如：每2周、每3个月）
6. 点击 "Create Todo"

**示例：**
```
标题: Weekly Blog Review
周期: Weekly, 间隔 1
优先级: High
截止日期: 2026-04-11 18:20
```

---

### 2️⃣ 点击 Start 开始任务

**操作：**
- 找到任务卡片
- 点击 "▶️ Start" 按钮

**结果：**
```
状态变化: Pending ⏳ → In Progress 🔄
```

**界面显示：**
```
🔄 Weekly Blog Review
   🔁 Weekly
   High | In Progress
   📅 Due: Apr 11, 2026 18:20
```

---

### 3️⃣ 点击 Complete 完成任务

**操作：**
- 点击 "✅ Complete" 按钮

**系统行为：**
1. **当前实例**标记为 Completed
2. **自动创建**下一个周期的新实例
3. 新实例状态为 **Pending**（待处理）
4. 新实例的截止日期自动计算

**结果：**
```
原任务 (ID: 123):
  状态: Completed ✅
  完成时间: 2026-04-04 18:20
  显示: "✓ This cycle completed"

新任务 (ID: 124):
  状态: Pending ⏳
  截止日期: 2026-04-11 18:20 (7天后)
  继承: 标题、描述、优先级、标签等
```

---

### 4️⃣ 下一周期自动显示为待处理

**新周期开始时：**
- 新任务出现在Todo列表中
- 状态为 **Pending ⏳**
- 可以再次执行 Start → Complete 流程
- 完成后又会创建下一个周期

**循环示例：**
```
第1周: Pending → Start → Complete → 创建第2周任务
第2周: Pending → Start → Complete → 创建第3周任务
第3周: Pending → Start → Complete → 创建第4周任务
...
```

---

## 🎨 界面显示优化

### 已完成的任务
```
✅ Weekly Blog Review
   🔁 Weekly
   High | Completed
   ✓ This cycle completed          ← 绿色提示
   📅 Due: Apr 11, 2026 18:20
   ✓ Completed: Apr 04, 2026 18:20
```

### 待处理的新周期任务
```
⏳ Weekly Blog Review
   🔁 Weekly
   High | Pending
   📅 Due: Apr 11, 2026 18:20
```

### 进行中的任务
```
🔄 Weekly Blog Review
   🔁 Weekly
   High | In Progress
   📅 Due: Apr 11, 2026 18:20
```

---

## 🔧 技术实现

### 模型方法

#### `complete()` 方法
```python
def complete(self):
    """
    完成任务，如果是周期性任务则创建下一个实例
    
    行为说明：
    - 非周期性任务：标记为 completed
    - 周期性任务：
      1. 当前实例标记为 completed
      2. 自动创建下一个周期的新实例（状态为 pending）
      3. 新实例的 due_date 根据周期类型自动计算
    """
    self.status = 'completed'
    self.completed_date = timezone.now()
    self.save()
    
    if self.is_recurring and self.recurring_type:
        next_todo = self.create_next_occurrence()
```

#### `create_next_occurrence()` 方法
```python
def create_next_occurrence(self):
    """
    为周期性任务创建下一个实例
    
    新实例特性：
    - status: 'pending' (待处理状态)
    - due_date: 根据周期类型自动计算
    - 继承原任务的所有属性
    """
    # 计算下次出现时间
    if self.recurring_type == 'daily':
        delta = timedelta(days=self.recurring_interval)
    elif self.recurring_type == 'weekly':
        delta = timedelta(weeks=self.recurring_interval)
    elif self.recurring_type == 'monthly':
        # 按月计算，处理月末日期
        ...
    elif self.recurring_type == 'yearly':
        # 按年计算，处理闰年
        ...
    
    # 创建新任务（状态为 pending）
    new_todo = Todo.objects.create(
        blog=self.blog,
        title=self.title,
        description=self.description,
        status='pending',  # ← 关键：新实例为待处理
        priority=self.priority,
        is_recurring=self.is_recurring,
        recurring_type=self.recurring_type,
        recurring_interval=self.recurring_interval,
        due_date=self.next_occurrence,
        tags=self.tags,
    )
    
    return new_todo
```

---

## 📊 周期计算规则

### Daily (每天)
```
完成时间: 2026-04-04 18:20
间隔: 1天
下次截止: 2026-04-05 18:20
```

### Weekly (每周)
```
完成时间: 2026-04-04 18:20
间隔: 1周
下次截止: 2026-04-11 18:20
```

### Monthly (每月)
```
完成时间: 2026-04-04 18:20
间隔: 1个月
下次截止: 2026-05-04 18:20

特殊情况（月末）:
完成时间: 2026-01-31 18:20
间隔: 1个月
下次截止: 2026-02-28 18:20 (2月只有28天)
```

### Yearly (每年)
```
完成时间: 2026-04-04 18:20
间隔: 1年
下次截止: 2027-04-04 18:20

特殊情况（闰年）:
完成时间: 2024-02-29 18:20
间隔: 1年
下次截止: 2025-02-28 18:20 (2025不是闰年)
```

---

## 💡 使用场景

### 场景1: 每周内容审查
```
任务: Weekly Content Review
周期: Weekly, 间隔 1
优先级: High

流程:
周一: Pending → Start (开始审查)
周三: Complete (完成审查)
      ↓
下周一: 新任务自动出现 (Pending)
```

### 场景2: 每月数据备份
```
任务: Monthly Database Backup
周期: Monthly, 间隔 1
优先级: Urgent

流程:
1号: Pending → Start (开始备份)
2号: Complete (备份完成)
      ↓
下月1号: 新任务自动出现 (Pending)
```

### 场景3: 每日日志检查
```
任务: Daily Log Check
周期: Daily, 间隔 1
优先级: Medium

流程:
今天: Pending → Start → Complete
      ↓
明天: 新任务自动出现 (Pending)
```

---

## ✨ 优势

### 1. 自动化
- ✅ 无需手动创建下一个周期的任务
- ✅ 自动计算截止日期
- ✅ 自动继承所有属性

### 2. 清晰的状态
- ✅ 已完成的任务明确标记
- ✅ 新周期任务从 Pending 开始
- ✅ "This cycle completed" 提示

### 3. 灵活性
- ✅ 支持多种周期类型
- ✅ 可自定义间隔
- ✅ 可随时编辑或取消

### 4. 可追溯
- ✅ 保留所有历史实例
- ✅ 记录完成时间
- ✅ 可查看完成情况

---

## 🔍 常见问题

### Q1: 为什么新任务是 Pending 而不是直接开始？
**A:** 这样设计是为了给用户控制权。用户可以选择何时开始新周期的任务，而不是自动开始。

### Q2: 如果我不想继续这个周期性任务怎么办？
**A:** 可以：
- 点击 "❌ Cancel" 将任务移入回收站
- 或者点击 "🗑️ Delete" 永久删除
- 新周期不会再自动创建

### Q3: 如何查看历史完成的周期性任务？
**A:** 
- 使用筛选器选择 "Completed"
- 或在回收站查看已取消的任务
- Django Admin 中可以看到所有实例

### Q4: 周期性任务的标签会继承吗？
**A:** 是的，新实例会继承原任务的所有标签。

### Q5: 可以修改周期性任务的周期类型吗？
**A:** 目前需要通过编辑功能修改。修改后，下一次完成时会使用新的周期类型。

---

## 📝 最佳实践

### 1. 合理设置周期
- **Daily**: 日常检查、日志审查
- **Weekly**: 周报、内容审查、团队会议
- **Monthly**: 月度报告、数据备份、性能优化
- **Yearly**: 年度规划、域名续费、证书更新

### 2. 使用标签分类
```
标签示例:
- review, weekly
- backup, monthly
- maintenance, daily
- planning, yearly
```

### 3. 设置合适的优先级
- **Urgent**: 必须按时完成的关键任务
- **High**: 重要的周期性工作
- **Medium**: 常规维护任务
- **Low**: 可选的周期性检查

### 4. 定期检查
- 每周查看一次Todo列表
- 及时完成到期的周期性任务
- 清理不再需要的周期性任务

---

## 🚀 快速开始

1. **创建第一个周期性任务**
   ```
   标题: Weekly Blog Review
   勾选: Recurring Task
   周期: Weekly, 间隔 1
   优先级: High
   ```

2. **开始任务**
   ```
   点击: ▶️ Start
   ```

3. **完成任务**
   ```
   点击: ✅ Complete
   观察: "✓ This cycle completed" 提示
   ```

4. **等待下一周期**
   ```
   7天后: 新任务自动出现
   状态: Pending ⏳
   重复: Start → Complete 流程
   ```

---

**更新日期**: 2026-04-05  
**版本**: v1.2  
**状态**: ✅ 已实现并测试
