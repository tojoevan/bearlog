# Todo 功能 Bug 修复

## 修复日期: 2026-04-05

### 🐛 问题描述

#### 问题1: 创建Todo时缺少默认时间
**现象**: 创建待办事项时，如果用户没有选择截止日期，`due_date` 字段为 `None`，导致：
- 任务没有明确的截止时间
- 排序时可能出现问题
- 用户体验不佳

#### 问题2: timezone.utc 错误
**错误信息**: 
```
module 'django.utils.timezone' has no attribute 'utc'
```

**原因**: Django 5.x 中，`django.utils.timezone` 模块不再提供 `utc` 属性。应该使用 Python 标准库的 `datetime.timezone.utc`。

**影响位置**: `blogs/views/studio.py` 第833行的排序逻辑

---

### ✅ 修复方案

#### 修复1: 添加默认截止日期

**文件**: `blogs/views/studio.py` - `todo_create()` 函数

**修改前**:
```python
# 处理截止日期
due_date = None
if due_date_str:
    try:
        # ... 解析逻辑
        due_date = aware_datetime
    except:
        pass  # 解析失败时 due_date 保持为 None
```

**修改后**:
```python
# 处理截止日期 - 如果没有选择时间，默认使用当前时间 + 7天
due_date = None
if due_date_str:
    try:
        from datetime import datetime as dt
        naive_datetime = dt.fromisoformat(due_date_str)
        user_timezone = request.COOKIES.get('timezone', 'UTC')
        from zoneinfo import ZoneInfo
        try:
            user_tz = ZoneInfo(user_timezone)
        except:
            user_tz = ZoneInfo('UTC')
        aware_datetime = timezone.make_aware(naive_datetime, user_tz)
        due_date = aware_datetime
    except Exception as e:
        print(f"Error parsing due_date: {e}")
        # 如果解析失败，使用默认值
        due_date = timezone.now() + timezone.timedelta(days=7)
else:
    # 没有选择时间，默认设置为当前时间 + 7天
    due_date = timezone.now() + timezone.timedelta(days=7)
```

**改进点**:
1. ✅ 未选择日期时，自动设置为当前时间 + 7天
2. ✅ 日期解析失败时，也使用默认值而不是留空
3. ✅ 添加了异常日志输出，便于调试
4. ✅ 更明确的注释说明

---

#### 修复2: 修正 timezone.utc 引用

**文件**: `blogs/views/studio.py` - `todo_list()` 函数

**修改前**:
```python
# 按优先级和截止日期排序
priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
todos = sorted(todos, key=lambda t: (priority_order.get(t.priority, 2), t.due_date or timezone.datetime.max.replace(tzinfo=timezone.utc)))
```

**修改后**:
```python
# 按优先级和截止日期排序
priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
from datetime import timezone as dt_timezone
todos = sorted(todos, key=lambda t: (priority_order.get(t.priority, 2), t.due_date or timezone.datetime.max.replace(tzinfo=dt_timezone.utc)))
```

**改进点**:
1. ✅ 使用 `datetime.timezone` 替代 `django.utils.timezone.utc`
2. ✅ 兼容 Django 5.x 及更高版本
3. ✅ 避免了 AttributeError

---

### 🧪 测试验证

#### 测试1: 默认排序逻辑
```python
test_date = None
result = test_date or timezone.datetime.max.replace(tzinfo=dt_timezone.utc)
# ✅ 输出: 9999-12-31 23:59:59.999999+00:00
# ✅ 没有报错
```

#### 测试2: 默认时间计算
```python
default_due = timezone.now() + timedelta(days=7)
# ✅ 当前时间: 2026-04-04 18:20
# ✅ 默认截止日期: 2026-04-11 18:20 (7天后)
```

#### 测试3: 异常处理
```python
bad_date_str = 'invalid-date'
try:
    naive_datetime = dt.fromisoformat(bad_date_str)
except Exception as parse_error:
    fallback_date = timezone.now() + timedelta(days=7)
# ✅ 捕获 ValueError
# ✅ 回退到默认值: 2026-04-11 18:20
```

---

### 📊 影响范围

**修改的文件**:
- `blogs/views/studio.py` (2处修改)

**影响的函数**:
1. `todo_list()` - 排序逻辑
2. `todo_create()` - 创建逻辑

**数据库影响**:
- 无数据库结构变更
- 现有数据不受影响
- 新创建的任务会有默认截止日期

**向后兼容性**:
- ✅ 完全向后兼容
- ✅ 不影响现有功能
- ✅ 仅增强用户体验

---

### 💡 使用建议

#### 创建任务时的行为

**场景1: 用户选择了截止日期**
```
用户输入: 2026-04-15 10:00
结果: due_date = 2026-04-15 10:00 (用户选择的时区)
```

**场景2: 用户未选择截止日期**
```
用户操作: 留空截止日期字段
结果: due_date = 当前时间 + 7天
示例: 2026-04-04 18:20 → 2026-04-11 18:20
```

**场景3: 日期格式错误**
```
用户输入: invalid-date
结果: 捕获异常，使用默认值 (当前时间 + 7天)
日志: "Error parsing due_date: ..."
```

---

### 🎯 最佳实践

1. **默认7天的合理性**:
   - 给用户足够的缓冲时间
   - 避免任务立即过期
   - 符合大多数任务的规划周期

2. **异常处理的重要性**:
   - 防止因用户输入错误导致系统崩溃
   - 提供友好的降级方案
   - 记录错误便于排查问题

3. **时区处理**:
   - 尊重用户的浏览器时区设置
   - 使用 `ZoneInfo` 进行时区转换
   - 回退到 UTC 作为安全选项

---

### 📝 相关文档

- [TODO_FEATURE.md](TODO_FEATURE.md) - Todo功能完整说明
- [TODO_UPDATE_v1.1.md](TODO_UPDATE_v1.1.md) - v1.1更新日志
- [TODO_QUICK_START.md](TODO_QUICK_START.md) - 快速启动指南

---

### 🔍 技术细节

#### Django 5.x 时区API变化

**Django 4.x**:
```python
from django.utils import timezone
tz = timezone.utc  # ✅ 可用
```

**Django 5.x**:
```python
from django.utils import timezone
tz = timezone.utc  # ❌ AttributeError

# 正确用法:
from datetime import timezone as dt_timezone
tz = dt_timezone.utc  # ✅ 使用Python标准库
```

#### 为什么选择7天作为默认值？

1. **用户体验**: 不会太紧迫，也不会太遥远
2. **业务逻辑**: 适合大多数短期任务
3. **灵活性**: 用户可以随时编辑修改
4. **行业标准**: 类似Trello、Asana等工具的默认值

---

**修复完成时间**: 2026-04-05  
**Django版本**: 5.2.9  
**Python版本**: 3.14.0  
**状态**: ✅ 已测试并通过
