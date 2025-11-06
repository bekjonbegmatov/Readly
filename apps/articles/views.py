from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from markdown import markdown
from django.core.files.base import ContentFile
from urllib.request import urlopen
from urllib.parse import urlparse
import os

from .models import Article, Tag, Comment, Like, Favorite
from .forms import ArticleForm, CommentForm


def render_markdown(text: str) -> str:
    return markdown(text or "")


def home(request):
    seg = request.GET.get('seg', '').strip()
    if request.user.is_authenticated:
        # Простая лента: статьи от пользователей, на которых подписаны, иначе последние
        followed_ids = []
        try:
            from apps.users.models import Follow
            followed_ids = list(
                Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)
            )
        except Exception:
            pass
        if followed_ids:
            base_qs = Article.objects.filter(author_id__in=followed_ids)
        else:
            base_qs = Article.objects.all()
    else:
        base_qs = Article.objects.all()

    # Фильтры сегментов (чипы)
    if seg == 'popular':
        # Используем другое имя аннотации для сортировки и добавляем счётчики
        articles = base_qs.annotate(
            num_likes=Count('likes'),
            likes_total=Count('likes'),
            comments_total=Count('comments')
        ).order_by('-num_likes', '-created_at')
    elif seg == 'new':
        articles = base_qs.annotate(
            likes_total=Count('likes'),
            comments_total=Count('comments')
        ).order_by('-created_at')
    elif seg == 'psychology':
        articles = base_qs.filter(tags__name__icontains='психолог').distinct().annotate(
            likes_total=Count('likes'),
            comments_total=Count('comments')
        ).order_by('-created_at')
    elif seg == 'business':
        articles = base_qs.filter(tags__name__icontains='бизнес').distinct().annotate(
            likes_total=Count('likes'),
            comments_total=Count('comments')
        ).order_by('-created_at')
    elif seg == 'inspire':
        articles = base_qs.filter(tags__name__icontains='вдох').distinct().annotate(
            likes_total=Count('likes'),
            comments_total=Count('comments')
        ).order_by('-created_at')
    else:
        articles = base_qs.annotate(
            likes_total=Count('likes'),
            comments_total=Count('comments')
        ).order_by('-created_at')

    # Простейшие рекомендации: статьи с популярными тегами из последних публикаций
    popular_tags = Tag.objects.all()[:10]
    recommended = Article.objects.filter(tags__in=popular_tags).distinct().annotate(
        likes_total=Count('likes'),
        comments_total=Count('comments')
    ).order_by('-created_at')[:10]
    # Пагинация и частичный рендер для динамической подгрузки
    page = int(request.GET.get('page', '1') or 1)
    paginator = Paginator(articles, 20)
    page_obj = paginator.get_page(page)

    # Если запрошен частичный контент (AJAX), возвращаем только список статей
    if request.GET.get('partial') == '1':
        return render(request, 'articles/_items.html', {
            'articles': page_obj,
        })

    return render(request, 'articles/home.html', {
        'articles': page_obj,
        'recommended': recommended,
        'seg': seg,
    })


@login_required
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            # Если файл не загружен, но указан URL — скачиваем и сохраняем как обложку
            try:
                has_file = bool(request.FILES.get('cover'))
                cover_url = (form.cleaned_data.get('cover_url') or '').strip()
                if not has_file and cover_url:
                    resp = urlopen(cover_url, timeout=6)
                    data = resp.read()
                    content_type = (resp.headers.get('Content-Type') or '').lower()
                    ext_map = {
                        'image/jpeg': 'jpg',
                        'image/jpg': 'jpg',
                        'image/png': 'png',
                        'image/webp': 'webp',
                    }
                    ext = ext_map.get(content_type.split(';')[0], '')
                    parsed = urlparse(cover_url)
                    base = os.path.basename(parsed.path) or 'cover'
                    if not os.path.splitext(base)[1] and ext:
                        base = f"{base}.{ext}"
                    filename = base[:120]
                    article.cover.save(filename, ContentFile(data), save=False)
            except Exception:
                # Тихо игнорируем ошибки загрузки URL, чтобы не мешать публикации
                pass
            article.save()
            # обработка тегов
            tags_raw = form.cleaned_data.get('tags_input', '')
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                article.tags.add(tag)
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'articles/create.html', {'form': form})


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    comments = article.comments.order_by('created_at')
    comment_form = CommentForm()
    content_html = render_markdown(article.content)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, article=article).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.author = request.user
            comment.save()
            return redirect('article_detail', pk=pk)

    return render(request, 'articles/detail.html', {
        'article': article,
        'content_html': content_html,
        'comments': comments,
        'comment_form': comment_form,
        'is_favorite': is_favorite,
    })


@login_required
def article_like(request, pk):
    article = get_object_or_404(Article, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, article=article)
    if not created:
        like.delete()
    return redirect('article_detail', pk=pk)


@login_required
def article_favorite(request, pk):
    article = get_object_or_404(Article, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, article=article)
    if not created:
        fav.delete()
    return redirect('article_detail', pk=pk)


@login_required
def favorites(request):
    favorites_qs = Favorite.objects.filter(user=request.user).select_related('article').order_by('-created_at')
    articles = [f.article for f in favorites_qs]
    return render(request, 'articles/favorites.html', {'articles': articles})


def search(request):
    q = request.GET.get('q', '').strip()
    articles = []
    authors = []
    if q:
        articles = Article.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__name__icontains=q)
        ).annotate(likes_total=Count('likes'), comments_total=Count('comments')).distinct().order_by('-created_at')
        authors = User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        ).order_by('username')[:20]
    return render(request, 'articles/search.html', {'query': q, 'results': articles, 'authors': authors})