from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from .forms import SignupForm, AvatarForm, ProfileEditForm

from apps.articles.models import Article, Like, Comment
from .models import Follow


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignupForm()
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
    # Ensure Profile exists
    try:
        profile = user.profile
    except Exception:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=user)

    # Color from username hash (HSL)
    import hashlib
    hue = int(hashlib.md5(user.username.encode()).hexdigest()[:6], 16) % 360
    avatar_bg = f'hsl({hue}, 70%, 85%)'

    avatar_form = None
    if request.user == user:
        avatar_form = AvatarForm(instance=profile)

    return render(request, 'users/profile.html', {
        'profile_user': user,
        'profile': profile,
        'articles': articles,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'avatar_bg': avatar_bg,
        'avatar_form': avatar_form,
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


@login_required
def avatar_upload(request, username):
    if request.user.username != username:
        return redirect('profile', username=username)
    user = request.user
    profile = getattr(user, 'profile', None)
    if profile is None:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=user)
    if request.method == 'POST':
        form = AvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
    return redirect('profile', username=username)


@login_required
def profile_settings(request):
    user = request.user
    # Ensure Profile exists
    profile = getattr(user, 'profile', None)
    if profile is None:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=user)
        avatar_form = AvatarForm(request.POST, request.FILES, instance=profile)
        ok = True
        if form.is_valid():
            form.save()
        else:
            ok = False
        if avatar_form.is_valid():
            avatar_form.save()
        else:
            ok = False
        if ok:
            return redirect('profile', username=user.username)
    else:
        form = ProfileEditForm(instance=user)
        avatar_form = AvatarForm(instance=profile)
    return render(request, 'users/settings.html', {'form': form, 'avatar_form': avatar_form})
