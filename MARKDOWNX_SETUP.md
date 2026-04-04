# MarkdownX 集成说明

## 已完成的更改

### 1. 依赖安装
已在 `requirements.txt` 中添加:
```
django-markdownx==4.0.9
```

### 2. Django 设置更新
在 `conf/settings.py` 中:
- 添加 `'markdownx'` 到 `INSTALLED_APPS`
- 配置 MarkdownX 相关参数:
  - `MARKDOWNX_UPLOAD_URLS_PATH`: 图片上传路径
  - `MARKDOWNX_MARKDOWNIFY_URL`: Markdown 转换路径
  - `MARKDOWNX_MEDIA_PATH`: 媒体文件存储路径
  - `MARKDOWNX_UPLOAD_MAX_SIZE`: 最大上传大小 (50MB)
  - `MARKDOWNX_IMAGE_MAX_SIZE`: 图片最大尺寸
  - `MARKDOWNX_DEFAULT_ATTRIBUTES`: 默认编辑器属性

### 3. URL 配置
在 `conf/urls.py` 中添加:
```python
path('markdownx/', include('markdownx.urls')),
```

### 4. 模板更新

#### 4.1 文章编辑页面 (`templates/studio/post_edit.html`)
- 将传统 textarea 替换为 MarkdownX 编辑器
- 添加实时预览功能
- 保留原有的 header content 编辑功能
- 支持图片拖放上传
- 支持粘贴上传图片

#### 4.2 主页编辑页面 (`templates/studio/studio.html`)
- 将传统 textarea 替换为 MarkdownX 编辑器
- 添加实时预览功能
- 保留原有的 header content 编辑功能
- 支持图片拖放上传
- 支持粘贴上传图片

### 5. 编辑器功能
更新了 `templates/snippets/editor_functions.html`:
- 兼容 MarkdownX 和传统 textarea
- 保留草稿恢复功能
- 保留图片上传功能
- 保留键盘快捷键 (Ctrl/Cmd + S 保存)

## 使用方法

### 安装依赖
```bash
pip install -r requirements.txt
```

### 数据库迁移
```bash
python manage.py migrate
```

### 收集静态文件
```bash
python manage.py collectstatic
```

### 运行服务器
```bash
python manage.py runserver
```

## 功能特性

1. **Markdown 编辑**: 所见即所得的 Markdown 编辑体验
2. **实时预览**: 编辑时自动渲染 Markdown 预览
3. **图片上传**: 
   - 点击"Insert media"按钮上传
   - 拖放图片到编辑区域
   - 粘贴图片直接上传
4. **草稿恢复**: 意外关闭页面后可恢复未保存的草稿
5. **快捷键**: Ctrl/Cmd + S 快速保存

## 注意事项

- MarkdownX 会自动处理 CSRF token
- 图片上传会保存到 `MEDIA_ROOT/uploads/YYYY/MM/DD/`
- 编辑器内容会在表单提交时自动同步到隐藏的 textarea
- 保持与现有功能的兼容性（header content、草稿恢复等）

## 样式定制

可以通过以下方式定制编辑器样式:

1. 修改 `settings.py` 中的 `MARKDOWNX_DEFAULT_ATTRIBUTES`
2. 在模板中覆盖 `.markdownx-editor` 和 `.markdownx-preview` 的 CSS 样式
3. 使用 `data-markdownx-*` 属性配置编辑器行为

## 故障排除

### 图片上传失败
- 检查 `MEDIA_ROOT` 目录权限
- 确认 `MARKDOWNX_UPLOAD_MAX_SIZE` 设置
- 查看服务器日志

### 预览不显示
- 检查是否正确加载了 MarkdownX 的 JavaScript
- 确认网络请求未被阻止
- 检查浏览器控制台错误

### 编辑器样式问题
- 清除浏览器缓存
- 检查是否有 CSS 冲突
- 使用浏览器开发者工具调试
