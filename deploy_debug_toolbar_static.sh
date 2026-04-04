#!/bin/bash
# Debug Toolbar 静态文件部署脚本
# 用于将 django-debug-toolbar 的静态文件复制到项目的 static 目录

set -e

echo "🚀 正在部署 Debug Toolbar 静态文件..."

# 获取 debug_toolbar 包的路径
DEBUG_TOOLBAR_PATH=$(python -c "import debug_toolbar; import os; print(os.path.dirname(debug_toolbar.__file__))")

if [ ! -d "$DEBUG_TOOLBAR_PATH" ]; then
    echo "❌ 错误：找不到 debug_toolbar 包，请先安装：pip install django-debug-toolbar"
    exit 1
fi

# 检查是否有静态文件目录
if [ ! -d "$DEBUG_TOOLBAR_PATH/static/debug_toolbar" ]; then
    echo "⚠️  警告：debug_toolbar 包中没有找到 static 目录"
    echo "   这可能是因为在生产环境中不需要手动复制静态文件"
    echo "   Django 会通过 AppDirectoriesFinder 自动查找"
    exit 0
fi

# 复制静态文件到项目 static 目录
echo "📦 从 $DEBUG_TOOLBAR_PATH/static/debug_toolbar 复制文件..."
cp -R "$DEBUG_TOOLBAR_PATH/static/debug_toolbar" static/

# 验证文件是否成功复制
if [ -d "static/debug_toolbar" ]; then
    echo "✅ Debug Toolbar 静态文件部署成功！"
    echo ""
    echo "已复制的文件："
    find static/debug_toolbar -type f | head -20
    echo ""
    echo "总计文件数：$(find static/debug_toolbar -type f | wc -l)"
else
    echo "❌ 错误：文件复制失败"
    exit 1
fi
