from django.db import migrations


def create_initial_content(apps, schema_editor):
    Module = apps.get_model('learning', 'Module')
    Lesson = apps.get_model('learning', 'Lesson')
    PracticeTask = apps.get_model('learning', 'PracticeTask')

    module_data = [
        {
            'title': 'Основы мобильной разработки',
            'description': 'Введение в мобильные приложения, платформы, типы приложений и основные этапы разработки.',
            'order': 1,
            'lessons': [
                {
                    'title': 'Введение в разработку мобильных приложений',
                    'goal': 'Сформировать представление о назначении мобильных приложений и этапах их создания.',
                    'content': (
                        'Мобильное приложение - это программный продукт, предназначенный для работы на смартфонах, '
                        'планшетах и других портативных устройствах.\n\n'
                        'При разработке важно учитывать размер экрана, способ ввода, производительность устройства, '
                        'энергопотребление и особенности операционной системы.\n\n'
                        'Типовой процесс разработки включает анализ задачи, проектирование интерфейса, реализацию, '
                        'тестирование и подготовку приложения к публикации.'
                    ),
                    'practice': {
                        'title': 'Анализ мобильного приложения',
                        'objective': 'Научиться выделять назначение, аудиторию и основные функции приложения.',
                        'assignment': (
                            'Выберите любое мобильное приложение и опишите его назначение, целевую аудиторию, '
                            'основные экраны и функции. Сформулируйте, какие задачи пользователя решает приложение.'
                        ),
                    },
                },
            ],
        },
        {
            'title': 'Среда разработки Android Studio',
            'description': 'Знакомство с инструментами Android Studio, структурой проекта и запуском приложения.',
            'order': 2,
            'lessons': [
                {
                    'title': 'Структура Android-проекта',
                    'goal': 'Разобраться с основными файлами и каталогами Android-проекта.',
                    'content': (
                        'Android-проект состоит из исходного кода, ресурсов, файлов конфигурации и Gradle-скриптов.\n\n'
                        'Исходный код отвечает за поведение приложения, ресурсы содержат изображения, строки, цвета '
                        'и описания интерфейса, а Gradle управляет сборкой и зависимостями проекта.'
                    ),
                    'practice': {
                        'title': 'Создание первого проекта',
                        'objective': 'Получить базовые навыки работы с Android Studio.',
                        'assignment': (
                            'Создайте новый проект в Android Studio, запустите его на эмуляторе или устройстве, '
                            'измените текст на стартовом экране и сделайте скриншот результата.'
                        ),
                    },
                },
            ],
        },
        {
            'title': 'Пользовательский интерфейс',
            'description': 'Основы построения экранов, работа с элементами интерфейса и принципами удобства.',
            'order': 3,
            'lessons': [
                {
                    'title': 'Компоненты интерфейса мобильного приложения',
                    'goal': 'Познакомиться с базовыми элементами интерфейса и их назначением.',
                    'content': (
                        'Интерфейс мобильного приложения состоит из визуальных компонентов: текстовых полей, кнопок, '
                        'списков, изображений, панелей навигации и других элементов.\n\n'
                        'Хороший интерфейс должен быть понятным, предсказуемым и удобным для работы на небольшом экране.'
                    ),
                    'practice': {
                        'title': 'Макет экрана приложения',
                        'objective': 'Закрепить принципы построения простого мобильного интерфейса.',
                        'assignment': (
                            'Спроектируйте экран приложения с заголовком, текстовым описанием, изображением и кнопкой. '
                            'Опишите назначение каждого элемента интерфейса.'
                        ),
                    },
                },
            ],
        },
    ]

    for module_item in module_data:
        lessons = module_item.pop('lessons')
        module, _ = Module.objects.get_or_create(
            title=module_item['title'],
            defaults=module_item,
        )

        for index, lesson_item in enumerate(lessons, start=1):
            practice = lesson_item.pop('practice')
            lesson, _ = Lesson.objects.get_or_create(
                module=module,
                title=lesson_item['title'],
                defaults={**lesson_item, 'order': index},
            )
            PracticeTask.objects.get_or_create(
                lesson=lesson,
                title=practice['title'],
                defaults={**practice, 'order': index},
            )


def remove_initial_content(apps, schema_editor):
    Module = apps.get_model('learning', 'Module')
    Module.objects.filter(
        title__in=[
            'Основы мобильной разработки',
            'Среда разработки Android Studio',
            'Пользовательский интерфейс',
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('learning', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_content, remove_initial_content),
    ]
