from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from apps.articles.models import Article, Like, Comment
from .models import Follow


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})


@login_required
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    articles = Article.objects.filter(author=user).order_by('-created_at')
    total_likes = Like.objects.filter(article__author=user).count()
    total_comments = Comment.objects.filter(article__author=user).count()
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    return render(request, 'users/profile.html', {
        'profile_user': user,
        'articles': articles,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    })


@login_required
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('profile', username=username)
    rel, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        rel.delete()
    return redirect('profile', username=username)
