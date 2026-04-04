# MarkdownX 编辑器说明

## ⚠️ 重要概念澄清

### MarkdownX **没有**工具栏按钮

MarkdownX 是一个 **Markdown 编辑器**，不是富文本编辑器（WYSIWYG）。

#### MarkdownX 的界面组成：

```
┌─────────────────────────────────────────────┐
│  编辑区 (textarea)      │  预览区 (preview)  │
│                         │                    │
│  # 标题                 │  标题              │
│  **粗体**               │  粗体              │
│  *斜体*                 │  斜体              │
│  - 列表项               │  • 列表项          │
│  [链接](url)           │  链接              │
│                         │                    │
└─────────────────────────────────────────────┘
```

- ✅ **左侧**：输入 Markdown 语法
- ✅ **右侧**：实时预览渲染效果
- ❌ **没有**：Bold、Italic、Heading 等工具栏按钮

### 如果你想要工具栏按钮...

你需要使用**富文本编辑器**（WYSIWYG），例如：

1. **Vditor**（项目中已有）
   - 位置：`/dashboard/posts/new/?vditor=true`
   - 或者点击 "Vditor editor" 按钮
   - 特点：有工具栏按钮，支持可视化编辑

2. **其他选择**：
   - TinyMCE
   - CKEditor
   - Quill
   - TipTap

## 📝 如何使用 MarkdownX

### 基本 Markdown 语法

```markdown
# 一级标题
## 二级标题
### 三级标题

**粗体文本**
*斜体文本*
***粗斜体***

- 无序列表项 1
- 无序列表项 2

1. 有序列表项 1
2. 有序列表项 2

[链接文本](https://example.com)

![图片描述](https://example.com/image.jpg)

> 引用文本

`行内代码`

```python
# 代码块
def hello():
    print("Hello, World!")
```

| 表格头1 | 表格头2 |
|--------|--------|
| 单元格1 | 单元格2 |
```

### 快捷键

- **Ctrl/Cmd + S**: 保存草稿
- **拖放图片**: 上传图片
- **粘贴图片**: 直接粘贴上传

## 🔍 调试 MarkdownX

### 检查编辑器是否正常加载

打开浏览器开发者工具 (F12)，查看 Console 标签：

```javascript
// 应该看到以下输出：
=== MarkdownX Debug Info ===
✅ MarkdownX library loaded
Editor element: ✅ Found
Preview element: ✅ Found
Container element: ✅ Found
Editor value length: XXX
Editor data attributes: {resizable: "true", uploadPath: "/markdownx/upload/", latency: "500"}
=== End Debug Info ===
```

### 如果看到错误

#### 1. MarkdownX is NOT loaded
```
❌ MarkdownX is NOT loaded!
```
**解决方案**：
- 清除浏览器缓存 (Ctrl+Shift+R / Cmd+Shift+R)
- 检查 `static/markdownx/js/markdownx.js` 是否存在
- 重启开发服务器

#### 2. Editor element: ❌ Not found
```
Editor element: ❌ Not found
```
**解决方案**：
- 确认你在正确的页面（编辑页面，不是列表页面）
- 检查模板中是否有 `.markdownx-editor` 类名的 textarea

#### 3. Preview element: ❌ Not found
```
Preview element: ❌ Not found
```
**解决方案**：
- 确认模板中有 `<div class="markdownx-preview">` 元素
- 检查 CSS 是否正确加载

## 🎨 自定义样式

可以通过 CSS 自定义编辑器外观：

```css
/* 编辑区样式 */
.markdownx-editor {
    width: 100%;
    min-height: 500px;
    border: 1px solid lightgrey;
    padding: 10px;
    font-family: 'Monaco', 'Courier New', monospace;
}

/* 预览区样式 */
.markdownx-preview {
    margin-top: 20px;
    padding: 10px;
    border: 1px solid #ddd;
    min-height: 200px;
    background-color: #f9f9f9;
}
```

## 📊 MarkdownX vs Vditor 对比

| 特性 | MarkdownX | Vditor |
|------|-----------|--------|
| **类型** | Markdown 编辑器 | 富文本编辑器 |
| **工具栏** | ❌ 无 | ✅ 有 |
| **实时预览** | ✅ 左右分屏 | ✅ 可选 |
| **学习曲线** | 需学 Markdown | 更直观 |
| **文件大小** | 较小 | 较大 |
| **适用场景** | 熟悉 Markdown 的用户 | 需要可视化的用户 |

## 💡 建议

### 如果你习惯 Markdown
✅ 继续使用 MarkdownX
- 更高效
- 更轻量
- 更好的版本控制

### 如果你不习惯 Markdown
✅ 使用 Vditor
- 有工具栏按钮
- 更直观的编辑体验
- 支持多种编辑模式

### 最佳实践
🎯 两者都提供，让用户选择
- 默认使用 MarkdownX（轻量、高效）
- 提供 Vditor 作为备选（可视化、易用）

## 🔗 相关资源

- [Markdown 语法指南](https://herman.bearblog.dev/markdown-cheatsheet/)
- [MarkdownX 文档](https://django-markdownx.readthedocs.io/)
- [Vditor 文档](https://b3log.org/vditor/)

## ❓ 常见问题

### Q: 为什么没有 Bold 按钮？
A: MarkdownX 是 Markdown 编辑器，使用 `**text**` 语法表示粗体，不需要按钮。

### Q: 如何插入图片？
A: 
1. 点击 "Insert media" 链接
2. 拖放图片到编辑区
3. 粘贴图片（Ctrl+V / Cmd+V）

### Q: 可以添加自定义工具栏吗？
A: MarkdownX 本身不支持，但你可以：
1. 切换到 Vditor（已有工具栏）
2. 或者创建自定义按钮，通过 JavaScript 插入 Markdown 语法

### Q: 预览区域不更新怎么办？
A: 
1. 检查浏览器控制台是否有错误
2. 确认 `/markdownx/markdownify/` API 可访问
3. 检查 Network 标签中的请求状态
