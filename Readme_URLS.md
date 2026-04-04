# Kapibala.icu URL 路由文档

> 生成时间: 2026-04-04

---

## 根 URL 配置 (`conf/urls.py`)

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/mothership/` | Django Admin | 管理后台 |
| `/accounts/` | django-allauth | 用户认证（登录/注册/密码等） |
| `/markdownx/` | django-markdownx | Markdown 编辑器 API |
| `/__debug__/` | debug-toolbar | 调试工具栏（仅 DEBUG 模式） |

---

## 博客主站 (`blogs/urls.py`)

### 首页 & 发现

| URL | 视图 | 说明 |
|-----|------|------|
| `/` | `discover.discover` | 首页/发现页 |
| `/home/` | `blog.home` | 旧版首页 |
| `/discover/` | `discover.discover` | 发现页 |
| `/discover/feed/` | `discover.feed` | 发现页动态 |
| `/discover/search/` | `discover.search` | 搜索 |
| `/discover/random-post/` | `discover.random_post` | 随机文章 |
| `/discover/random-blog/` | `discover.random_blog` | 随机博客 |

### Staff 管理后台

| URL | 视图 | 说明 |
|-----|------|------|
| `/staff/dashboard/` | `staff.dashboard` | 管理面板 |
| `/staff/actions/` | `staff.actions` | 批量操作 |
| `/staff/playground/` | `staff.playground` | 测试页 |
| `/staff/dashboard/migrate-blog/` | `staff.migrate_blog` | 迁移博客 |
| `/staff/dashboard/import-posts/` | `staff.import_posts` | 导入文章 |
| `/staff/dashboard/check-spam/` | `staff.check_spam` | 检查垃圾 |
| `/staff/review/new/` | `staff.review_bulk` | 审核新提交 |
| `/staff/review/opt-in/` | `staff.review_bulk` | 审核 opt-in |
| `/staff/review/dodgy/` | `staff.review_bulk` | 审核可疑 |
| `/staff/review/flagged/` | `staff.review_bulk` | 审核被标记 |
| `/staff/review/approve/<pk>` | `staff.approve` | 批准 |
| `/staff/review/block/<pk>` | `staff.block` | 屏蔽 |
| `/staff/review/ignore/<pk>` | `staff.ignore` | 忽略 |
| `/staff/review/flag/<pk>` | `staff.flag` | 标记 |
| `/staff/review/delete/<pk>` | `staff.delete` | 删除 |

### 用户仪表盘

| URL | 视图 | 说明 |
|-----|------|------|
| `/signup/` | `signup_flow.signup` | 注册流程 |
| `/dashboard/` | `studio.list` | 博客列表 |
| `/dashboard/upgrade/` | `dashboard.upgrade` | 升级页面 |
| `/dashboard/customise/` | `studio.dashboard_customisation` | 自定义仪表盘 |
| `/accounts/delete/` | `dashboard.delete_user` | 删除账户 |

### 博客管理 (`/<subdomain>/dashboard/`)

| URL | 视图 | 说明 |
|-----|------|------|
| `/<id>/dashboard/` | `studio.studio` | 主页编辑 |
| `/<id>/dashboard/nav/` | `dashboard.nav` | 导航设置 |
| `/<id>/dashboard/styles/` | `dashboard.styles` | 样式编辑 |
| `/<id>/dashboard/settings/` | `dashboard.settings` | 基本设置 |
| `/<id>/dashboard/settings/advanced/` | `studio.advanced_settings` | 高级设置 |
| `/<id>/dashboard/custom-domain/` | `studio.custom_domain_edit` | 自定义域名 |
| `/<id>/dashboard/directives/` | `studio.directive_edit` | 指令配置 |
| `/<id>/dashboard/email-list/` | `emailer.email_list` | 邮件列表 |
| `/<id>/dashboard/media/` | `media.media_center` | 媒体中心 |
| `/<id>/dashboard/media/delete-selected/` | `media.delete_selected_media` | 删除媒体 |
| `/<id>/dashboard/upload-image/` | `media.upload_image` | 上传图片 |
| `/<id>/dashboard/analytics/` | `analytics.analytics` | 统计分析 |
| `/<id>/dashboard/posts/` | `dashboard.posts_edit` | 文章列表 |
| `/<id>/dashboard/pages/` | `dashboard.pages_edit` | 页面列表 |
| `/<id>/dashboard/posts/new/` | `studio.post` | 新建文章 |
| `/<id>/dashboard/posts/<uid>/` | `studio.post` | 编辑文章 |
| `/<id>/dashboard/posts/<uid>/delete/` | `dashboard.post_delete` | 删除文章 |
| `/<id>/dashboard/vditor/new/` | `studio.vditor_post` | Vditor 新建 |
| `/<id>/dashboard/vditor/<uid>/` | `studio.vditor_post` | Vditor 编辑 |
| `/<id>/dashboard/preview/` | `studio.preview` | 预览 |
| `/<id>/dashboard/post-template/` | `studio.post_template` | 文章模板 |
| `/<id>/dashboard/opt-in-review/` | `dashboard.opt_in_review` | Opt-in 审核 |
| `/<id>/delete/` | `dashboard.blog_delete` | 删除博客 |
| `/<id>/remove-domain/` | `studio.remove_domain` | 移除域名 |

### MarkdownX API

| URL | 视图 | 说明 |
|-----|------|------|
| `/markdownx/upload/` | `markdownx.upload` | 图片上传 |
| `/markdownx/markdownify/` | `markdownx.markdownify` | Markdown 转 HTML |

### 公共功能

| URL | 视图 | 说明 |
|-----|------|------|
| `/ping/` | `blog.ping` | Caddy 验证 |
| `/sitemap.xml` | `blog.sitemap` | SEO sitemap |
| `/robots.txt` | `blog.robots` | SEO robots |
| `/upvote/` | `blog.upvote` | 点赞 |
| `/upvote-info/<uid>/` | `blog.get_upvote_info` | 点赞信息 |
| `/hit/` | `analytics.hit` | 页面访问统计 |
| `/subscribe/` | `emailer.subscribe` | 订阅 |
| `/email-subscribe/` | `emailer.email_subscribe` | 邮件订阅 |
| `/lemon-webhook/` | `subscriptions.lemon_webhook` | LemonSqueezy webhook |
| `/public-analytics/` | `blog.public_analytics` | 公开统计 |

### 订阅源 (Feeds)

| URL | 别名 |
|-----|------|
| `/feed/` | /atom/, /rss/ |
| `/feed/atom/` | - |
| `/feed/rss/` | - |
| `/feed.xml` | /atom.xml, /rss.xml, /index.xml |

### 静态资源 & 文章

| URL | 说明 |
|-----|------|
| `/favicon.ico` | 网站图标 |
| `/apple-touch-icon.png` | Apple 图标 |
| `/favicons/*` | Favicon 集合 |
| `/<path:slug>/` | 博客文章（catch-all） |

---

## 架构特点

### 1. 子域名路由

`main_site_only` 中间件根据 `MAIN_SITE_HOSTS` 环境变量判断请求是主站还是博客子域名。

```python
main_site_hosts = os.getenv('MAIN_SITE_HOSTS', '').split(',')
# 如果 host 不在列表中，路由到博客子域名
```

### 2. 动态博客路径

`<id>/dashboard/*` 路径中的 `<id>` 是博客子域名：

```
/joevan/dashboard/          -> 博客子域名为 joevan
/joevan/dashboard/posts/    -> 编辑 joevan 的文章
```

### 3. MarkdownX 集成

- **上传**: `POST /markdownx/upload/` - 上传图片到媒体库
- **转换**: `POST /markdownx/markdownify/` - 将 Markdown 转为 HTML

### 4. Debug Toolbar

仅在 `DEBUG=True` 时启用，提供性能分析、SQL 查询查看等调试功能。

---

## 视图模块映射

| 模块 | 文件 | 功能 |
|------|------|------|
| `blog` | `blogs/views/blog.py` | 博客文章、首页、SEO |
| `studio` | `blogs/views/studio.py` | 文章编辑、仪表盘 |
| `dashboard` | `blogs/views/dashboard.py` | 用户设置、删除 |
| `staff` | `blogs/views/staff.py` | 管理后台 |
| `staff_api` | `blogs/views/staff_api.py` | 管理员 API |
| `discover` | `blogs/views/discover.py` | 发现页、搜索 |
| `feed` | `blogs/views/feed.py` | RSS/Atom 订阅源 |
| `analytics` | `blogs/views/analytics.py` | 访问统计 |
| `emailer` | `blogs/views/emailer.py` | 邮件订阅 |
| `media` | `blogs/views/media.py` | 媒体中心 |
| `subscriptions` | `blogs/subscriptions.py` | 支付订阅 |
| `signup_flow` | `blogs/views/signup_flow.py` | 注册流程 |

