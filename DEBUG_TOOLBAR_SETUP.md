# Django Debug Toolbar 配置说明

## 概述

Django Debug Toolbar 是一个强大的调试工具，可以在开发和生产环境中提供详细的调试信息。

## 安装

Debug Toolbar 已经在 `requirements.txt` 中配置：
```
django-debug-toolbar==5.0.1
```

安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

### 1. settings.py 配置

已在 `conf/settings.py` 中完成以下配置：

#### INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
    # ...
]
```

#### MIDDLEWARE
```python
MIDDLEWARE = [
    # ...
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # 必须在 SessionMiddleware 之后
    # ...
]
```

#### INTERNAL_IPS
```python
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]
```

#### DEBUG_TOOLBAR_CONFIG
```python
if DEBUG:
    def show_toolbar(request):
        return True
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    }
```

**重要**: `show_toolbar` 回调函数允许在任何 IP 地址上显示 Debug Toolbar，而不仅限于 `INTERNAL_IPS`。这在生产环境开启 DEBUG 时非常有用。

### 2. urls.py 配置

已在 `conf/urls.py` 中添加：
```python
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

## 静态文件管理

### 开发环境 (DEBUG=True)

在开发环境下，Django 会通过 `AppDirectoriesFinder` 自动从 django-debug-toolbar 包中查找静态文件，**不需要**手动复制。

### 生产环境 (DEBUG=False 或 DEBUG=True)

在生产环境部署时，需要确保 Debug Toolbar 的静态文件存在于 `static/debug_toolbar/` 目录：

#### 方法 1: 使用部署脚本（推荐）
```bash
./deploy_debug_toolbar_static.sh
```

#### 方法 2: 使用 Makefile
```bash
make deploy-static
```

#### 方法 3: 手动复制
```bash
cp -R $(python -c "import debug_toolbar; import os; print(os.path.dirname(debug_toolbar.__file__))")/static/debug_toolbar static/
```

#### 方法 4: 运行 collectstatic
```bash
python manage.py collectstatic --noinput
```

## 部署流程

### 完整的生产环境部署步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 部署第三方包的静态文件
./deploy_markdownx_static.sh
./deploy_debug_toolbar_static.sh

# 3. 收集所有静态文件到 staticfiles/
python manage.py collectstatic --noinput

# 4. 运行数据库迁移
python manage.py migrate

# 5. 启动服务器
gunicorn conf.wsgi:application
```

### 使用 Makefile 简化部署

```bash
make deploy-static
```

这会自动执行：
- 部署 MarkdownX 静态文件
- 部署 Debug Toolbar 静态文件
- 运行 collectstatic

## 验证安装

### 1. 检查静态文件是否存在

```bash
ls -la static/debug_toolbar/
```

应该看到：
```
static/debug_toolbar/
├── css/
│   ├── print.css
│   └── toolbar.css
└── js/
    ├── history.js
    ├── redirect.js
    ├── timer.js
    ├── toolbar.js
    └── utils.js
```

### 2. 测试静态文件访问

```bash
curl -I http://your-domain.com/static/debug_toolbar/css/toolbar.css
```

应该返回 HTTP 200。

### 3. 检查 Debug Toolbar 是否显示

访问任何页面，应该在页面右侧看到 Debug Toolbar 面板。

## 常见问题

### 问题 1: Debug Toolbar 不显示

**可能原因**:
1. DEBUG = False
2. 静态文件未正确部署
3. Middleware 配置顺序错误

**解决方案**:
```python
# 确保 DEBUG = True
DEBUG = True

# 确保 Middleware 顺序正确
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # 在 SessionMiddleware 之后
    # ...
]

# 部署静态文件
./deploy_debug_toolbar_static.sh
python manage.py collectstatic --noinput
```

### 问题 2: 静态文件 404 错误

**可能原因**:
- 静态文件未复制到 `static/` 目录
- WhiteNoise 配置问题

**解决方案**:
```bash
# 重新部署静态文件
./deploy_debug_toolbar_static.sh
python manage.py collectstatic --noinput

# 重启服务器
```

### 问题 3: 生产环境性能问题

**建议**:
- 只在需要调试时开启 DEBUG=True
- 调试完成后立即关闭 DEBUG
- 考虑使用条件性启用：

```python
# 只在特定条件下启用 Debug Toolbar
DEBUG_TOOLBAR_ENABLED = os.getenv('ENABLE_DEBUG_TOOLBAR', 'False') == 'True'

if DEBUG and DEBUG_TOOLBAR_ENABLED:
    def show_toolbar(request):
        return True
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    }
```

## 安全注意事项

⚠️ **重要**: 在生产环境开启 DEBUG=True 存在安全风险！

1. **不要长期开启**: 只在调试问题时临时开启
2. **限制访问**: 使用环境变量控制是否启用
3. **监控日志**: 密切关注访问日志
4. **及时关闭**: 调试完成后立即关闭 DEBUG

推荐的安全生产配置：
```python
# .env 文件
DEBUG=False
ENABLE_DEBUG_TOOLBAR=False

# settings.py
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ENABLE_DEBUG_TOOLBAR = os.getenv('ENABLE_DEBUG_TOOLBAR', 'False') == 'True'

if DEBUG and ENABLE_DEBUG_TOOLBAR:
    # 启用 Debug Toolbar
    pass
```

## 相关文件

- `conf/settings.py` - Django 配置
- `conf/urls.py` - URL 路由配置
- `deploy_debug_toolbar_static.sh` - 静态文件部署脚本
- `Makefile` - 构建命令
- `requirements.txt` - 依赖列表
