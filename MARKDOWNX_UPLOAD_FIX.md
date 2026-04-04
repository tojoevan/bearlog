# MarkdownX 图片上传 400 错误修复

## 问题描述

在浏览器控制台看到以下错误：
```
markdownx/upload/:1 Failed to load resource: the server responded with a status of 400 ()
```

## 根本原因

Django 缺少媒体文件（Media Files）配置，导致 MarkdownX 无法保存图片。

## 已完成的修复

### 1. 添加 MEDIA_ROOT 和 MEDIA_URL 配置

在 `conf/settings.py` 中添加：

```python
# Media files (for uploads)
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
```

### 2. 创建媒体目录

```bash
mkdir -p media/uploads
```

### 3. 更新 URL 配置

在 `conf/urls.py` 中添加：

```python
from django.conf.urls.static import static

# 在 DEBUG 模式下提供媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 4. 重启开发服务器

```bash
python manage.py runserver
```

## 验证修复

### 方法 1: 测试上传 API

在浏览器控制台中运行：

```javascript
// 创建一个测试图片
const canvas = document.createElement('canvas');
canvas.width = 100;
canvas.height = 100;
const ctx = canvas.getContext('2d');
ctx.fillStyle = 'red';
ctx.fillRect(0, 0, 100, 100);

canvas.toBlob(blob => {
    const formData = new FormData();
    formData.append('image', blob, 'test.png');
    
    fetch('/markdownx/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        }
    })
    .then(response => {
        console.log('Status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response:', data);
        if (data.image_code) {
            console.log('✅ Upload successful!');
            console.log('Image markdown:', data.image_code);
        } else {
            console.error('❌ Upload failed:', data);
        }
    })
    .catch(error => {
        console.error('❌ Error:', error);
    });
}, 'image/png');
```

应该返回：
```json
{
    "image_code": "![](/media/uploads/2026/04/04/test_xxxxxx.png)"
}
```

### 方法 2: 手动测试

1. 访问文章编辑页面：`/{blog-subdomain}/dashboard/posts/new/`
2. 点击 "Insert media" 或拖放图片到编辑器
3. 检查浏览器控制台是否有错误
4. 如果成功，应该看到图片的 Markdown 代码被插入

### 方法 3: 检查文件是否保存

```bash
ls -la media/uploads/$(date +%Y)/$(date +%m)/$(date +%d)/
```

应该能看到上传的图片文件。

## 常见问题

### 问题 1: 仍然返回 400 错误

**可能原因**: CSRF token 缺失或无效

**解决方案**:
1. 确保表单中有 `{% csrf_token %}`
2. 检查请求头中是否包含 `X-CSRFToken`

### 问题 2: 返回 403 Forbidden

**可能原因**: 权限问题

**解决方案**:
```bash
# 确保 media 目录有写权限
chmod -R 755 media/
```

### 问题 3: 返回 500 Internal Server Error

**可能原因**: 目录不存在或权限不足

**解决方案**:
```bash
# 创建目录
mkdir -p media/uploads

# 设置权限
chmod -R 755 media/
```

### 问题 4: 图片上传成功但无法显示

**可能原因**: 媒体文件 URL 配置不正确

**解决方案**:
1. 检查 `MEDIA_URL` 是否为 `/media/`
2. 确保 `urls.py` 中有 `static()` 配置
3. 访问 `http://127.0.0.1:8000/media/uploads/...` 测试

## 生产环境部署

在生产环境中，需要配置 Web 服务器（如 Nginx）来提供媒体文件：

### Nginx 配置示例

```nginx
location /media/ {
    alias /path/to/your/project/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Django 配置

确保 `settings.py` 中有：
```python
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
```

### 收集静态文件时包含媒体文件

注意：`collectstatic` **不会**处理媒体文件，媒体文件是用户上传的，需要单独管理。

## 安全注意事项

⚠️ **重要**: 在生产环境中，应该：

1. **限制上传文件大小**
   ```python
   MARKDOWNX_UPLOAD_MAX_SIZE = 52428800  # 50 MB
   ```

2. **验证文件类型**
   ```python
   MARKDOWNX_IMAGE_MAX_SIZE = {'size': (2000, 2000), 'quality': 90}
   ```

3. **使用安全的文件存储**
   - 考虑使用云存储（如 AWS S3、阿里云 OSS）
   - 不要将媒体文件放在项目目录中

4. **防止恶意文件上传**
   - 验证文件签名（不只是扩展名）
   - 重命名上传的文件
   - 扫描病毒

## 相关文件

- ✅ `conf/settings.py` - 添加了 MEDIA_ROOT 和 MEDIA_URL
- ✅ `conf/urls.py` - 添加了媒体文件 URL 路由
- ✅ `media/` - 创建了媒体文件目录
- ✅ `MARKDOWNX_SETUP.md` - 更新了部署说明

## 测试清单

- [ ] media 目录已创建
- [ ] MEDIA_ROOT 和 MEDIA_URL 已配置
- [ ] urls.py 已更新
- [ ] 开发服务器已重启
- [ ] 图片上传测试成功
- [ ] 上传的文件可以在浏览器中访问
- [ ] 控制台没有 400 错误
