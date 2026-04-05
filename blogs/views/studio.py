from django.contrib.auth.decorators import login_required
from django.db import DataError, models
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.core.cache import cache

from zoneinfo import ZoneInfo
from datetime import datetime
import json
import random
import string

from blogs.backup import backup_in_thread
from blogs.forms import AdvancedSettingsForm, BlogForm, DashboardCustomisationForm, PostTemplateForm
from blogs.helpers import check_connection, is_protected, salt_and_hash
from blogs.models import Blog, Post, Upvote, Todo, Bookmark
from blogs.subscriptions import get_subscriptions, normalize_plan_type


@login_required
def blog_list(request):
    """博客列表页面"""
    blogs = Blog.objects.filter(user=request.user).order_by("created_date")

    if request.method == "POST":
        form = BlogForm(request.POST)
        if form.is_valid():
            if blogs.count() >= request.user.settings.max_blogs:
                form.add_error('title', 'You have reached the maximum number of blogs.')
            else:
                subdomain = slugify(form.cleaned_data['subdomain'])

                if not is_protected(subdomain) and not Blog.objects.filter(subdomain=subdomain).exists():
                    blog_info = form.save(commit=False)
                    blog_info.user = request.user
                    blog_info.save()
                    return redirect('dashboard', id=blog_info.subdomain)
                else:
                    form.add_error('subdomain', 'This subdomain is already in use or protected.')
    else:
        form = BlogForm()

    subscription_cancelled = None
    subscription_link = None
    variant = None
    upgrade_subscription_link = None

    if request.user.settings.order_id and request.user.settings.plan_type != 'lifetime':
        try:
            subscription = get_subscriptions(request.user.settings.order_id)
            if subscription and subscription['data']:
                subscription_cancelled = subscription['data'][0]['attributes']['cancelled']
                subscription_link = subscription['data'][0]['attributes']['urls']['customer_portal']
                upgrade_subscription_link = subscription['data'][0]['attributes']['urls']['customer_portal_update_subscription']
                variant = subscription['data'][0]['attributes']['variant_name']
                status = subscription['data'][0]['attributes']['status']
                plan_type = normalize_plan_type(variant)
                if plan_type and request.user.settings.plan_type != plan_type:
                    request.user.settings.plan_type = plan_type
                    request.user.settings.save()

                if status in ('expired', 'paused') and request.user.settings.upgraded:
                    request.user.settings.upgraded = False
                    request.user.settings.upgraded_date = None
                    request.user.settings.order_id = None
                    request.user.settings.plan_type = None
                    request.user.settings.save()
                elif status == 'active' and not request.user.settings.upgraded:
                    request.user.settings.upgraded = True
                    request.user.settings.save()
            else:
                request.user.settings.plan_type = 'lifetime'
                request.user.settings.save()
        except Exception as e:
            print('No sub found ', e)

    return render(request, 'studio/blog_list.html', {
        'blogs': blogs,
        'form': form,
        'subscription_cancelled': subscription_cancelled,
        'subscription_link': subscription_link,
        'upgrade_subscription_link': upgrade_subscription_link,
        'variant': variant
    })


@login_required
def studio(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    error_messages = []
    header_content = request.POST.get('header_content', '')
    body_content = request.POST.get('body_content', '')

    if request.method == "POST" and header_content:
        try:
            error_messages.extend(parse_raw_homepage(blog, header_content, body_content))
        except IndexError:
            error_messages.append("One of the header options is invalid")
        except ValueError as error:
            error_messages.append(error)
        except DataError as error:
            error_messages.append(error)

    return render(request, 'studio/studio.html', {
        'blog': blog,
        'error_messages': error_messages,
        'header_content': header_content,
    })


def parse_raw_homepage(blog, header_content, body_content):
    if len(body_content) > 100000:
        return ["Your content is too long. This is a safety feature to prevent abuse. If you're sure you need more, please contact support."]
    
    raw_header = [item for item in header_content.split('\r\n') if item]
    
    # Clear out data
    blog.favicon = ''
    blog.meta_description = ''
    blog.meta_image = ''

    error_messages = []
    # Parse and populate header data
    for item in raw_header:
        item = item.split(':', 1)
        name = item[0].strip()
        value = item[1].strip()
        if str(value).lower() == 'true':
            value = True
        if str(value).lower() == 'false':
            value = False

        if name == 'title':
            blog.title = value
        elif name == 'favicon':
            if len(value) < 100:
                blog.favicon = value
            else:
                error_messages.append("Favicon is too long. Use an emoji.")
        elif name == 'meta_description':
            blog.meta_description = value
        elif name == 'meta_image':
            blog.meta_image = value
        else:
            error_messages.append(f"{name} is an unrecognised header option")

    if not blog.title:
        blog.title = "My blog"
    if not blog.subdomain:
        blog.slug = slugify(blog.user.username)

    blog.content = body_content
    blog.last_modified = timezone.now()
    blog.save()
    return error_messages


@login_required
def post(request, id, uid=None):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    is_page = request.GET.get('is_page', '')
    tags = []
    post = None

    if uid:
        post = Post.objects.filter(blog=blog, uid=uid).first()

    error_messages = []
    header_content = request.POST.get("header_content", "")
    body_content = request.POST.get("body_content", "")
    preview = request.POST.get("preview", False) == "true"

    if request.method == "POST" and header_content:
        if blog.posts.count() >= 5000:
            error_messages.append("You have reached the maximum number of posts. This is a safety feature to prevent abuse. If you're sure you need more, please contact support.")
            return render(request, 'studio/post_edit.html', {
                'blog': blog,
                'post': post,
                'error_messages': error_messages,
            })
        if len(body_content) > 1000000:
            error_messages.append("Your content is too long. This is a safety feature to prevent abuse. If you're sure you need more, please contact support.")
            return render(request, 'studio/post_edit.html', {
                'blog': blog,
                'post': post,
                'error_messages': error_messages,
            })
        
        raw_header = [item for item in header_content.split('\r\n') if item]
        is_new = False

        if not post:
            post = Post(blog=blog)
            is_new = True

        try:
            # Clear out data
            slug = ''
            post.alias = ''
            post.class_name = ''
            post.canonical_url = ''
            post.meta_description = ''
            post.meta_image = ''
            post.is_page = False
            post.make_discoverable = True
            post.lang = ''
            post.all_tags = '[]'

            # Parse and populate header data
            for item in raw_header:
                item = item.split(':', 1)
                name = item[0].strip()

                # Prevent index error
                if len(item) == 2:
                    value = item[1].strip()
                else:
                    value = ''

                if str(value).lower() == 'true':
                    value = True
                if str(value).lower() == 'false':
                    value = False

                if name == 'title':
                    post.title = value
                elif name == 'link':
                    slug = value
                elif name == 'alias':
                    if value[0] == '/':
                        value = value[1:]
                    if value[-1] == '/':
                        value = value[:-1]
                    post.alias = value
                elif name == 'published_date':
                    if not value:
                        post.published_date = timezone.now()
                    else:
                        value = str(value).replace('/', '-')
                        try:
                            # Convert given date/time from local timezone to UTC
                            naive_datetime = datetime.fromisoformat(value)
                            user_timezone = request.COOKIES.get('timezone', 'UTC')

                            try:
                                user_tz = ZoneInfo(user_timezone)
                            except Exception as e:
                                user_tz = ZoneInfo('UTC')

                            aware_datetime = timezone.make_aware(naive_datetime, user_tz)
                            utc_datetime = aware_datetime.astimezone(ZoneInfo('UTC'))
                            post.published_date = utc_datetime
                        except Exception as e:
                            error_messages.append('Bad date format. Use YYYY-MM-DD HH:MM')
                elif name == 'tags':
                    tags = []
                    for tag in value.split(','):
                        stripped_tag = tag.strip()
                        if stripped_tag and stripped_tag not in tags:
                            tags.append(stripped_tag)
                    post.all_tags = json.dumps(tags)
                elif name == 'make_discoverable':
                    if type(value) is bool:
                        post.make_discoverable = value
                    else:
                        error_messages.append('make_discoverable needs to be "true" or "false"')
                elif name == 'is_page':
                    if type(value) is bool:
                        post.is_page = value
                    else:
                        error_messages.append('is_page needs to be "true" or "false"')
                elif name == 'class_name':
                    post.class_name = slugify(value)
                elif name == 'canonical_url':
                    post.canonical_url = value
                elif name == 'lang':
                    post.lang = value
                elif name == 'meta_description':
                    post.meta_description = value
                elif name == 'meta_image':
                    post.meta_image = value
                else:
                    error_messages.append(f"{name} is an unrecognised header option")

            if not post.title:
                post.title = "New post"

            post.slug = unique_slug(blog, post, slug)

            if not post.published_date:
                post.published_date = timezone.now()

            post.content = body_content

            post.publish = request.POST.get("publish", False) == "true"
            post.last_modified = timezone.now()

            if preview:
                return post
            else:
                post.save()
                
                # Backup blog
                backup_in_thread(blog)
                
                if is_new:
                    # Self-upvote
                    upvote = Upvote(post=post, hash_id=salt_and_hash(request, 'year'))
                    upvote.save()

                    # Redirect to the new post detail view
                    return redirect('post_edit', id=blog.subdomain, uid=post.uid)

        except Exception as error:
            error_messages.append(f"Header attribute error - your post has not been saved. Error: {str(error)}")
            post.content = body_content

    template_header = ""
    template_body = ""
    if blog.post_template:
        template_parts = blog.post_template.split("___", 1)
        if len(template_parts) == 2:
            template_header, template_body = template_parts

    return render(request, 'studio/post_edit.html', {
        'blog': blog,
        'post': post,
        'error_messages': error_messages,
        'template_header': template_header,
        'template_body': template_body,
        'is_page': is_page
    })


@login_required
def vditor_post(request, id, uid=None):
    """Vditor-based markdown editor view - uses the same backend logic as post()"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    is_page = request.GET.get('is_page', '')
    tags = []
    post = None

    if uid:
        post = Post.objects.filter(blog=blog, uid=uid).first()

    error_messages = []
    header_content = request.POST.get("header_content", "")
    body_content = request.POST.get("body_content", "")
    preview = request.POST.get("preview", False) == "true"

    template_header = ""
    template_body = ""
    if blog.post_template:
        template_parts = blog.post_template.split("___", 1)
        if len(template_parts) == 2:
            template_header, template_body = template_parts

    if request.method == "POST" and header_content:
        if blog.posts.count() >= 5000:
            error_messages.append("You have reached the maximum number of posts. This is a safety feature to prevent abuse. If you're sure you need more, please contact support.")
            return render(request, 'studio/vditor_post_edit.html', {
                'blog': blog,
                'post': post,
                'error_messages': error_messages,
                'template_header': template_header,
                'template_body': template_body,
                'is_page': is_page,
            })
        if len(body_content) > 1000000:
            error_messages.append("Your content is too long. This is a safety feature to prevent abuse. If you're sure you need more, please contact support.")
            return render(request, 'studio/vditor_post_edit.html', {
                'blog': blog,
                'post': post,
                'error_messages': error_messages,
                'template_header': template_header,
                'template_body': template_body,
                'is_page': is_page,
            })
        
        raw_header = [item for item in header_content.split('\r\n') if item]
        is_new = False

        if not post:
            post = Post(blog=blog)
            is_new = True

        try:
            # Clear out data
            slug = ''
            post.alias = ''
            post.class_name = ''
            post.canonical_url = ''
            post.meta_description = ''
            post.meta_image = ''
            post.is_page = False
            post.make_discoverable = True
            post.lang = ''
            post.all_tags = '[]'

            # Parse and populate header data
            for item in raw_header:
                item = item.split(':', 1)
                name = item[0].strip()

                # Prevent index error
                if len(item) == 2:
                    value = item[1].strip()
                else:
                    value = ''

                if str(value).lower() == 'true':
                    value = True
                if str(value).lower() == 'false':
                    value = False

                if name == 'title':
                    post.title = value
                elif name == 'link':
                    slug = value
                elif name == 'alias':
                    if value[0] == '/':
                        value = value[1:]
                    if value[-1] == '/':
                        value = value[:-1]
                    post.alias = value
                elif name == 'published_date':
                    if not value:
                        post.published_date = timezone.now()
                    else:
                        value = str(value).replace('/', '-')
                        try:
                            # Convert given date/time from local timezone to UTC
                            naive_datetime = datetime.fromisoformat(value)
                            user_timezone = request.COOKIES.get('timezone', 'UTC')

                            try:
                                user_tz = ZoneInfo(user_timezone)
                            except Exception as e:
                                user_tz = ZoneInfo('UTC')

                            aware_datetime = timezone.make_aware(naive_datetime, user_tz)
                            utc_datetime = aware_datetime.astimezone(ZoneInfo('UTC'))
                            post.published_date = utc_datetime
                        except Exception as e:
                            error_messages.append('Bad date format. Use YYYY-MM-DD HH:MM')
                elif name == 'tags':
                    tags = []
                    for tag in value.split(','):
                        stripped_tag = tag.strip()
                        if stripped_tag and stripped_tag not in tags:
                            tags.append(stripped_tag)
                    post.all_tags = json.dumps(tags)
                elif name == 'make_discoverable':
                    if type(value) is bool:
                        post.make_discoverable = value
                    else:
                        error_messages.append('make_discoverable needs to be "true" or "false"')
                elif name == 'is_page':
                    if type(value) is bool:
                        post.is_page = value
                    else:
                        error_messages.append('is_page needs to be "true" or "false"')
                elif name == 'class_name':
                    post.class_name = slugify(value)
                elif name == 'canonical_url':
                    post.canonical_url = value
                elif name == 'lang':
                    post.lang = value
                elif name == 'meta_description':
                    post.meta_description = value
                elif name == 'meta_image':
                    post.meta_image = value
                else:
                    error_messages.append(f"{name} is an unrecognised header option")

            if not post.title:
                post.title = "New post"

            post.slug = unique_slug(blog, post, slug)

            if not post.published_date:
                post.published_date = timezone.now()

            post.content = body_content

            post.publish = request.POST.get("publish", False) == "true"
            post.last_modified = timezone.now()

            if preview:
                return post
            else:
                post.save()
                
                # Backup blog
                backup_in_thread(blog)
                
                if is_new:
                    # Self-upvote
                    upvote = Upvote(post=post, hash_id=salt_and_hash(request, 'year'))
                    upvote.save()

                    # Redirect to the new post detail view (using vditor editor)
                    return redirect('vditor_post_edit', id=blog.subdomain, uid=post.uid)

        except Exception as error:
            error_messages.append(f"Header attribute error - your post has not been saved. Error: {str(error)}")
            post.content = body_content

    return render(request, 'studio/vditor_post_edit.html', {
        'blog': blog,
        'post': post,
        'error_messages': error_messages,
        'template_header': template_header,
        'template_body': template_body,
        'is_page': is_page
    })


def unique_slug(blog, post, new_slug):
    # Clean the new_slug to be alphanumeric lowercase with only '/', '_' and '-' allowed
    cleaned_slug = ''.join(c for c in new_slug.lower() if c.isalnum() or c == '/' or c == '-' or c == '_')

    # Remove trailing and leading slashes
    if len(cleaned_slug) > 0 and cleaned_slug[-1] == '/':
        cleaned_slug = cleaned_slug[:-1]
    if len(cleaned_slug) > 0 and cleaned_slug[0] == '/':
        cleaned_slug = cleaned_slug[1:]

    # If the cleaned slug is empty, use the title
    if cleaned_slug == '':
        slug = slugify(post.title) or slugify(str(random.randint(0,9999)))
    else:
        slug = cleaned_slug
    
    new_stack = "-new"

    while Post.objects.filter(blog=blog, slug=slug).exclude(pk=post.pk).exists():
        slug = f"{slug}{new_stack}"
        new_stack += "-new"

    return slug


@csrf_exempt
@login_required
def preview(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    post = Post(blog=blog)

    header_content = request.POST.get("header_content", "")
    body_content = request.POST.get("body_content", "")
    try:
        if header_content:
            raw_header = [item for item in header_content.split('\r\n') if item]

            if post is None:
                post = Post(blog=blog)

            # Clear out data
            # post.slug = ''
            post.alias = ''
            post.class_name = ''
            post.canonical_url = ''
            post.meta_description = ''
            post.meta_image = ''
            post.is_page = False
            post.make_discoverable = True
            post.lang = ''

            # Parse and populate header data
            for item in raw_header:
                item = item.split(':', 1)
                name = item[0].strip()
                value = item[1].strip()
                if str(value).lower() == 'true':
                    value = True
                if str(value).lower() == 'false':
                    value = False

                if name == 'title':
                    post.title = value
                elif name == 'alias':
                    post.alias = value
                elif name == 'published_date':
                    # Check if previously posted 'now'
                    value = value.replace('/', '-')
                    if not str(post.published_date).startswith(value):
                        post.published_date = timezone.datetime.fromisoformat(value)
                elif name == 'make_discoverable':
                    post.make_discoverable = value
                elif name == 'is_page':
                    post.is_page = value
                elif name == 'class_name':
                    post.class_name = slugify(value)
                elif name == 'canonical_url':
                    post.canonical_url = value
                elif name == 'lang':
                    post.lang = value
                elif name == 'meta_description':
                    post.meta_description = value
                elif name == 'meta_image':
                    post.meta_image = value

            if not post.title:
                post.title = "New post"
            if not post.slug:
                post.slug = slugify(post.title)
                if not post.slug or post.slug == "":
                    post.slug = ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(10))
            if not post.published_date:
                post.published_date = timezone.now()

            post.content = body_content

    except ValidationError:
        return HttpResponseBadRequest("One of the header options is invalid")
    except IndexError:
        return HttpResponseBadRequest("One of the header options is invalid")
    except ValueError as error:
        return HttpResponseBadRequest(error)
    except DataError as error:
        return HttpResponseBadRequest(error)

    full_path = f'{blog.useful_domain}/{post.slug}/'
    canonical_url = full_path
    if post.canonical_url and post.canonical_url.startswith('https://'):
        canonical_url = post.canonical_url
    return render(
        request,
        'post.html',
        {
            'blog': blog,
            'content': post.content,
            'post': post,
            'full_path': full_path,
            'canonical_url': canonical_url,
            'meta_image': post.meta_image or blog.meta_image,
            'preview': True,
        }
    )


@login_required
def post_template(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    if request.method == "POST":
        form = PostTemplateForm(request.POST, instance=blog)
        if form.is_valid():
            blog_info = form.save(commit=False)
            blog_info.save()
    else:
        form = PostTemplateForm(instance=blog)

    return render(request, 'studio/post_template_edit.html', {
        'blog': blog,
        'form': form})


@login_required
def custom_domain_edit(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    if not blog.user.settings.upgraded:
        return redirect('upgrade')

    error_messages = []

    if request.method == "POST":
        custom_domain = request.POST.get("custom-domain", "").lower().strip().replace('https://', '').replace('http://', '')

        if Blog.objects.filter(domain__iexact=custom_domain).exclude(pk=blog.pk).count() == 0:
            try:
                validator = URLValidator()
                validator('http://' + custom_domain)
                blog.domain = custom_domain
                blog.save()

                # Invalidate domain_map cache
                cache.delete('domain_map')
            except ValidationError:
                error_messages.append(f'{custom_domain} is an invalid domain')
                print("error")
        elif not custom_domain:
            blog.domain = ''
            blog.save()

            # Invalidate domain_map cache
            cache.delete('domain_map')
        else:
            error_messages.append(f"{custom_domain} is already registered with another blog")

    # If records not set correctly
    if blog.domain and not check_connection(blog):
        error_messages.append(f"The DNS records for { blog.domain } have not been set.")

    return render(request, 'studio/custom_domain_edit.html', {
        'blog': blog,
        'error_messages': error_messages
    })


@login_required
def remove_domain(request, id):
    if request.method != 'POST':
        return redirect('dashboard', id=id)
    blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    blog.domain = ""
    blog.save()
    # Invalidate domain_map cache
    cache.delete('domain_map')
    blog.user.settings.orphaned_domain_warning_email_sent = None
    blog.user.settings.save()
    return redirect('dashboard', id=blog.subdomain)


@login_required
def directive_edit(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    if not blog.user.settings.upgraded:
        return redirect('upgrade')

    header = request.POST.get("header", "")
    footer = request.POST.get("footer", "")

    if request.method == "POST":
        blog.header_directive = header
        blog.footer_directive = footer
        blog.save()

    return render(request, 'studio/directive_edit.html', {
        'blog': blog
    })


@login_required
def advanced_settings(request, id):
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)

    if request.method == "POST":
        form = AdvancedSettingsForm(request.POST, instance=blog)
        if form.is_valid():
            blog_info = form.save(commit=False)
            blog_info.save()
    else:
        form = AdvancedSettingsForm(instance=blog)

    return render(request, 'dashboard/advanced_settings.html', {
        'blog': blog,
        'form': form
    })


@login_required
def dashboard_customisation(request):
    if request.method == "POST":
        form = DashboardCustomisationForm(request.POST, instance=request.user.settings)
        if form.is_valid():
            user_settings = form.save(commit=False)
            user_settings.save()
    else:
        form = DashboardCustomisationForm(instance=request.user.settings)

    return render(request, 'dashboard/dashboard_customisation.html', {'form': form})


@login_required
def todo_list(request, id):
    """待办事项列表页面"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    
    # 获取过滤参数
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    view_mode = request.GET.get('view', 'active')  # 'active' or 'trash'
    
    # 分页参数
    items_per_page = 20
    page = int(request.GET.get('page', 1))
    
    # 基础查询集
    todos = Todo.objects.filter(blog=blog)
    
    # 检查并重置周期性任务的状态
    for todo in todos:
        if todo.is_recurring:
            todo.check_and_reset_cycle()
    
    # 如果是回收站视图，只显示已取消的任务
    if view_mode == 'trash':
        todos = todos.filter(status='cancelled')
        status_filter = 'cancelled'
    else:
        # 应用过滤器
        if status_filter != 'all':
            todos = todos.filter(status=status_filter)
        elif status_filter == 'completed':
            # 如果明确选择查看已完成，显示所有已完成的任务
            todos = todos.filter(status='completed')
        else:
            # 默认视图：显示待处理、进行中的任务
            # 以及最近完成的周期性任务（等待新周期）
            from django.utils import timezone as tz
            recent_completed_cutoff = tz.now() - tz.timedelta(hours=24)
            
            todos = todos.filter(
                models.Q(status__in=['pending', 'in_progress']) |
                models.Q(
                    status='completed',
                    is_recurring=True,
                    completed_date__gte=recent_completed_cutoff
                )
            ).exclude(status='cancelled')
    
    if priority_filter != 'all':
        todos = todos.filter(priority=priority_filter)
    
    # 按优先级和截止日期排序
    priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
    from datetime import timezone as dt_timezone
    todos = sorted(todos, key=lambda t: (priority_order.get(t.priority, 2), t.due_date or timezone.datetime.max.replace(tzinfo=dt_timezone.utc)))
    
    # 分页
    total_items = len(todos)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_todos = todos[start_idx:end_idx]
    
    # 生成分页范围
    max_visible = 7
    if total_pages <= max_visible:
        paginator_range = list(range(1, total_pages + 1))
    else:
        paginator_range = []
        if page <= 4:
            paginator_range = list(range(1, 6))
            paginator_range.append('...')
            paginator_range.append(total_pages)
        elif page >= total_pages - 3:
            paginator_range = [1]
            paginator_range.append('...')
            paginator_range.extend(range(total_pages - 4, total_pages + 1))
        else:
            paginator_range = [1]
            paginator_range.append('...')
            paginator_range.extend(range(page - 1, page + 2))
            paginator_range.append('...')
            paginator_range.append(total_pages)
    
    # 统计信息
    stats = {
        'total': Todo.objects.filter(blog=blog).exclude(status__in=['completed', 'cancelled']).count(),
        'pending': Todo.objects.filter(blog=blog, status='pending').count(),
        'in_progress': Todo.objects.filter(blog=blog, status='in_progress').count(),
        'completed': Todo.objects.filter(blog=blog, status='completed').count(),
        'cancelled': Todo.objects.filter(blog=blog, status='cancelled').count(),
        'overdue': Todo.objects.filter(
            blog=blog,
            status__in=['pending', 'in_progress'],
            due_date__lt=timezone.now()
        ).count() if any(t for t in todos if t.due_date and t.due_date < timezone.now() and t.status in ['pending', 'in_progress']) else 0,
    }
    
    return render(request, 'studio/todo_list.html', {
        'blog': blog,
        'todos': paginated_todos,
        'stats': stats,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'view_mode': view_mode,
        'page': page,
        'total_pages': total_pages,
        'total_items': total_items,
        'items_per_page': items_per_page,
        'paginator_range': paginator_range,
    })


@login_required
def todo_create(request, id):
    """创建待办事项"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        due_date_str = request.POST.get('due_date', '')
        is_recurring = request.POST.get('is_recurring') == 'on'
        recurring_type = request.POST.get('recurring_type', '') if is_recurring else None
        recurring_interval = int(request.POST.get('recurring_interval', 1)) if is_recurring else 1
        tags = request.POST.get('tags', '').strip()
        
        if not title:
            return redirect('todo_list', id=blog.subdomain)
        
        # 处理截止日期 - 如果没有选择时间，默认使用当前时间 + 7天
        due_date = None
        if due_date_str:
            try:
                from datetime import datetime as dt
                naive_datetime = dt.fromisoformat(due_date_str)
                user_timezone = request.COOKIES.get('timezone', 'UTC')
                from zoneinfo import ZoneInfo
                try:
                    user_tz = ZoneInfo(user_timezone)
                except:
                    user_tz = ZoneInfo('UTC')
                aware_datetime = timezone.make_aware(naive_datetime, user_tz)
                due_date = aware_datetime
            except Exception as e:
                print(f"Error parsing due_date: {e}")
                # 如果解析失败，使用默认值
                due_date = timezone.now() + timezone.timedelta(days=7)
        else:
            # 没有选择时间，默认设置为当前时间 + 7天
            due_date = timezone.now() + timezone.timedelta(days=7)
        
        # 处理标签
        import json
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        
        # 创建待办事项
        todo = Todo.objects.create(
            blog=blog,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            is_recurring=is_recurring,
            recurring_type=recurring_type if is_recurring else None,
            recurring_interval=recurring_interval if is_recurring else 1,
            tags=json.dumps(tag_list),
        )
        
        return redirect('todo_list', id=blog.subdomain)
    
    return redirect('todo_list', id=blog.subdomain)


@login_required
def todo_update(request, id, pk):
    """更新待办事项状态"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        # 处理批量操作
        if action in ['bulk_restore', 'bulk_delete', 'bulk_permanent_delete']:
            # selected_todos 是逗号分隔的字符串，如 "1,2,3"
            selected_ids_str = request.POST.get('selected_todos', '')
            if selected_ids_str:
                selected_ids = [int(pk.strip()) for pk in selected_ids_str.split(',') if pk.strip().isdigit()]
                todos = Todo.objects.filter(pk__in=selected_ids, blog=blog)
                count = todos.count()
                
                if action == 'bulk_restore':
                    for todo in todos:
                        todo.status = 'pending'
                        todo.completed_date = None
                        todo.save()
                    print(f"✅ Restored {count} todos from trash")
                elif action == 'bulk_delete':
                    for todo in todos:
                        todo.status = 'cancelled'
                        todo.save()
                    print(f"🗑️ Moved {count} todos to trash")
                elif action == 'bulk_permanent_delete':
                    todos.delete()
                    print(f"⚠️ Permanently deleted {count} todos")
            
            return redirect(f"{reverse('todo_list', args=[blog.subdomain])}?view=trash")
        
        # 单个操作
        todo = get_object_or_404(Todo, pk=pk, blog=blog)
        
        if action == 'complete':
            todo.complete()
        elif action == 'start':
            todo.status = 'in_progress'
            todo.save()
        elif action == 'cancel':
            todo.status = 'cancelled'
            todo.save()
        elif action == 'restore':
            # 从回收站恢复
            todo.status = 'pending'
            todo.completed_date = None
            todo.save()
        elif action == 'reopen':
            todo.status = 'pending'
            todo.completed_date = None
            todo.save()
        elif action == 'delete':
            todo.delete()
            return redirect('todo_list', id=blog.subdomain)
        elif action == 'empty_trash':
            # 清空回收站（删除所有已取消的任务）
            Todo.objects.filter(blog=blog, status='cancelled').delete()
            return redirect('todo_list', id=blog.subdomain + '?view=trash')
        elif action == 'update':
            # 更新详细信息
            todo.title = request.POST.get('title', todo.title)
            todo.description = request.POST.get('description', todo.description)
            todo.priority = request.POST.get('priority', todo.priority)
            
            due_date_str = request.POST.get('due_date', '')
            if due_date_str:
                try:
                    from datetime import datetime as dt
                    naive_datetime = dt.fromisoformat(due_date_str)
                    user_timezone = request.COOKIES.get('timezone', 'UTC')
                    from zoneinfo import ZoneInfo
                    try:
                        user_tz = ZoneInfo(user_timezone)
                    except:
                        user_tz = ZoneInfo('UTC')
                    aware_datetime = timezone.make_aware(naive_datetime, user_tz)
                    todo.due_date = aware_datetime
                except Exception as e:
                    print(f"Error parsing due_date in update: {e}")
                    pass
            else:
                todo.due_date = None
            
            # 更新标签
            tags_str = request.POST.get('tags', '')
            import json
            tag_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            todo.tags = json.dumps(tag_list)
            
            # 更新周期性任务属性
            is_recurring = request.POST.get('is_recurring') == 'on'
            todo.is_recurring = is_recurring
            
            if is_recurring:
                recurring_type = request.POST.get('recurring_type', '')
                recurring_interval_str = request.POST.get('recurring_interval', '1')
                
                if recurring_type:
                    todo.recurring_type = recurring_type
                
                try:
                    recurring_interval = int(recurring_interval_str)
                    if recurring_interval >= 1:
                        todo.recurring_interval = recurring_interval
                except:
                    pass
            else:
                # 如果取消周期性，清空相关字段
                todo.recurring_type = None
                todo.recurring_interval = 1
                todo.next_occurrence = None
            
            todo.save()
            print(f"✅ Updated todo '{todo.title}' (Recurring: {todo.is_recurring}, Type: {todo.recurring_type})")
        
        return redirect('todo_list', id=blog.subdomain)
    
    return redirect('todo_list', id=blog.subdomain)


@login_required
def bookmark_list(request, id):
    """书签列表页面"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    
    # 获取过滤参数
    visibility_filter = request.GET.get('visibility', 'all')
    
    # 分页参数
    items_per_page = 30
    page = int(request.GET.get('page', 1))
    
    # 基础查询集
    bookmarks = Bookmark.objects.filter(blog=blog)
    
    # 应用过滤器
    if visibility_filter == 'public':
        bookmarks = bookmarks.filter(is_public=True)
    elif visibility_filter == 'private':
        bookmarks = bookmarks.filter(is_public=False)
    
    # 排序
    bookmarks = bookmarks.order_by('-order', '-created_date')
    
    # 分页
    total_items = bookmarks.count()
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_bookmarks = bookmarks[start_idx:end_idx]
    
    # 生成分页范围
    max_visible = 7
    if total_pages <= max_visible:
        paginator_range = list(range(1, total_pages + 1))
    else:
        paginator_range = []
        if page <= 4:
            paginator_range = list(range(1, 6))
            paginator_range.append('...')
            paginator_range.append(total_pages)
        elif page >= total_pages - 3:
            paginator_range = [1]
            paginator_range.append('...')
            paginator_range.extend(range(total_pages - 4, total_pages + 1))
        else:
            paginator_range = [1]
            paginator_range.append('...')
            paginator_range.extend(range(page - 1, page + 2))
            paginator_range.append('...')
            paginator_range.append(total_pages)
    
    # 统计信息
    stats = {
        'total': Bookmark.objects.filter(blog=blog).count(),
        'public': Bookmark.objects.filter(blog=blog, is_public=True).count(),
        'private': Bookmark.objects.filter(blog=blog, is_public=False).count(),
    }
    
    return render(request, 'studio/bookmark_list.html', {
        'blog': blog,
        'bookmarks': paginated_bookmarks,
        'stats': stats,
        'visibility_filter': visibility_filter,
        'page': page,
        'total_pages': total_pages,
        'total_items': total_items,
        'items_per_page': items_per_page,
        'paginator_range': paginator_range,
    })


@login_required
def bookmark_create(request, id):
    """创建书签"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        url = request.POST.get('url', '').strip()
        description = request.POST.get('description', '').strip()
        is_public = request.POST.get('is_public') == 'on'
        tags = request.POST.get('tags', '').strip()
        
        if not title or not url:
            return redirect('bookmark_list', id=blog.subdomain)
        
        # 验证URL格式
        try:
            validator = URLValidator()
            validator(url)
        except ValidationError:
            return redirect('bookmark_list', id=blog.subdomain)
        
        # 处理标签
        import json
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        
        # 获取最大排序值
        max_order = Bookmark.objects.filter(blog=blog).aggregate(models.Max('order'))['order__max'] or 0
        
        # 创建书签
        bookmark = Bookmark.objects.create(
            blog=blog,
            title=title,
            url=url,
            description=description,
            is_public=is_public,
            tags=json.dumps(tag_list),
            order=max_order + 1,
        )
        
        return redirect('bookmark_list', id=blog.subdomain)
    
    return redirect('bookmark_list', id=blog.subdomain)


@login_required
def bookmark_update(request, id, pk):
    """更新书签"""
    if request.user.is_superuser:
        blog = get_object_or_404(Blog, subdomain=id)
    else:
        blog = get_object_or_404(Blog, user=request.user, subdomain=id)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        # 删除操作
        if action == 'delete':
            bookmark = get_object_or_404(Bookmark, pk=pk, blog=blog)
            bookmark.delete()
            return redirect('bookmark_list', id=blog.subdomain)
        
        # 更新操作
        bookmark = get_object_or_404(Bookmark, pk=pk, blog=blog)
        
        if action == 'update':
            bookmark.title = request.POST.get('title', bookmark.title).strip()
            bookmark.url = request.POST.get('url', bookmark.url).strip()
            bookmark.description = request.POST.get('description', bookmark.description).strip()
            bookmark.is_public = request.POST.get('is_public') == 'on'
            
            # 验证URL
            if bookmark.url:
                try:
                    validator = URLValidator()
                    validator(bookmark.url)
                except ValidationError:
                    bookmark.url = 'https://' + bookmark.url
            
            # 更新标签
            tags_str = request.POST.get('tags', '')
            import json
            tag_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            bookmark.tags = json.dumps(tag_list)
            
            # 更新排序
            order_str = request.POST.get('order', '')
            if order_str:
                try:
                    bookmark.order = int(order_str)
                except ValueError:
                    pass
            
            bookmark.save()
        
        return redirect('bookmark_list', id=blog.subdomain)
    
    return redirect('bookmark_list', id=blog.subdomain)