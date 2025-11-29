# Readly — курсовой проект

Readly — учебный веб‑проект на Django для публикации, чтения и обсуждения статей. Интерфейс ориентирован на мобильные устройства, поддерживает динамическую подгрузку, рекомендации, лайки, комментарии, избранное и базовые социальные связи между пользователями.

## Кратко о функциональности

- Лента статей с сегментами: `Вдохновляющее`, `Обсуждаемое`, `Новое`, `Психология`, `Бизнес`.
- Динамическая подгрузка ленты (IntersectionObserver + AJAX частичные шаблоны).
- Просмотр статьи: обложка, теги, Markdown‑контент, лайк, комментарии, добавление в избранное.
- Поиск по статьям и авторам.
- Профиль пользователя: аватар, статистика (лайки/комментарии), подписки и подписчики, настройки профиля.
- Авторизация: вход/выход, регистрация.

## Технологии и инструменты

- Backend: `Django 5.x` (ORM, шаблоны, вьюхи, формы, middleware).
- База данных: `SQLite` (по умолчанию), легко заменить на PostgreSQL.
- Frontend: `Tailwind CSS` (CDN), `Lucide` для иконок.
- Markdown: `python-markdown` для рендеринга контента статьи на сервере.
- Медиаконтент: загрузка файлов (ImageField), статика (`static/`) и медиа (`media/`).
- Демоданные: management‑команда `seed_demo` для генерации пользователей, статей, взаимодействий.

## Структура проекта

- `server/` — конфигурация Django (settings, urls, wsgi, asgi).
- `apps/articles/` — доменная логика статей, теги, лайки, комментарии, избранное.
- `apps/users/` — профили, подписки (Follow), формы и вьюхи пользователей.
- `templates/` — HTML‑шаблоны страниц и частичных блоков.
- `static/` — статические ресурсы (manifest, sw.js, стили).
- `media/` — загруженные пользователями файлы (аватары, обложки).

## Настройки Django (server/settings.py)

- `INSTALLED_APPS`: `apps.users`, `apps.articles`, системные приложения Django.
- `DATABASES`: SQLite (`db.sqlite3`).
- `TEMPLATES.DIRS`: `templates/` в корне.
- `STATIC_URL`: `static/`, `STATICFILES_DIRS`: `[BASE_DIR / 'static']`.
- `MEDIA_URL`: `media/`, `MEDIA_ROOT`: `BASE_DIR / 'media'`.
- `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` настроены на базовые пути.

## Маршруты (server/urls.py)

- `admin/` — админ‑панель.
- `''` — `apps.articles.urls` и `apps.users.urls`.

### Статьи (apps/articles/urls.py)

- `/` — главная лента (home).
- `/article/create/` — создание статьи.
- `/article/<pk>/` — просмотр статьи.
- `/article/<pk>/like/` — лайк/анлайк.
- `/article/<pk>/favorite/` — избранное/удаление из избранного.
- `/favorites/` — список избранного.
- `/search/` — поиск.

### Пользователи (apps/users/urls.py)

- `/login/`, `/logout/`, `/signup/` — аутентификация.
- `/u/<username>/` — профиль пользователя.
- `/u/<username>/follow/` — подписка/отписка.
- `/u/<username>/avatar/` — загрузка аватара.
- `/settings/profile/` — настройки профиля (имя, фамилия, ник + аватар).

## Модели и связи (apps/articles/models.py, apps/users/models.py)

- `Tag(name)` — тег статьи, `ManyToMany` с `Article`.
- `Article(author, title, content, cover, tags)` — статья, `author: User`, `tags: Tag[*]`.
  - `@property likes_count` и `@property comments_count` — счётчики как свойства модели.
- `Like(user, article)` — лайк, уникальная пара `(user, article)`.
- `Comment(article, author, text)` — комментарий к статье.
- `Favorite(user, article)` — избранное, уникальная пара `(user, article)`.
- `Follow(follower, following)` — связь подписки между пользователями, уникальная пара `(follower, following)`.
- `Profile(user, avatar)` — профиль с аватаром (создаётся сигналом `post_save`).

Схема связей: `User 1—* Article`, `Article *—* Tag`, `User *—* Article (Like/Favorite)`, `User *—* User (Follow)`, `Article 1—* Comment`.

## Вьюхи и логика (apps/articles/views.py)

- `home(request)`
  - Сегменты ленты: фильтруют `base_qs` и добавляют аннотации `likes_total`, `comments_total` через `Count()`.
  - Рекомендации: простая выборка по популярным тегам с аннотацией счётчиков.
  - Пагинация: `Paginator(articles, 20)` и частичный рендер `_items.html` при `partial=1` (для AJAX).
- `article_create(request)`
  - `ArticleForm`: сохранение статьи, обработка тегов из `tags_input`.
  - Если указан `cover_url`, скачивает файл и сохраняет как обложку (с определением расширения по `Content-Type`).
- `article_detail(request, pk)`
  - Рендер Markdown на сервере: `render_markdown()` → `content_html`.
  - Лайк/избранное/комментарии: взаимодействия через POST/GET.
- `favorites(request)`
  - Вывод избранных статей текущего пользователя.
- `search(request)`
  - Поиск по `Article` (title/content/tags) и авторам (`User`) + аннотации счётчиков.

### Пользовательские вьюхи (apps/users/views.py)

- `signup` — создание пользователя и автоматический вход.
- `profile` — страница профиля, счётчики взаимодействий, флаг подписки (`is_following`), подбор цвета аватара.
- `follow_toggle` — подписка/отписка.
- `avatar_upload` — загрузка аватара.
- `profile_settings` — редактирование профиля и аватара.

## Формы (apps/articles/forms.py, apps/users/forms.py)

- `ArticleForm` — заголовок, контент, файл обложки + `cover_url` (URL) и `tags_input` (строка).
- `CommentForm` — поле `text`.
- `SignupForm` — наследует `UserCreationForm`, унифицированные классы Tailwind.
- `AvatarForm` — загрузка аватара (`Profile.avatar`).
- `ProfileEditForm` — редактирование `User.username/first_name/last_name`.

## Шаблоны и фронтенд

- Базовый макет: `templates/base.html` — навигация, поиск, нижняя панель, иконки Lucide, Tailwind.
- Статьи:
  - `home.html` — сегменты, блок рекомендаций, динамическая подгрузка.
  - `_items.html` / `_item.html` — частичный список и карточка статьи.
  - `detail.html` — чтение статьи, Markdown, лайки, комментарии.
  - `create.html` — форма создания статьи.
  - `favorites.html` — избранное.
- Пользователи: `users/profile.html`, `users/settings.html`.
- Аутентификация: `auth/login.html`, `auth/signup.html`.

### Динамическая подгрузка (home.html)

- JS (`fetch`) запрашивает `/?page=<N>&partial=1&seg=<seg>` с заголовком `X-Requested-With: XMLHttpRequest`.
- Ответ — HTML `_items.html`, который добавляется в контейнер `#feed`.
- `IntersectionObserver` вызывает автоподгрузку при появлении кнопки `#loadMore` в зоне видимости.
- Дополнительная проверка окончания ленты — запрос следующей страницы; при пустом ответе кнопка скрывается.

## Алгоритмы и подходы

- Аннотации счётчиков: `likes_total` и `comments_total` через `Count()` — безопасные алиасы, чтобы не конфликтовать с `@property`.
- Рекомендации: выборка статей по популярным тегам из последних публикаций, сортировка по `created_at`.
- Пагинация: серверная (Django `Paginator`) + клиентская автоподгрузка.
- Рендеринг контента: Markdown → HTML на сервере, `content_html|safe` в шаблоне.
- Загрузка изображений по URL: определение расширения из `Content-Type`, безопасное имя файла, `ContentFile`.

## Docker запуск (порт 8080)

- Включены файлы:
  - `Dockerfile` — Python + gunicorn + entrypoint.
  - `docker-compose.yml` — сервисы `web` (Django) и `nginx` (reverse proxy).
  - `nginx.conf` — конфигурация Nginx для `/static/` и `/media/` и проксирования на `web:8000`.
  - `entrypoint.sh` — автоматические миграции и сбор статики.

### Быстрый старт

- Установите Docker и Docker Compose Plugin.
- В корне проекта выполните: `docker compose up -d --build`
- Откройте `http://<IP>:8080` — приложение будет доступно.

### Что делает entrypoint

- `python manage.py migrate --noinput`
- `python manage.py collectstatic --noinput`
- `gunicorn server.wsgi:application --bind 0.0.0.0:8000 --workers 3`

### Команды управления

- Пересборка и запуск: `docker compose up -d --build`
- Логи приложения: `docker compose logs -f web`
- Логи Nginx: `docker compose logs -f nginx`
- Остановка: `docker compose down`

### Данные

- По умолчанию используется SQLite внутри контейнера (эпhemeral). Для постоянства данных добавлю том для БД или PostgreSQL по запросу.
