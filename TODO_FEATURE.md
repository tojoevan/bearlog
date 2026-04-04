# Todo 待办事项功能说明

## 功能概述

为每个Blog添加了独立的待办事项跟踪系统，支持：
- ✅ 多用户场景（每个用户可有多个Blog）
- ✅ 每个Blog有独立的待办事项列表
- ✅ 任务状态管理（待处理、进行中、已完成、已取消）
- ✅ 优先级设置（低、中、高、紧急）
- ✅ 周期性任务支持（每天、每周、每月、每年）
- ✅ 截止日期提醒
- ✅ 标签分类
- ✅ 统计面板

## 数据库设计

### Todo 模型字段说明

```python
class Todo(models.Model):
    # 关联到具体的Blog
    blog = ForeignKey(Blog)
    
    # 基本信息
    title = CharField(max_length=200)           # 标题
    description = TextField(blank=True)          # 描述
    
    # 状态管理
    status = CharField(choices=[
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ])
    
    # 优先级
    priority = CharField(choices=[
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ])
    
    # 时间相关
    created_date = DateTimeField(auto_now_add=True)     # 创建时间
    last_modified = DateTimeField(auto_now=True)        # 最后修改时间
    due_date = DateTimeField(blank=True, null=True)     # 截止日期
    completed_date = DateTimeField(blank=True, null=True) # 完成日期
    
    # 周期性任务配置
    is_recurring = BooleanField(default=False)          # 是否周期性任务
    recurring_type = CharField(choices=[
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('yearly', '每年'),
        ('custom', '自定义'),
    ], blank=True, null=True)
    recurring_interval = IntegerField(default=1)        # 周期间隔
    next_occurrence = DateTimeField(blank=True, null=True) # 下次出现时间
    
    # 标签和排序
    tags = TextField(default='[]')                      # 标签（JSON格式）
    order = IntegerField(default=0)                     # 排序
```

## 使用方法

### 1. 访问Todo页面

在任意Blog的仪表板导航栏中，点击 **Todo** 菜单项即可进入该Blog的待办事项页面。

URL格式：`/{blog_subdomain}/dashboard/todo/`

### 2. 创建待办事项

点击 "➕ Add New Todo" 展开表单，填写以下信息：

- **Title**（必填）：任务标题
- **Description**（可选）：任务详细描述
- **Priority**：选择优先级（低/中/高/紧急）
- **Due Date**：设置截止日期和时间
- **Recurring Task**：勾选后启用周期性任务
  - **Repeat Every**：选择周期类型（天/周/月/年）
  - **Interval**：设置间隔数量
- **Tags**：添加标签，用逗号分隔（如：work, important, review）

### 3. 管理待办事项

每个待办事项卡片显示：
- 任务标题和状态图标
- 优先级徽章
- 状态徽章
- 截止日期（如果设置）
- 标签列表
- 操作按钮

**可用操作：**
- **Start**：将任务状态改为"进行中"
- **Complete**：完成任务
  - 如果是周期性任务，会自动创建下一个周期的任务实例
- **Cancel**：取消任务
- **Reopen**：重新打开已完成或已取消的任务
- **Delete**：删除任务（需确认）

### 4. 筛选和排序

页面顶部提供筛选器：
- **按状态筛选**：全部活动/待处理/进行中/已完成/已取消
- **按优先级筛选**：全部优先级/紧急/高/中/低

默认视图不显示已完成和已取消的任务，可通过筛选器查看。

### 5. 统计面板

页面顶部显示统计信息：
- Total Active：当前活动任务总数
- Pending：待处理任务数
- In Progress：进行中任务数
- Completed：已完成任务数
- Overdue：逾期任务数（如果有）

## 周期性任务工作原理

当标记一个任务为周期性任务并完成时：

1. 当前任务状态变为"已完成"
2. 系统自动创建一个新的待办事项实例
3. 新任务的截止日期根据周期类型和间隔自动计算
4. 新任务继承原任务的所有属性（标题、描述、优先级、标签等）

**周期计算示例：**
- 每天重复，间隔2天 → 每2天创建一次
- 每周重复，间隔1周 → 每周创建一次
- 每月重复，间隔3个月 → 每3个月创建一次
- 每年重复，间隔1年 → 每年创建一次

## Django Admin 管理

超级用户可以在Django管理后台（/admin/）管理所有待办事项：

- 查看所有用户的待办事项
- 按Blog、状态、优先级等筛选
- 批量操作
- 编辑和删除任务

## 技术实现

### URL路由
```python
path('<id>/dashboard/todo/', studio.todo_list, name='todo_list')
path('<id>/dashboard/todo/create/', studio.todo_create, name='todo_create')
path('<id>/dashboard/todo/<int:pk>/update/', studio.todo_update, name='todo_update')
```

### 视图函数
- `todo_list()`: 显示待办事项列表，支持筛选
- `todo_create()`: 创建新的待办事项
- `todo_update()`: 更新待办事项状态和信息

### 模板
- `templates/studio/todo_list.html`: 待办事项列表页面

## 注意事项

1. **权限控制**：只有Blog的所有者或超级用户可以访问该Blog的待办事项
2. **数据隔离**：每个Blog的待办事项完全独立，互不影响
3. **时区处理**：截止日期会根据用户浏览器的时区Cookie自动转换
4. **性能优化**：数据库添加了适当的索引以优化查询性能

## 未来扩展建议

可以考虑添加的功能：
- [ ] 任务提醒通知（邮件或站内通知）
- [ ] 任务附件支持
- [ ] 任务评论/讨论
- [ ] 任务分配（多人协作）
- [ ] 任务依赖关系
- [ ] 甘特图视图
- [ ] 导出/导入功能
- [ ] 任务模板
- [ ] 子任务支持
- [ ] 任务进度百分比
