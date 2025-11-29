from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт администратора с username=apple и паролем 12345678, если он отсутствует"

    def handle(self, *args, **options):
        User = get_user_model()
        username = "apple"
        password = "12345678"
        email = "admin@example.com"

        try:
            user = User.objects.filter(username=username).first()
            if user is None:
                self.stdout.write(f"Создаю администратора '{username}'…")
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS("Администратор создан"))
            else:
                # Если пользователь существует, убеждаемся, что это админ
                updated = False
                if not user.is_superuser or not user.is_staff:
                    user.is_superuser = True
                    user.is_staff = True
                    updated = True
                # Пароль не переустанавливаем, чтобы не затирать изменения
                if updated:
                    user.save()
                    self.stdout.write(self.style.SUCCESS("Пользователь существовал — права повышены до администратора"))
                else:
                    self.stdout.write("Администратор уже существует — пропускаю")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка создания администратора: {e}"))
            raise

