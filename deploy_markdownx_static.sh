#!/bin/bash
# MarkdownX 静态文件部署脚本
# 用于将 django-markdownx 的静态文件复制到项目的 static 目录

set -e

echo "🚀 正在部署 MarkdownX 静态文件..."

# 获取 markdownx 包的路径
MARKDOWNX_PATH=$(python -c "import markdownx; import os; print(os.path.dirname(markdownx.__file__))")

if [ ! -d "$MARKDOWNX_PATH" ]; then
    echo "❌ 错误：找不到 markdownx 包，请先安装：pip install django-markdownx"
    exit 1
fi

# 复制静态文件到项目 static 目录
echo "📦 从 $MARKDOWNX_PATH/static/markdownx 复制文件..."
cp -R "$MARKDOWNX_PATH/static/markdownx" static/

# 验证文件是否成功复制
if [ -f "static/markdownx/js/markdownx.js" ] && [ -f "static/markdownx/admin/css/markdownx.css" ]; then
    echo "✅ MarkdownX 静态文件部署成功！"
    echo ""
    echo "已复制的文件："
    find static/markdownx -type f | sort
else
    echo "❌ 错误：文件复制失败"
    exit 1
fi
