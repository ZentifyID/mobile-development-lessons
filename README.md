# Электронное учебное пособие

Django-сайт по дисциплине "Разработка мобильных приложений".

## Запуск проекта

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

После запуска сайт доступен по адресу:

```text
http://127.0.0.1:8000/
```

## Основные разделы

- `/` - главная страница;
- `/modules/` - учебные модули и уроки;
- `/practice/` - практические задания;
- `/practice/<id>/` - отдельная практическая работа и отправка ответа;
- `/tests/<id>/` - прохождение теста по уроку;
- `/accounts/register/` - регистрация студента;
- `/accounts/login/` - вход пользователя;
- `/dashboard/` - личный кабинет студента;
- `/admin/` - админ-панель Django.

## Демо-доступ

Администратор:

```text
login: admin
password: Admin12345!
```

Студент:

```text
login: student_demo
password: StrongPass123
```

## Наполнение демо-данными

Команда создаёт демо-пользователей, модули, уроки, практические задания, тесты, вопросы и варианты ответов:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo_content
```

## Проверка

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```
