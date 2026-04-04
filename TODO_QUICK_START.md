# Todo 功能 - 快速启动指南

## 🚀 立即体验

### 1. 启动开发服务器
```bash
cd /Users/joevan/kapibala/kapibala.icu
python manage.py runserver
```

### 2. 访问Todo页面

**方式一：使用测试账户**
- URL: http://127.0.0.1:8000/testblog/dashboard/todo/
- 用户名: `testuser`
- 密码: `testpass123`

**方式二：使用你自己的账户**
1. 登录你的账户
2. 进入任意Blog的仪表板
3. 点击导航栏中的 **"Todo"** 链接

### 3. 创建第一个待办事项

1. 点击 **"➕ Add New Todo"** 展开表单
2. 填写任务信息：
   - **Title**: "发布新文章"（必填）
   - **Description**: "完成本周的技术博客文章"
   - **Priority**: 选择 "High"
   - **Due Date**: 选择一个未来日期
   - **Tags**: "writing, blog, weekly"
3. 点击 **"Create Todo"**

### 4. 尝试周期性任务

1. 创建新任务："每周备份"
2. 勾选 **"Recurring Task"**
3. 设置：
   - Repeat Every: "Week(s)"
   - Interval: 1
4. 完成任务后，系统会自动创建下周的任务

## 📋 功能速览

### 任务状态流程
```
⏳ Pending (待处理)
    ↓ [Start]
🔄 In Progress (进行中)
    ↓ [Complete]
✅ Completed (已完成)
    
或者：
    ↓ [Cancel]
❌ Cancelled (已取消)
```

### 操作按钮说明
- **Start**: 开始处理任务（pending → in_progress）
- **Complete**: 完成任务（任何状态 → completed）
- **Cancel**: 取消任务（任何状态 → cancelled）
- **Reopen**: 重新打开（completed/cancelled → pending）
- **Delete**: 删除任务（需要确认）

### 筛选器使用
- **按状态**: 查看特定状态的任务
- **按优先级**: 聚焦高优先级任务
- **清除筛选**: 返回默认视图

## 🎯 使用场景示例

### 场景1: 内容创作计划
```
标题: 撰写技术教程
优先级: High
截止日期: 本周五
标签: writing, tutorial, python
描述: 完成Django进阶教程的第一部分
```

### 场景2: 定期维护任务
```
标题: 数据库备份
优先级: Urgent
周期性: 每天
标签: maintenance, backup
描述: 每日自动备份数据库
```

### 场景3: 月度审查
```
标题: 月度数据分析
优先级: Medium
周期性: 每月，间隔1
标签: analytics, review
描述: 分析上月网站数据和用户反馈
```

## 💡 最佳实践

### 1. 优先级使用建议
- **Urgent**: 今天必须完成的任务
- **High**: 本周内需要完成
- **Medium**: 常规任务，有缓冲时间
- **Low**: 有空时再做

### 2. 标签策略
- 按项目分类: `project-a`, `project-b`
- 按类型分类: `writing`, `coding`, `review`
- 按时间分类: `daily`, `weekly`, `monthly`

### 3. 周期性任务示例
- 每日: 数据备份、日志检查
- 每周: 内容审查、性能优化
- 每月: 数据分析、安全审计
- 每年: 域名续费、证书更新

## 🔍 常见问题

### Q: 如何查看已完成的任务？
A: 使用状态筛选器，选择 "Completed"

### Q: 周期性任务完成后会发生什么？
A: 当前任务标记为完成，同时自动创建下一个周期的新任务

### Q: 可以编辑已创建的任务吗？
A: 目前可以通过Django Admin编辑，后续会添加前端编辑功能

### Q: 任务会过期吗？
A: 任务不会自动删除，但逾期的任务会以红色边框高亮显示

### Q: 不同Blog的任务会混在一起吗？
A: 不会，每个Blog有完全独立的任务列表

## 🛠️ 管理后台

超级用户可以访问 Django Admin 进行高级管理：

1. 访问: http://127.0.0.1:8000/admin/
2. 找到 "Blogs" → "Todos"
3. 可以：
   - 查看所有用户的任务
   - 批量操作
   - 导出数据
   - 高级筛选

## 📊 统计面板解读

- **Total Active**: 当前活动任务总数（不包括已完成和已取消）
- **Pending**: 等待开始的任务
- **In Progress**: 正在进行的任务
- **Completed**: 已完成的任务历史
- **Overdue**: 已过截止日期的任务（如果有）

## 🎨 界面元素说明

### 徽章颜色
- 🔴 红色: Urgent 优先级或逾期任务
- 🟠 橙色: High 优先级
- 🔵 蓝色: Medium 优先级
- 🟢 绿色: Low 优先级或已完成任务

### 图标含义
- ⏳ 待处理
- 🔄 进行中
- ✅ 已完成
- ❌ 已取消
- 🔁 周期性任务
- 📅 截止日期
- ⚠️ 逾期警告

## 📝 下一步

1. ✅ 熟悉基本操作
2. ✅ 创建你的第一个任务列表
3. ✅ 尝试周期性任务
4. ✅ 使用标签组织任务
5. 🔄 定期检查并完成的任务

## 🆘 需要帮助？

- 查看详细文档: `TODO_FEATURE.md`
- 技术实现细节: `TODO_IMPLEMENTATION_SUMMARY.md`
- 运行测试脚本: `python test_todo.py`

---

**祝使用愉快！** 🎉
