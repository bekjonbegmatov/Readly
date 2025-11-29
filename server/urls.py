from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.articles.urls')),
    path('', include('apps.users.urls')),
]

# Настройка заголовков админки под проект
admin.site.site_header = "Readly — администрирование"
admin.site.site_title = "Readly"
admin.site.index_title = "Управление проектом Readly"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
