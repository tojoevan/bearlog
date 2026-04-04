# MarkdownX "NOT loaded" 错误修复

## 问题描述

在浏览器控制台看到以下错误：
```
❌ MarkdownX is NOT loaded!
```

## 根本原因分析

这个错误通常由以下原因之一引起：

1. **脚本加载时序问题** - JavaScript 在 MarkdownX 库完全加载之前执行
2. **浏览器缓存** - 浏览器缓存了旧版本的页面或脚本
3. **网络问题** - 脚本文件加载失败（404、CORS 等）
4. **脚本执行错误** - 脚本加载成功但执行时出错

## 已完成的修复

### 1. 添加延迟检查

在 `studio.html` 和 `post_edit.html` 中添加了 100ms 延迟，等待 MarkdownX 初始化：

```javascript
setTimeout(() => {
    if (typeof MarkdownX === 'undefined') {
        console.error('❌ MarkdownX is NOT loaded!');
        // 尝试重新加载
    } else {
        console.log('✅ MarkdownX library loaded');
    }
}, 100);
```

### 2. 添加自动重试机制

如果检测到 MarkdownX 未加载，会自动尝试重新加载脚本：

```javascript
const script = document.createElement('script');
script.src = '/static/markdownx/js/markdownx.js';
script.onload = () => {
    console.log('✅ Script reloaded successfully');
};
document.head.appendChild(script);
```

### 3. 增强调试信息

添加了详细的调试输出：
- 脚本标签执行时的状态
- DOMContentLoaded 事件触发
- MarkdownX 对象是否存在
- 编辑器元素是否找到
- Data 属性是否正确设置

## 故障排除步骤

### 步骤 1: 清除浏览器缓存

**最重要的一步！**

```
Windows/Linux: Ctrl+Shift+R
Mac: Cmd+Shift+R
```

或者：
1. 打开开发者工具 (F12)
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

### 步骤 2: 检查 Network 标签

1. 打开开发者工具 (F12)
2. 切换到 **Network** 标签
3. 刷新页面
4. 查找 `markdownx.js`
5. 检查状态码：
   - ✅ **200** - 文件加载成功
   - ❌ **404** - 文件未找到
   - ❌ **403** - 权限被拒绝
   - ❌ **(failed)** - 网络错误

### 步骤 3: 检查 Console 输出

应该看到以下日志：

```
Script tag executed, checking MarkdownX...
typeof MarkdownX: function
=== MarkdownX Debug Info ===
DOM Content Loaded
✅ MarkdownX library loaded
MarkdownX version: unknown
Editor element: ✅ Found
Preview element: ✅ Found
Container element: ✅ Found
=== End Debug Info ===
```

如果看到：
```
❌ MarkdownX is NOT loaded!
Attempting to reload markdownx.js...
✅ Script reloaded successfully
typeof MarkdownX after reload: function
```

这说明第一次加载失败，但重试成功了。

### 步骤 4: 手动测试脚本加载

在浏览器控制台中运行：

```javascript
// 检查文件是否可以访问
fetch('/static/markdownx/js/markdownx.js')
    .then(r => {
        console.log('Status:', r.status);
        return r.text();
    })
    .then(text => {
        console.log('File length:', text.length);
        console.log('First 100 chars:', text.substring(0, 100));
    })
    .catch(e => console.error('Error:', e));
```

应该返回文件内容。

### 步骤 5: 检查服务器日志

查看 Django 开发服务器的输出：

```bash
[04/Apr/2026 XX:XX:XX] "GET /static/markdownx/js/markdownx.js HTTP/1.1" 200 XXXXX
```

- ✅ **200** - 请求成功
- ❌ **404** - 文件未找到
- ❌ **其他** - 查看具体错误

## 常见原因和解决方案

### 原因 1: 浏览器缓存

**症状**: 文件存在但仍显示未加载

**解决方案**:
```bash
# 方法 1: 硬刷新
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)

# 方法 2: 禁用缓存
# 1. 打开 DevTools
# 2. 切换到 Network 标签
# 3. 勾选 "Disable cache"
# 4. 刷新页面
```

### 原因 2: 静态文件未收集

**症状**: 404 错误

**解决方案**:
```bash
# 开发环境
python manage.py runserver

# 生产环境
./deploy_markdownx_static.sh
python manage.py collectstatic --noinput
```

### 原因 3: STATICFILES_FINDERS 配置缺失

**症状**: 开发环境下 404

**解决方案**:
确保 `settings.py` 中有：
```python
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
```

### 原因 4: 脚本加载顺序问题

**症状**: 脚本加载成功但 MarkdownX 未定义

**解决方案**:
使用 `defer` 或 `async` 属性：
```html
<script src="{% static 'markdownx/js/markdownx.js' %}" defer></script>
```

或在 `DOMContentLoaded` 事件中初始化。

### 原因 5: CORS 问题

**症状**: 跨域错误

**解决方案**:
确保 `settings.py` 中有：
```python
CORS_ALLOW_ALL_ORIGINS = True  # 开发环境
# 或
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
]
```

## 验证修复

### 测试清单

- [ ] 清除了浏览器缓存
- [ ] Network 标签显示 markdownx.js 返回 200
- [ ] Console 显示 "✅ MarkdownX library loaded"
- [ ] Editor element: ✅ Found
- [ ] Preview element: ✅ Found
- [ ] 可以看到左右分屏的编辑器界面
- [ ] 输入 Markdown 后右侧实时预览

### 快速测试

访问测试页面：
```
http://127.0.0.1:8000/test_markdownx.html
```

应该看到：
- ✅ JS 文件加载成功
- ✅ CSS 文件加载成功
- ✅ MarkdownX 编辑器正常显示

## 高级调试

### 检查 MarkdownX 对象

在控制台中运行：
```javascript
console.log('MarkdownX:', MarkdownX);
console.log('MarkdownX prototype:', MarkdownX.prototype);
console.log('Window properties:', Object.keys(window).filter(k => k.includes('markdown')));
```

### 检查脚本内容

```javascript
fetch('/static/markdownx/js/markdownx.js')
    .then(r => r.text())
    .then(text => {
        // 检查是否包含 MarkdownX 定义
        console.log('Contains MarkdownX:', text.includes('MarkdownX'));
        console.log('File size:', text.length, 'bytes');
    });
```

### 手动初始化

如果自动初始化失败，尝试手动初始化：

```javascript
const containers = document.querySelectorAll('.markdownx');
containers.forEach(container => {
    const textarea = container.querySelector('textarea');
    if (textarea && typeof MarkdownX !== 'undefined') {
        new MarkdownX(container, textarea);
        console.log('Manually initialized MarkdownX');
    }
});
```

## 相关文件

- ✅ `templates/studio/studio.html` - 添加了延迟检查和重试
- ✅ `templates/studio/post_edit.html` - 添加了延迟检查和重试
- ✅ `conf/settings.py` - 确保 STATICFILES_FINDERS 配置正确
- ✅ `test_markdownx.html` - 测试页面

## 如果问题仍然存在

请提供以下信息：

1. **完整的 Console 输出**（截图或文本）
2. **Network 标签中 markdownx.js 的状态**
3. **浏览器和版本**
4. **操作系统**
5. **Django 版本**
6. **django-markdownx 版本**

```bash
python -c "import django; print('Django:', django.VERSION)"
python -c "import markdownx; print('MarkdownX:', markdownx.__version__)"
```
