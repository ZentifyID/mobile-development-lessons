from django.db import migrations


def create_initial_tests(apps, schema_editor):
    Lesson = apps.get_model('learning', 'Lesson')
    KnowledgeTest = apps.get_model('learning', 'KnowledgeTest')
    Question = apps.get_model('learning', 'Question')
    Answer = apps.get_model('learning', 'Answer')

    tests = [
        {
            'lesson_title': 'Введение в разработку мобильных приложений',
            'title': 'Основы мобильной разработки',
            'description': 'Проверка базовых понятий о мобильных приложениях и этапах разработки.',
            'questions': [
                {
                    'text': 'Для каких устройств в первую очередь разрабатываются мобильные приложения?',
                    'answers': [
                        ('Для смартфонов и планшетов', True),
                        ('Только для настольных компьютеров', False),
                        ('Только для серверов', False),
                    ],
                },
                {
                    'text': 'Какой этап обычно выполняется перед реализацией приложения?',
                    'answers': [
                        ('Анализ задачи и проектирование', True),
                        ('Публикация приложения', False),
                        ('Удаление исходного кода', False),
                    ],
                },
            ],
        },
        {
            'lesson_title': 'Структура Android-проекта',
            'title': 'Структура проекта Android',
            'description': 'Проверка понимания назначения основных частей Android-проекта.',
            'questions': [
                {
                    'text': 'Что обычно хранится в ресурсах Android-проекта?',
                    'answers': [
                        ('Строки, цвета, изображения и описания интерфейса', True),
                        ('Только пароли пользователей', False),
                        ('Только системные файлы Windows', False),
                    ],
                },
                {
                    'text': 'Для чего используется Gradle в Android-проекте?',
                    'answers': [
                        ('Для сборки проекта и управления зависимостями', True),
                        ('Для рисования иконок вручную', False),
                        ('Для замены операционной системы', False),
                    ],
                },
            ],
        },
    ]

    for test_order, test_data in enumerate(tests, start=1):
        lesson = Lesson.objects.filter(title=test_data['lesson_title']).first()
        if not lesson:
            continue

        knowledge_test, _ = KnowledgeTest.objects.get_or_create(
            lesson=lesson,
            title=test_data['title'],
            defaults={
                'description': test_data['description'],
                'passing_percent': 60,
                'order': test_order,
            },
        )

        for question_order, question_data in enumerate(test_data['questions'], start=1):
            question, _ = Question.objects.get_or_create(
                test=knowledge_test,
                text=question_data['text'],
                defaults={'order': question_order},
            )

            for answer_order, (answer_text, is_correct) in enumerate(question_data['answers'], start=1):
                Answer.objects.get_or_create(
                    question=question,
                    text=answer_text,
                    defaults={
                        'is_correct': is_correct,
                        'order': answer_order,
                    },
                )


def remove_initial_tests(apps, schema_editor):
    KnowledgeTest = apps.get_model('learning', 'KnowledgeTest')
    KnowledgeTest.objects.filter(
        title__in=[
            'Основы мобильной разработки',
            'Структура проекта Android',
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('learning', '0004_knowledgetest_question_answer_testattempt'),
    ]

    operations = [
        migrations.RunPython(create_initial_tests, remove_initial_tests),
    ]
