# MarkdownX 工具栏不显示 - 故障排除指南

## 问题描述

在 `/dashboard/posts/` 页面或文章编辑页面看不到 MarkdownX 的工具栏/编辑器。

## 重要说明

### `/dashboard/posts/` 页面

**这是文章列表页面，不是编辑页面！**

- ✅ 这个页面只显示文章列表
- ❌ 这个页面**不需要** MarkdownX 编辑器
- ✅ 点击"New post"或某篇文章标题后，才会进入编辑页面

### 编辑页面应该有 MarkdownX

当你访问以下页面时，应该看到 MarkdownX 编辑器：
- `/dashboard/posts/new/` - 新建文章
- `/dashboard/posts/{uid}/` - 编辑文章
- `/dashboard/` → 点击 "Home" - 编辑主页

## 故障排除步骤

### 1. 清除浏览器缓存

```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

或者在浏览器中：
- 打开开发者工具 (F12)
- 右键点击刷新按钮
- 选择"清空缓存并硬性重新加载"

### 2. 检查浏览器控制台错误

打开浏览器开发者工具 (F12)，查看 Console 标签：

```javascript
// 应该看到的日志（如果没有错误）
console.log('MarkdownX initialized')
```

如果看到错误，记录下来并提供给我。

### 3. 验证静态文件加载

在浏览器控制台中运行：

```javascript
// 检查 markdownx.js 是否加载
fetch('/static/markdownx/js/markdownx.js')
    .then(r => console.log('markdownx.js:', r.status))
    .catch(e => console.error('Error:', e));

// 检查 markdownx.css 是否加载
fetch('/static/markdownx/admin/css/markdownx.css')
    .then(r => console.log('markdownx.css:', r.status))
    .catch(e => console.error('Error:', e));
```

应该返回 HTTP 200。

### 4. 检查 MarkdownX 元素是否存在

在浏览器控制台中运行：

```javascript
// 检查编辑器元素
const editor = document.querySelector('.markdownx-editor');
console.log('Editor element:', editor);

// 检查预览区域
const preview = document.querySelector('.markdownx-preview');
console.log('Preview element:', preview);

// 检查 markdownx 容器
const container = document.querySelector('.markdownx');
console.log('Container:', container);
```

### 5. 手动初始化 MarkdownX

如果自动初始化失败，尝试手动初始化：

```javascript
// 在浏览器控制台中运行
if (typeof MarkdownX !== 'undefined') {
    const editors = document.querySelectorAll('.markdownx');
    editors.forEach(el => {
        new MarkdownX(el, el.querySelector('textarea'));
    });
    console.log('MarkdownX manually initialized');
} else {
    console.error('MarkdownX is not loaded');
}
```

### 6. 检查 Django 设置

确保 `conf/settings.py` 中有以下配置：

```python
INSTALLED_APPS = [
    # ...
    'markdownx',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MARKDOWNX_UPLOAD_URLS_PATH = '/markdownx/upload/'
MARKDOWNX_MARKDOWNIFY_URL = '/markdownx/markdownify/'
```

### 7. 检查 URL 配置

确保 `conf/urls.py` 中有：

```python
path('markdownx/', include('markdownx.urls')),
```

### 8. 重启开发服务器

```bash
# 停止服务器 (Ctrl+C)
# 然后重新启动
python manage.py runserver
```

## 常见问题

### 问题 1: 看到普通 textarea 而不是 MarkdownX 编辑器

**原因**: MarkdownX JavaScript 未加载或初始化失败

**解决方案**:
1. 检查浏览器控制台是否有错误
2. 确认 `markdownx.js` 文件可以访问
3. 清除浏览器缓存
4. 重启开发服务器

### 问题 2: 编辑器显示但没有实时预览

**原因**: MarkdownX 的 AJAX 请求失败

**解决方案**:
1. 检查 Network 标签，看 `/markdownx/markdownify/` 请求是否成功
2. 确认 CSRF token 正确配置
3. 检查服务器日志

### 问题 3: 图片上传失败

**原因**: 上传路径配置错误或权限问题

**解决方案**:
1. 检查 `MEDIA_ROOT` 目录权限
2. 确认 `MARKDOWNX_UPLOAD_URLS_PATH` 配置正确
3. 查看服务器错误日志

### 问题 4: 在生产环境不工作

**原因**: 静态文件未正确部署

**解决方案**:
```bash
# 部署静态文件
./deploy_markdownx_static.sh
python manage.py collectstatic --noinput
```

## 快速测试

访问测试页面验证 MarkdownX 是否正常工作：

```
http://127.0.0.1:8000/test_markdownx.html
```

这个页面会显示：
- ✅ JS 文件是否加载成功
- ✅ CSS 文件是否加载成功
- ✅ MarkdownX 编辑器是否正常初始化

## 需要帮助？

如果以上步骤都无法解决问题，请提供：

1. **浏览器控制台错误信息**（截图或文本）
2. **Network 标签中的请求状态**（特别是 markdownx.js 和 markdownify 请求）
3. **你访问的具体 URL**
4. **看到的是什么样的界面**（截图）
5. **Django 版本和 django-markdownx 版本**

```bash
python -c "import django; print('Django:', django.VERSION)"
python -c "import markdownx; print('MarkdownX:', markdownx.__version__)"
```
