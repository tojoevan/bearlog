# Todo 功能更新日志

## v1.1 - 2026-04-05

### ✨ 新增功能

#### 1. **编辑按钮**
- ✅ 每个待办事项卡片添加"✏️ Edit"按钮
- ✅ 点击后展开内联编辑表单
- ✅ 支持修改：
  - 标题（Title）
  - 描述（Description）
  - 优先级（Priority）
  - 截止日期（Due Date）
  - 标签（Tags）
- ✅ 保存/取消操作

#### 2. **回收站功能**
- ✅ Cancelled的任务自动移入回收站
- ✅ 顶部导航栏显示回收站入口："🗑️ Trash (数量)"
- ✅ 统计面板中可点击的回收站卡片
- ✅ 回收站视图专用界面

#### 3. **恢复功能**
- ✅ 回收站中的任务可以恢复
- ✅ "♻️ Restore"按钮将任务状态改回Pending
- ✅ 恢复后任务重新出现在活动列表中

#### 4. **永久删除**
- ✅ 回收站中的任务可以永久删除
- ✅ 删除前有确认对话框
- ✅ "🗑️ Delete"按钮单个删除
- ✅ "🗑️ Empty Trash"按钮批量清空回收站

### 🎨 UI改进

#### 统计面板
- **活动视图**：显示 Total Active, Pending, In Progress, Completed, Overdue
- **回收站视图**：显示 In Trash 数量和返回按钮
- **快捷入口**：统计面板中的Trash卡片可直接点击进入回收站

#### 筛选器
- **活动视图**：按状态和优先级筛选
- **回收站视图**：显示"Back to Active Todos"返回链接
- **视图切换**：清晰的当前视图指示

#### 操作按钮
- **活动任务**：Edit, Start, Complete, Reopen, Cancel
- **回收站任务**：Restore, Delete
- **图标增强**：使用emoji提升可读性
  - ✏️ Edit
  - ▶️ Start
  - ✅ Complete
  - 🔄 Reopen
  - ❌ Cancel
  - ♻️ Restore
  - 🗑️ Delete

### 🔧 技术实现

#### 后端变更 (`blogs/views/studio.py`)

**todo_list() 视图增强：**
```python
# 新增 view_mode 参数支持
view_mode = request.GET.get('view', 'active')  # 'active' or 'trash'

# 回收站视图逻辑
if view_mode == 'trash':
    todos = todos.filter(status='cancelled')
    status_filter = 'cancelled'

# 统计信息增加 cancelled 计数
stats = {
    ...
    'cancelled': Todo.objects.filter(blog=blog, status='cancelled').count(),
    ...
}
```

**todo_update() 视图增强：**
```python
# 新增 restore 动作
elif action == 'restore':
    todo.status = 'pending'
    todo.completed_date = None
    todo.save()

# 新增 empty_trash 动作
elif action == 'empty_trash':
    Todo.objects.filter(blog=blog, status='cancelled').delete()
    return redirect('todo_list', id=blog.subdomain + '?view=trash')

# update 动作增加标签支持
tags_str = request.POST.get('tags', '')
tag_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
todo.tags = json.dumps(tag_list)
```

#### 前端变更 (`templates/studio/todo_list.html`)

**条件渲染：**
```html
{% if view_mode == 'trash' %}
    <!-- 回收站视图 -->
{% else %}
    <!-- 活动视图 -->
{% endif %}
```

**编辑表单：**
```html
<div id="edit-form-{{ todo.pk }}" class="todo-edit-form" style="display: none;">
    <form method="POST" action="{% url 'todo_update' id=blog.subdomain pk=todo.pk %}">
        <!-- 编辑字段 -->
    </form>
</div>
```

**JavaScript函数：**
```javascript
function toggleEditForm(todoId) {
    const form = document.getElementById('edit-form-' + todoId);
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
}
```

### 📊 工作流程

#### 取消任务流程
```
Active Todo → Click "❌ Cancel" → Status: cancelled
                                    ↓
                            Moved to Trash
```

#### 恢复任务流程
```
Trash View → Click "♻️ Restore" → Status: pending
                                   ↓
                            Back to Active List
```

#### 编辑任务流程
```
Click "✏️ Edit" → Form Expands → Modify Fields → 
    ↓                              ↓
  Save Changes              Cancel (Close Form)
    ↓
  Updated Todo
```

#### 清空回收站流程
```
Trash View → Click "🗑️ Empty Trash" → Confirmation Dialog →
    ↓                                       ↓
  Confirm                               Cancel
    ↓
All Cancelled Todos Deleted Permanently
```

### 🎯 使用场景

#### 场景1：误取消任务
1. 不小心取消了重要任务
2. 进入回收站（点击统计面板的Trash卡片）
3. 找到被取消的任务
4. 点击"♻️ Restore"恢复

#### 场景2：批量清理
1. 定期查看回收站
2. 确认不再需要的任务
3. 点击"🗑️ Empty Trash"清空所有

#### 场景3：修改任务详情
1. 任务优先级变化
2. 点击"✏️ Edit"
3. 修改优先级、截止日期等
4. 点击"💾 Save Changes"保存

### 💡 最佳实践

1. **定期清理回收站**：每周检查一次，永久删除不需要的任务
2. **谨慎使用Cancel**：取消前确认是否真的不需要该任务
3. **善用编辑功能**：任务信息变化时及时更新，保持准确性
4. **利用恢复功能**：误操作后可以快速恢复，无需重新创建

### 🔍 访问方式

**活动视图（默认）：**
```
/{blog_subdomain}/dashboard/todo/
或
/{blog_subdomain}/dashboard/todo/?view=active
```

**回收站视图：**
```
/{blog_subdomain}/dashboard/todo/?view=trash
```

### ⚠️ 注意事项

1. **回收站不是无限期的**：Cancelled任务会一直保留在回收站，直到手动删除
2. **永久删除不可恢复**：从回收站删除的任务无法恢复，请谨慎操作
3. **编辑不影响历史记录**：修改任务不会改变创建时间和完成时间
4. **周期性任务特殊处理**：完成的周期性任务会自动创建下一个实例，不会进入回收站

### 📝 文件变更清单

1. `blogs/views/studio.py` - 更新视图逻辑（+29行）
2. `templates/studio/todo_list.html` - 更新模板（+150行）

### 🚀 下一步计划

可能的未来增强：
- [ ] 回收站自动清理（如30天后自动删除）
- [ ] 任务版本历史（查看修改记录）
- [ ] 批量编辑功能
- [ ] 任务复制/克隆
- [ ] 导出/导入任务
- [ ] 任务评论/备注
- [ ] 附件支持

---

**更新日期**: 2026-04-05  
**版本**: v1.1  
**兼容性**: 完全向后兼容，不影响现有数据
