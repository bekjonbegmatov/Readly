import os
import random
import string
from pathlib import Path
from datetime import datetime, timedelta

from django.utils import timezone

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.core.files.base import ContentFile

from apps.users.models import Profile, Follow
from apps.articles.models import Article, Tag, Comment, Like, Favorite


def read_file_bytes(fp: Path) -> bytes:
    with open(fp, 'rb') as f:
        return f.read()


def assign_image_field(field, fp: Path, max_name_len: int = 120):
    name = fp.name[:max_name_len]
    data = read_file_bytes(fp)
    field.save(name, ContentFile(data), save=False)


class Command(BaseCommand):
    help = 'Seeds the database with demo users, articles, interactions and media.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=100, help='Number of users to create')
        parser.add_argument('--seed', type=int, default=42, help='Random seed')
        parser.add_argument('--avatar_dir', type=str, default='/Users/behruz/Documents/ESSTUM/Web Programming/Readly/media/avatars/example', help='Directory with avatar images')
        parser.add_argument('--cover_dir', type=str, default='/Users/behruz/Documents/ESSTUM/Web Programming/Readly/media/covers/example', help='Directory with cover images')
        parser.add_argument('--popular_share', type=float, default=0.25, help='Fraction of articles considered popular')
        parser.add_argument('--buckets', type=int, default=100, help='Time buckets across the current year')

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options['seed'])
        n_users = options['users']
        avatar_dir = Path(options['avatar_dir'])
        cover_dir = Path(options['cover_dir'])
        popular_share = options['popular_share']
        buckets = options['buckets']
        spreader = YearSpreader(year=timezone.now().year, buckets=buckets)

        self.stdout.write(self.style.NOTICE('Starting demo seed...'))

        avatar_files = [p for p in avatar_dir.glob('*') if p.is_file()]
        cover_files = [p for p in cover_dir.glob('*') if p.is_file()]

        tags_pool = ['tech', 'ios', 'дизайн', 'психология', 'бизнес', 'вдохновение', 'книги', 'спорт', 'музыка', 'фото']
        tag_objs = {}
        for t in tags_pool:
            tag_objs[t], _ = Tag.objects.get_or_create(name=t)

        # Users
        users: list[User] = []
        for i in range(n_users):
            username = f'user{i:03d}'
            # Avoid recreating existing users
            user, created = User.objects.get_or_create(username=username, defaults={
                'first_name': f'User{i}',
                'last_name': 'Demo',
                'email': f'{username}@example.local',
            })
            if created:
                user.set_password('pass1234')
                user.save()
            # Распределим дату регистрации по году
            set_user_date_joined(user.pk, spreader.next())
            # Ensure Profile
            profile, _ = Profile.objects.get_or_create(user=user)
            # Assign avatar to some users
            if avatar_files and random.random() < 0.6 and not profile.avatar:
                fp = random.choice(avatar_files)
                assign_image_field(profile.avatar, fp)
                profile.save()
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'Users prepared: {len(users)}'))

        # Follows network
        follow_count = 0
        for u in users:
            k = random.randint(5, 20)
            candidates = [x for x in users if x != u]
            following = random.sample(candidates, k=min(k, len(candidates)))
            for v in following:
                rel, _ = Follow.objects.get_or_create(follower=u, following=v)
                set_created_at(Follow, rel.pk, spreader.next())
                follow_count += 1
        self.stdout.write(self.style.SUCCESS(f'Follows created/ensured: ~{follow_count}'))

        # Articles
        articles: list[Article] = []
        article_target = int(n_users * 8)  # ~800 for 100 users
        # Distribute articles across users
        for i in range(article_target):
            author = random.choice(users)
            title = f"{random.choice(['Советы', 'Идеи', 'Опыт', 'Мнение', 'Обзор'])} #{i+1}"
            paragraphs = [
                '## Заголовок раздела',
                'Некоторый текст с мыслями и наблюдениями.',
                '- список пунктов\n- ещё пункт',
                f'Тэги и направление: {random.choice(tags_pool)}',
            ]
            content = '\n\n'.join(paragraphs)
            a = Article(author=author, title=title, content=content)
            # Assign cover sometimes
            if cover_files and random.random() < 0.8:
                fp = random.choice(cover_files)
                assign_image_field(a.cover, fp)
            a.save()
            set_created_at(Article, a.pk, spreader.next())
            # tags
            for t in random.sample(tags_pool, k=random.randint(1, 3)):
                a.tags.add(tag_objs[t])
            articles.append(a)
        self.stdout.write(self.style.SUCCESS(f'Articles created: {len(articles)}'))

        # Interactions: likes, comments, favorites
        total_likes = 0
        total_comments = 0
        total_favs = 0
        popular_n = int(len(articles) * popular_share)
        popular_set = set(random.sample(articles, k=popular_n)) if popular_n > 0 else set()

        comment_texts = [
            'Отличная статья! Спасибо.',
            'Согласен не со всем, но интересно.',
            'Можно больше примеров?',
            'Это помогло в проекте.',
            'Классная мысль!',
            'Спорный момент, но ок.',
            'Лаконично и по делу.',
            'Супер, жду продолжения!',
        ]

        for a in articles:
            is_popular = a in popular_set
            # Likes
            like_n = random.randint(30, 120) if is_popular else random.randint(0, 30)
            like_users = random.sample(users, k=min(like_n, len(users)))
            for u in like_users:
                like_obj, created = Like.objects.get_or_create(user=u, article=a)
                if created:
                    total_likes += 1
                set_created_at(Like, like_obj.pk, spreader.next())

            # Comments
            comment_n = random.randint(10, 30) if is_popular else random.randint(0, 10)
            comment_users = random.sample(users, k=min(comment_n, len(users)))
            for u in comment_users:
                txt = random.choice(comment_texts)
                c = Comment.objects.create(article=a, author=u, text=txt)
                total_comments += 1
                set_created_at(Comment, c.pk, spreader.next())

            # Favorites (smaller share)
            fav_n = random.randint(5, 20) if is_popular else random.randint(0, 5)
            fav_users = random.sample(users, k=min(fav_n, len(users)))
            for u in fav_users:
                fav_obj, created = Favorite.objects.get_or_create(user=u, article=a)
                if created:
                    total_favs += 1
                set_created_at(Favorite, fav_obj.pk, spreader.next())

        self.stdout.write(self.style.SUCCESS(
            f'Interactions — likes: {total_likes}, comments: {total_comments}, favorites: {total_favs}'
        ))

        self.stdout.write(self.style.SUCCESS('Demo seed completed successfully.'))
class YearSpreader:
    """Генератор дат, равномерно распределённых по году в указанном количестве корзин.

    Для анализа данных удобно получать квазирегулярное распределение: год делится на
    `buckets` интервалов, а каждая следующая дата попадает в следующий интервал с
    небольшим случайным джиттером внутри интервала.
    """

    def __init__(self, year: int, buckets: int = 100):
        tz = timezone.get_current_timezone()
        self.start = timezone.make_aware(datetime(year, 1, 1), tz)
        self.end = timezone.make_aware(datetime(year + 1, 1, 1), tz)
        total_seconds = int((self.end - self.start).total_seconds())
        # Размер шага в секундах для одной корзины
        self.buckets = max(1, buckets)
        self.step = max(1, total_seconds // self.buckets)
        self._i = 0

    def next(self) -> datetime:
        base = self.start + timedelta(seconds=self.step * (self._i % self.buckets))
        jitter = random.randint(0, max(0, self.step - 1))
        self._i += 1
        return base + timedelta(seconds=jitter)


def set_created_at(model_cls, pk, created_dt: datetime):
    """Безопасно обновляет поле created_at у объекта с заданным pk."""
    try:
        model_cls.objects.filter(pk=pk).update(created_at=created_dt)
    except Exception:
        # Игнорируем любые ошибки обновления, чтобы сид не падал
        pass


def set_user_date_joined(pk, joined_dt: datetime):
    """Обновляет дату регистрации пользователя (User.date_joined)."""
    try:
        User.objects.filter(pk=pk).update(date_joined=joined_dt)
    except Exception:
        pass
