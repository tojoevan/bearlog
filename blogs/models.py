from django.utils import timezone
from django.db import models, connection
from django.contrib.postgres.search import SearchVectorField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


from zoneinfo import ZoneInfo
import os
import json
from math import log
import random
import string
import hashlib
import requests


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings', blank=True)
    upgraded = models.BooleanField(default=False, db_index=True)
    max_blogs = models.IntegerField(default=10)
    upgraded_date = models.DateTimeField(blank=True, null=True, db_index=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    order_email = models.CharField(max_length=100, blank=True, null=True)
    PLAN_TYPE_CHOICES = [
        ('monthly', 'monthly'),
        ('yearly', 'yearly'),
        ('lifetime', 'lifetime'),
    ]
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, blank=True, null=True)
    upgraded_email_sent = models.BooleanField(default=False)
    orphaned_domain_warning_email_sent = models.DateTimeField(blank=True, null=True)
    upgrade_nudge_email_sent = models.DateTimeField(blank=True, null=True)
    contribution_nudge_email_sent = models.DateTimeField(blank=True, null=True)
    discovery_hide_list = models.JSONField(default=dict, blank=True)

    dashboard_styles = models.TextField(blank=True)
    dashboard_footer = models.TextField(blank=True)

    def __str__(self):
        return f'{self.user} - Settings'


# On User save, create UserSettings
@receiver(post_save, sender=User)
def create_user_settings(sender, instance, **kwargs):
    user_settings, created = UserSettings.objects.get_or_create(user=instance)
    if user_settings.upgraded:
        user_settings.user.blogs.update(reviewed=True)


class Blog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, related_name='blogs')
    title = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    last_modified = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    last_posted = models.DateTimeField(blank=True, null=True, db_index=True)
    subdomain = models.SlugField(max_length=100, unique=True, db_index=True)
    domain = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    auth_token = models.CharField(max_length=128, blank=True)

    nav = models.TextField(default="[Home](/) [Blog](/blog/)", blank=True)
    content = models.TextField(default="Hello World!", blank=True)
    meta_description = models.CharField(max_length=200, blank=True)
    meta_image = models.CharField(max_length=200, blank=True)
    lang = models.CharField(max_length=10, default='en', blank=True, db_index=True)
    meta_tag = models.CharField(max_length=500, blank=True)
    blog_path = models.CharField(max_length=200, default="blog")
    header_directive = models.TextField(blank=True)
    footer_directive = models.TextField(blank=True)
    all_tags = models.TextField(default='[]')

    custom_styles = models.TextField(blank=True)
    overwrite_styles = models.BooleanField(
        default=False,
        choices=((True, 'Overwrite default styles'), (False, 'Extend default styles')),
        verbose_name='')
    favicon = models.CharField(max_length=100, default="🐼", blank=True)

    date_format = models.CharField(max_length=32, default="d M, Y", blank=True)

    analytics_active = models.BooleanField(default=True)
    fathom_site_id = models.CharField(max_length=8, blank=True)
    
    # TODO: Deprecate this
    public_analytics = models.BooleanField(default=False)

    post_template = models.TextField(blank=True)
    robots_txt = models.TextField(blank=True, default="User-agent: *\nAllow: /")
    rss_alias = models.CharField(max_length=100, blank=True)
    codemirror_enabled = models.BooleanField(default=True)
    
    # Discovery feed settings
    dodginess_score = models.FloatField(default=0, db_index=True)
    reviewed = models.BooleanField(default=False, db_index=True)
    ignored_date = models.DateTimeField(blank=True, null=True, db_index=True)
    permanent_ignore = models.BooleanField(default=False, db_index=True)
    to_review = models.BooleanField(default=False, db_index=True)
    reviewer_note = models.TextField(blank=True)
    hidden = models.BooleanField(default=False, db_index=True)
    flagged = models.BooleanField(default=False, db_index=True)
    posts_in_last_12_hours = models.IntegerField(default=0, db_index=True)

    @property
    def is_after_cutoff(self):
        cutoff_date = timezone.datetime(2025, 4, 20, tzinfo=ZoneInfo('UTC'))
        return self.created_date > cutoff_date
    
    @property
    def contains_code(self):
        return "```" in self.content

    @property
    def blank_bear_domain(self):
        current_host = os.getenv('MAIN_SITE_HOSTS').split(',')[0]
        return f'{self.subdomain}.{current_host}'

    @property
    def bear_domain(self):
        return f'https://{self.blank_bear_domain}'

    @property
    def blank_useful_domain(self):
        if self.domain:
            return self.domain
        else:
            return f'{self.blank_bear_domain}'

    @property
    def useful_domain(self):
        return f'https://{self.blank_useful_domain}'

    @property
    def dynamic_useful_domain(self):
        return f'//{self.blank_useful_domain}'
    
    @property
    def is_empty(self):
        content_length = len(self.content) if self.content is not None else 0
        return not self.user.settings.upgraded and content_length < 20 and self.posts.count() == 0 and self.custom_styles == ""
    
    @property
    def tags(self):
        return sorted(json.loads(self.all_tags))
    
    def generate_auth_token(self):
        allowed_chars = string.ascii_letters.replace('O', '').replace('l', '')
        self.auth_token = ''.join(random.choice(allowed_chars) for _ in range(30))
        self.save()

    def determine_dodginess(self):
        persistent_store = PersistentStore.load()
        dodgy_term_count = 0
        blacklisted_term_count = 0
        all_content = f"{self.title} {self.content}"
        
        if self.pk:
            post = self.posts.first()
            if post:
                all_content += f"{post.title} {post.content}"

        for term in persistent_store.highlight_terms:
            dodgy_term_count += all_content.lower().count(term.lower())

        for term in persistent_store.blacklist_terms:
            blacklisted_term_count += all_content.lower().count(term.lower())

        self.dodginess_score = dodgy_term_count + blacklisted_term_count * 10

    def update_all_tags(self):
        all_tags = []
        if self.pk:
            for post in Post.objects.filter(blog=self, publish=True, is_page=False, published_date__lt=timezone.now()):
                all_tags.extend(json.loads(post.all_tags))
                all_tags = list(set(all_tags))
        self.all_tags = json.dumps(all_tags)

    def invalidate_cloudflare_cache(self):
        if os.getenv('ENVIRONMENT') == 'dev':
            # Don't invalidate on dev
            return

        cloudflare_api_key = os.getenv('CLOUDFLARE_API_KEY')
        cloudflare_email = os.getenv('CLOUDFLARE_EMAIL')
        cloudflare_zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
        
        if not all([cloudflare_api_key, cloudflare_email, cloudflare_zone_id]):
            return
            
        headers = {
            'X-Auth-Email': cloudflare_email,
            'Authorization': f'Bearer {cloudflare_api_key}',
            'Content-Type': 'application/json',
        }
        
        url = f"https://api.cloudflare.com/client/v4/zones/{cloudflare_zone_id}/purge_cache"
        
        data = {
            "tags": [self.subdomain]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get('success') == True:
                print(f"Invalidated Cloudflare cache for tag: {self.subdomain}")
            else:
                errors = response_data.get('errors', [])
                print(f"Failed to invalidate Cloudflare cache for tag: {self.subdomain}")
                print(f"Errors: {errors}")

            return response_data
        except Exception as e:
            # Log the error but don't prevent the save operation
            print(f"Error invalidating Cloudflare cache for {self.subdomain}: {str(e)}")
            return None

    def save(self, *args, **kwargs):
        # Handle all tags
        self.update_all_tags()

        # Upgraded blogs are auto-reviewed
        if self.user.settings.upgraded:
            self.reviewed = True
        
        # Determine how dodgy the blog is if it's not reviewed
        if not self.reviewed:
            self.determine_dodginess()

        # When custom styles is empty set it to default (legacy overwrite patch)
        if not self.custom_styles:
            self.custom_styles = Stylesheet.objects.filter(identifier="default").first().css
            self.overwrite_styles = True
        
        # Double check subdomains are lowercase
        self.subdomain = self.subdomain.lower()

        if self.pk:
            # Update last posted
            self.last_posted = self.posts.filter(publish=True, published_date__lt=timezone.now()).order_by('-published_date').values_list('published_date', flat=True).first()

            # Update posts in last 12 hours
            self.posts_in_last_12_hours = self.posts.filter(published_date__gte=timezone.now() - timezone.timedelta(hours=12), published_date__lte=timezone.now(), publish=True, make_discoverable=True).count()

        # Save the blog
        super(Blog, self).save(*args, **kwargs)
        
        # Invalidate Cloudflare cache after saving
        if self.pk:
            self.invalidate_cloudflare_cache()

    def __str__(self):
        return f'{self.title} ({self.useful_domain})'


class Post(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='posts')
    uid = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=200, db_index=True)
    slug = models.CharField(max_length=200, db_index=True)
    alias = models.CharField(max_length=200, blank=True, db_index=True)
    published_date = models.DateTimeField(blank=True, db_index=True)
    last_modified = models.DateTimeField(auto_now_add=True, blank=True)
    all_tags = models.TextField(default='[]')
    publish = models.BooleanField(default=True, db_index=True)
    make_discoverable = models.BooleanField(default=True, db_index=True)
    is_page = models.BooleanField(default=False, db_index=True)
    content = models.TextField()
    canonical_url = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=200, blank=True)
    meta_image = models.CharField(max_length=200, blank=True)
    lang = models.CharField(max_length=10, blank=True, db_index=True)
    class_name = models.CharField(max_length=200, blank=True)

    first_published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    upvotes = models.IntegerField(default=0, db_index=True)
    shadow_votes = models.IntegerField(default=0, db_index=True)
    score = models.FloatField(default=0, db_index=True)
    hidden = models.BooleanField(default=False, db_index=True)
    search_vector = SearchVectorField(null=True)

    @property
    def contains_code(self):
        return "```" in self.content

    @property
    def tags(self):
        return sorted(json.loads(self.all_tags))
    
    @property
    def token(self):
        return hashlib.sha256(self.uid.encode()).hexdigest()[0:10]

    def update_score(self):
        self.upvotes = self.upvote_set.count()
        upvotes = self.upvotes

        if upvotes > 1: 
            # Cap upvotes at 30 so they don't stick to the top forever
            if upvotes > 30:
                upvotes = 30

            upvotes += self.shadow_votes

            log_of_upvotes = log(upvotes, 10)

            posted_at = self.first_published_at or self.published_date

            seconds = posted_at.timestamp()
            if seconds > 0:
                # Lower buoyancy means posts sink faster with time
                buoyancy = 14
                score = (log_of_upvotes) + ((seconds - 1577811600) / (buoyancy * 86400))
                self.score = score
    
    def save(self, *args, **kwargs):
        # Use to skip blog save so as to not invalidate cache
        skip_blog_save = kwargs.pop('skip_blog_save', False)

        self.slug = self.slug.lower()
        if not self.all_tags:
            self.all_tags = '[]'
        
        # Create unique random identifier
        if not self.uid:
            allowed_chars = string.ascii_letters.replace('O', '').replace('l', '')
            self.uid = ''.join(random.choice(allowed_chars) for _ in range(20))

        # Set first_published_at for score calculation
        if self.publish:
            if self.first_published_at is None or self.published_date < self.first_published_at:
                self.first_published_at = self.published_date or timezone.now()

        # Update the score for the discover feed
        if self.pk:
            self.update_score()

        # Save the post
        super(Post, self).save(*args, **kwargs)

        # Update search vector via SQL to handle large content
        # Note: to_tsvector is PostgreSQL-specific, skip for SQLite
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE blogs_post
                    SET search_vector = to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(all_tags, '') || ' ' || LEFT(COALESCE(content, ''), 50000))
                    WHERE id = %s
                """, [self.pk])

        # Save blog to trigger a few other things (unless skipped)
        if not skip_blog_save:
            self.blog.save()
            
    def __str__(self):
        return self.title


class Upvote(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    hash_id = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        # Save the Upvote instance
        super(Upvote, self).save(*args, **kwargs)
        
        # Update the post score without triggering blog save
        self.post.save(skip_blog_save=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'hash_id']),
        ]

    def __str__(self):
        return f"{self.created_date.strftime('%d %b %Y, %X')} - {self.hash_id} - {self.post}"


class Hit(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    hash_id = models.CharField(max_length=200)
    referrer = models.URLField(default=None, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    device = models.CharField(max_length=200, blank=True, null=True)
    browser = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        indexes = [
            # Optimized for the get_posts query - covers blog_id, post_id, created_date, and referrer
            models.Index(fields=['blog', 'post', 'created_date', 'referrer'], name='hit_blog_post_date_ref'),
            
            # For unique visitors
            models.Index(fields=['blog', 'created_date', 'post', 'referrer', 'hash_id'], name='hit_visitors_opt'),
            
            # For blog-level analytics queries
            models.Index(fields=['blog', 'created_date'], name='hit_blog_date'),

            # For device aggregation
            models.Index(fields=['blog', 'created_date', 'device'], name='hit_blog_date_device'),
            
            # For browser aggregation
            models.Index(fields=['blog', 'created_date', 'browser'], name='hit_blog_date_browser'),
            
            # For country aggregation
            models.Index(fields=['blog', 'created_date', 'country'], name='hit_blog_date_country'),
        ]

    def __str__(self):
        return f"{self.created_date.strftime('%d %b %Y, %X')} - {self.blog.subdomain} - {self.post}"


class Subscriber(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    email_address = models.EmailField()
    subscribed_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.blog.title} - {self.email_address}"


class Stylesheet(models.Model):
    title = models.CharField(max_length=100)
    identifier = models.SlugField(max_length=100, unique=True)
    css = models.TextField(blank=True)
    external = models.BooleanField(default=False)
    image = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title


class Media(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='media')
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    @property
    def name(self):
        return self.url.split('/')[-1]

    def __str__(self):
        return f"{self.blog.subdomain} - {self.url} - {self.created_at}"
    

# Singleton model to store Bear specific settings
class PersistentStore(models.Model):
    last_executed = models.DateTimeField(default=timezone.now)
    review_ignore_terms = models.TextField(blank=True, default='[]')
    review_highlight_terms = models.TextField(blank=True, default='[]')
    review_blacklist_terms = models.TextField(blank=True, default='[]')
    reviewed_blogs = models.JSONField(default=dict)

    @property
    def ignore_terms(self):
        return sorted(json.loads(self.review_ignore_terms))
    
    @property
    def highlight_terms(self):
        return sorted(json.loads(self.review_highlight_terms))
    
    @property
    def blacklist_terms(self):
        return sorted(json.loads(self.review_blacklist_terms))
    
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super(PersistentStore, self).save(*args, **kwargs)

    def __str__(self):
        return self.last_executed.strftime('%d %B %Y, %I:%M %p')


class Todo(models.Model):
    """待办事项模型 - 支持多用户、多blog、周期性任务"""
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    
    # 状态管理
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # 优先级
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    
    # 时间相关
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='截止日期')
    completed_date = models.DateTimeField(blank=True, null=True, verbose_name='完成日期')
    
    # 周期性任务配置
    is_recurring = models.BooleanField(default=False, db_index=True, verbose_name='是否周期性任务')
    RECURRING_CHOICES = [
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('yearly', '每年'),
        ('custom', '自定义'),
    ]
    recurring_type = models.CharField(max_length=20, choices=RECURRING_CHOICES, blank=True, null=True, verbose_name='周期类型')
    recurring_interval = models.IntegerField(default=1, verbose_name='周期间隔（天/周/月/年）')
    next_occurrence = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='下次出现时间')
    
    # 标签和分类
    tags = models.TextField(default='[]', blank=True, verbose_name='标签')
    
    # 排序
    order = models.IntegerField(default=0, db_index=True, verbose_name='排序')
    
    class Meta:
        ordering = ['-order', '-created_date']
        indexes = [
            models.Index(fields=['blog', 'status'], name='todo_blog_status'),
            models.Index(fields=['blog', 'due_date'], name='todo_blog_due_date'),
            models.Index(fields=['blog', 'is_recurring'], name='todo_blog_recurring'),
        ]
    
    @property
    def tag_list(self):
        import json
        return json.loads(self.tags) if self.tags else []
    
    def complete(self):
        """完成任务，如果是周期性任务则创建下一个实例"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_date = timezone.now()
        self.save()
        
        # 如果是周期性任务，创建下一个实例
        if self.is_recurring and self.recurring_type:
            self.create_next_occurrence()
    
    def create_next_occurrence(self):
        """为周期性任务创建下一个实例"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.next_occurrence:
            # 计算下次出现时间
            now = timezone.now()
            if self.recurring_type == 'daily':
                delta = timedelta(days=self.recurring_interval)
            elif self.recurring_type == 'weekly':
                delta = timedelta(weeks=self.recurring_interval)
            elif self.recurring_type == 'monthly':
                # 简单处理：按月增加
                month = now.month + self.recurring_interval
                year = now.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                try:
                    next_date = now.replace(year=year, month=month)
                except ValueError:
                    # 处理月末日期问题
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    next_date = now.replace(year=year, month=month, day=last_day)
                delta = next_date - now
            elif self.recurring_type == 'yearly':
                try:
                    next_date = now.replace(year=now.year + self.recurring_interval)
                except ValueError:
                    import calendar
                    last_day = calendar.monthrange(now.year + self.recurring_interval, now.month)[1]
                    next_date = now.replace(year=now.year + self.recurring_interval, day=last_day)
                delta = next_date - now
            else:
                delta = timedelta(days=self.recurring_interval)
            
            self.next_occurrence = now + delta
        
        # 创建新的待办事项
        new_todo = Todo.objects.create(
            blog=self.blog,
            title=self.title,
            description=self.description,
            status='pending',
            priority=self.priority,
            is_recurring=self.is_recurring,
            recurring_type=self.recurring_type,
            recurring_interval=self.recurring_interval,
            due_date=self.next_occurrence,
            next_occurrence=None,  # 将在下次完成时计算
            tags=self.tags,
        )
        
        # 更新当前任务的下次出现时间
        self.save()
        
        return new_todo
    
    def __str__(self):
        status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅', 'cancelled': '❌'}.get(self.status, '')
        return f"{status_icon} {self.title} ({self.blog.subdomain})"
