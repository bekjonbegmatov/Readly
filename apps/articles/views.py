from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from markdown import markdown

from .models import Article, Tag, Comment, Like
from .forms import ArticleForm, CommentForm


def render_markdown(text: str) -> str:
    return markdown(text or "")


def home(request):
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
            articles = Article.objects.filter(author_id__in=followed_ids).order_by('-created_at')
        else:
            articles = Article.objects.all().order_by('-created_at')
    else:
        articles = Article.objects.all().order_by('-created_at')

    # Простейшие рекомендации: статьи с популярными тегами из последних публикаций
    popular_tags = Tag.objects.all()[:10]
    recommended = Article.objects.filter(tags__in=popular_tags).distinct().order_by('-created_at')[:10]

    return render(request, 'articles/home.html', {
        'articles': articles,
        'recommended': recommended,
    })


@login_required
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
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
    })


@login_required
def article_like(request, pk):
    article = get_object_or_404(Article, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, article=article)
    if not created:
        like.delete()
    return redirect('article_detail', pk=pk)


def search(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = Article.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__name__icontains=q)
        ).distinct().order_by('-created_at')
    return render(request, 'articles/search.html', {'query': q, 'results': results})