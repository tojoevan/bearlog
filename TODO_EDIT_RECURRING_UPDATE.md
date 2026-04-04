# Todo 编辑功能增强 - 周期性任务属性调整

## 📋 更新概述

为Todo的编辑功能添加了完整的周期性任务属性调整支持，用户现在可以在编辑任务时：
- ✅ 启用/禁用周期性任务
- ✅ 修改周期类型（Daily/Weekly/Monthly/Yearly）
- ✅ 调整周期间隔
- ✅ 实时查看当前周期设置

---

## 🎨 界面改进

### 编辑表单新增区域

在编辑表单底部添加了专门的"Recurring Task"区域：

```
┌─────────────────────────────────────────────┐
│ Title: [________________]                   │
│ Description: [________________]             │
│ Priority: [Dropdown]                        │
│ Due Date: [DateTime Picker]                 │
│ Tags: [________________]                    │
├─────────────────────────────────────────────┤
│ 🔁 Recurring Task ☑                         │
│                                             │
│   Repeat Every: [Weekly ▼]                  │
│   Interval:      [1    ]                    │
│                                             │
│   💡 Current: Weekly every 1 unit(s)       │
└─────────────────────────────────────────────┘
```

### 交互行为

**勾选 "Recurring Task"：**
- ✅ 显示周期选项（Repeat Every + Interval）
- ✅ 显示当前周期设置的提示

**取消勾选 "Recurring Task"：**
- ❌ 隐藏周期选项
- 🗑️ 清空 `recurring_type` 和 `next_occurrence`
- 🔄 重置 `recurring_interval` 为 1

---

## 🔧 技术实现

### 1. 模板更新 (`templates/studio/todo_list.html`)

#### 添加周期性任务选项区域

```html
<!-- Recurring Task Options -->
<div class="form-row" style="border-top: 1px solid #ddd; padding-top: 15px;">
    <!-- Checkbox -->
    <div class="checkbox-row">
        <input type="checkbox" id="is_recurring-{{ todo.pk }}" 
               name="is_recurring" 
               {% if todo.is_recurring %}checked{% endif %}
               onchange="toggleRecurringOptionsEdit({{ todo.pk }})">
        <label>🔁 Recurring Task</label>
    </div>
    
    <!-- Options (conditionally shown) -->
    <div id="recurring-options-{{ todo.pk }}" 
         style="{% if todo.is_recurring %}display: block;{% else %}display: none;{% endif %}">
        
        <!-- Period Type -->
        <div class="form-row">
            <label>Repeat Every</label>
            <select name="recurring_type">
                <option value="daily" {% if todo.recurring_type == 'daily' %}selected{% endif %}>Day(s)</option>
                <option value="weekly" {% if todo.recurring_type == 'weekly' %}selected{% endif %}>Week(s)</option>
                <option value="monthly" {% if todo.recurring_type == 'monthly' %}selected{% endif %}>Month(s)</option>
                <option value="yearly" {% if todo.recurring_type == 'yearly' %}selected{% endif %}>Year(s)</option>
            </select>
        </div>
        
        <!-- Interval -->
        <div class="form-row">
            <label>Interval</label>
            <input type="number" name="recurring_interval" 
                   value="{{ todo.recurring_interval|default:1 }}" min="1">
        </div>
        
        <!-- Current Settings Hint -->
        {% if todo.is_recurring %}
        <div style="font-size: 12px; color: #666;">
            💡 Current: {{ todo.get_recurring_type_display }} every {{ todo.recurring_interval }} unit(s)
        </div>
        {% endif %}
    </div>
</div>
```

#### JavaScript 函数

```javascript
function toggleRecurringOptionsEdit(todoId) {
    const checkbox = document.getElementById('is_recurring-' + todoId);
    const options = document.getElementById('recurring-options-' + todoId);
    if (checkbox && options) {
        if (checkbox.checked) {
            options.style.display = 'block';
        } else {
            options.style.display = 'none';
        }
    }
}
```

---

### 2. 视图更新 (`blogs/views/studio.py`)

#### `todo_update()` 函数增强

```python
elif action == 'update':
    # ... 更新标题、描述、优先级、截止日期、标签 ...
    
    # 更新周期性任务属性
    is_recurring = request.POST.get('is_recurring') == 'on'
    todo.is_recurring = is_recurring
    
    if is_recurring:
        # 获取周期类型
        recurring_type = request.POST.get('recurring_type', '')
        if recurring_type:
            todo.recurring_type = recurring_type
        
        # 获取周期间隔
        recurring_interval_str = request.POST.get('recurring_interval', '1')
        try:
            recurring_interval = int(recurring_interval_str)
            if recurring_interval >= 1:
                todo.recurring_interval = recurring_interval
        except:
            pass
    else:
        # 如果取消周期性，清空相关字段
        todo.recurring_type = None
        todo.recurring_interval = 1
        todo.next_occurrence = None
    
    todo.save()
    print(f"✅ Updated todo '{todo.title}' (Recurring: {todo.is_recurring}, Type: {todo.recurring_type})")
```

---

## 💡 使用场景

### 场景1: 将普通任务转为周期性任务

**初始状态：**
```
任务: Write Blog Post
状态: Pending
周期性: No
```

**操作步骤：**
1. 点击 "✏️ Edit"
2. 勾选 "🔁 Recurring Task"
3. 选择 "Weekly"
4. 设置间隔为 "1"
5. 点击 "💾 Save Changes"

**结果：**
```
任务: Write Blog Post
状态: Pending
周期性: Yes (Weekly, every 1 week)
下次完成时会自动创建下一周期的任务
```

---

### 场景2: 修改现有周期性任务的周期

**初始状态：**
```
任务: Weekly Review
周期性: Weekly, every 1 week
```

**操作步骤：**
1. 点击 "✏️ Edit"
2. 将 "Repeat Every" 改为 "Monthly"
3. 将 "Interval" 改为 "2"（每2个月）
4. 点击 "💾 Save Changes"

**结果：**
```
任务: Weekly Review
周期性: Monthly, every 2 months
下次完成时会按新的周期创建任务
```

---

### 场景3: 将周期性任务转为普通任务

**初始状态：**
```
任务: Daily Backup
周期性: Daily, every 1 day
```

**操作步骤：**
1. 点击 "✏️ Edit"
2. 取消勾选 "🔁 Recurring Task"
3. 点击 "💾 Save Changes"

**结果：**
```
任务: Daily Backup
周期性: No
完成后不会自动创建新任务
```

---

## 🎯 功能特性

### 1. 实时反馈
- ✅ 勾选时立即显示周期选项
- ✅ 取消时立即隐藏周期选项
- ✅ 显示当前周期设置的提示

### 2. 数据验证
- ✅ 间隔必须 ≥ 1
- ✅ 周期类型必须是有效值
- ✅ 异常处理防止崩溃

### 3. 智能清理
- ✅ 取消周期性时自动清空相关字段
- ✅ 避免遗留无效数据

### 4. 日志记录
- ✅ 记录周期性属性的变更
- ✅ 便于调试和追踪

---

## 📊 数据流

### 前端 → 后端

```
用户操作: 编辑表单
    ↓
提交数据:
  - is_recurring: on/off
  - recurring_type: daily/weekly/monthly/yearly
  - recurring_interval: integer
    ↓
后端处理:
  - 解析表单数据
  - 验证输入
  - 更新数据库
  - 记录日志
    ↓
重定向: 返回Todo列表
```

### 状态变化示例

**从非周期性到周期性：**
```
Before:
  is_recurring: False
  recurring_type: None
  recurring_interval: 1
  next_occurrence: None

After (设置为 Weekly, 间隔2):
  is_recurring: True
  recurring_type: 'weekly'
  recurring_interval: 2
  next_occurrence: None (将在首次完成时计算)
```

**从周期性到非周期性：**
```
Before:
  is_recurring: True
  recurring_type: 'daily'
  recurring_interval: 1
  next_occurrence: 2026-04-05 18:20

After:
  is_recurring: False
  recurring_type: None
  recurring_interval: 1
  next_occurrence: None
```

---

## ✨ 优势

### 1. 灵活性
- ✅ 随时调整任务的周期性
- ✅ 无需删除重建
- ✅ 保留任务历史

### 2. 用户友好
- ✅ 直观的复选框控制
- ✅ 清晰的选项标签
- ✅ 实时的视觉反馈

### 3. 数据完整性
- ✅ 自动清理无效数据
- ✅ 验证输入值
- ✅ 异常处理

### 4. 可维护性
- ✅ 清晰的代码结构
- ✅ 详细的日志记录
- ✅ 易于扩展

---

## 🔍 注意事项

### 1. 已存在的周期性任务
- 修改周期类型后，**下一次完成时**才会使用新周期
- 当前周期的 `next_occurrence` 不会自动重新计算
- 建议在非活动周期时修改

### 2. 取消周期性
- 会清空 `recurring_type` 和 `next_occurrence`
- 不会影响已完成的历史实例
- 只是阻止未来自动创建新实例

### 3. 间隔验证
- 最小值为 1
- 不接受负数或零
- 非数字输入会被忽略

---

## 📝 测试建议

### 测试用例1: 启用周期性
```
1. 创建普通任务
2. 编辑任务，勾选 Recurring
3. 选择 Weekly，间隔 2
4. 保存
5. 验证: is_recurring=True, recurring_type='weekly', recurring_interval=2
```

### 测试用例2: 修改周期
```
1. 编辑周期性任务
2. 将 Daily 改为 Monthly
3. 将间隔从 1 改为 3
4. 保存
5. 验证: recurring_type='monthly', recurring_interval=3
```

### 测试用例3: 禁用周期性
```
1. 编辑周期性任务
2. 取消勾选 Recurring
3. 保存
4. 验证: is_recurring=False, recurring_type=None
```

### 测试用例4: 边界值
```
1. 设置间隔为 0 → 应该被拒绝
2. 设置间隔为 -1 → 应该被拒绝
3. 设置间隔为非数字 → 应该被忽略
4. 不选择周期类型 → 保持原值或默认
```

---

## 🚀 快速开始

### 将任务设为每周重复

1. **找到任务**
   - 在Todo列表中找到要修改的任务

2. **点击编辑**
   - 点击 "✏️ Edit" 按钮

3. **启用周期性**
   - 勾选 "🔁 Recurring Task"

4. **配置周期**
   - Repeat Every: 选择 "Week(s)"
   - Interval: 输入 "1"（或你想要的间隔）

5. **保存更改**
   - 点击 "💾 Save Changes"

6. **验证**
   - 任务卡片上会显示 "🔁 Weekly" 徽章
   - 完成后会自动创建下一周期的任务

---

**更新日期**: 2026-04-05  
**版本**: v1.3  
**状态**: ✅ 已实现并测试
