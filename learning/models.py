from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Module(models.Model):
    title = models.CharField('Название', max_length=180)
    description = models.TextField('Описание', blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликовано', default=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Учебный модуль'
        verbose_name_plural = 'Учебные модули'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Модуль',
    )
    title = models.CharField('Название', max_length=180)
    goal = models.TextField('Цель занятия', blank=True)
    content = models.TextField('Теоретический материал')
    order = models.PositiveIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликовано', default=True)

    class Meta:
        ordering = ['module__order', 'order', 'title']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('lesson_detail', kwargs={'pk': self.pk})


class PracticeTask(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='practice_tasks',
        verbose_name='Урок',
    )
    title = models.CharField('Название', max_length=180)
    objective = models.TextField('Цель работы', blank=True)
    assignment = models.TextField('Задание')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['lesson__module__order', 'lesson__order', 'order']
        verbose_name = 'Практическое задание'
        verbose_name_plural = 'Практические задания'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('practice_detail', kwargs={'pk': self.pk})


class PracticeSubmission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_submissions',
        verbose_name='Пользователь',
    )
    task = models.ForeignKey(
        PracticeTask,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Практическое задание',
    )
    answer_text = models.TextField('Ответ студента')
    attached_file = models.FileField(
        'Прикреплённый файл',
        upload_to='practice_submissions/%Y/%m/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    teacher_comment = models.TextField('Комментарий преподавателя', blank=True)
    is_checked = models.BooleanField('Проверено', default=False)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'task'],
                name='unique_practice_submission_per_user',
            )
        ]
        verbose_name = 'Отправка практической работы'
        verbose_name_plural = 'Отправки практических работ'

    def __str__(self):
        return f'{self.user} - {self.task}'


class LessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='Пользователь',
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name='Урок',
    )
    completed_at = models.DateTimeField('Дата изучения', auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'lesson'],
                name='unique_lesson_progress_per_user',
            )
        ]
        verbose_name = 'Прогресс по уроку'
        verbose_name_plural = 'Прогресс по урокам'

    def __str__(self):
        return f'{self.user} - {self.lesson}'


class KnowledgeTest(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='knowledge_tests',
        verbose_name='Урок',
    )
    title = models.CharField('Название', max_length=180)
    description = models.TextField('Описание', blank=True)
    passing_percent = models.PositiveIntegerField(
        'Проходной процент',
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    order = models.PositiveIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликовано', default=True)

    class Meta:
        ordering = ['lesson__module__order', 'lesson__order', 'order', 'title']
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('test_detail', kwargs={'pk': self.pk})


class Question(models.Model):
    test = models.ForeignKey(
        KnowledgeTest,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Тест',
    )
    text = models.TextField('Вопрос')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['test__order', 'order']
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text[:80]


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос',
    )
    text = models.CharField('Ответ', max_length=255)
    is_correct = models.BooleanField('Правильный ответ', default=False)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['question__order', 'order']
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return self.text


class TestAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name='Пользователь',
    )
    test = models.ForeignKey(
        KnowledgeTest,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Тест',
    )
    score = models.PositiveIntegerField('Количество правильных ответов', default=0)
    total_questions = models.PositiveIntegerField('Количество вопросов', default=0)
    percent = models.PositiveIntegerField(
        'Процент выполнения',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_passed = models.BooleanField('Тест пройден', default=False)
    created_at = models.DateTimeField('Дата прохождения', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Попытка теста'
        verbose_name_plural = 'Попытки тестов'

    def __str__(self):
        return f'{self.user} - {self.test} - {self.percent}%'


class TestAttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='selected_answers',
        verbose_name='Попытка',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        related_name='attempt_answers',
        verbose_name='Вопрос',
        blank=True,
        null=True,
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.SET_NULL,
        related_name='attempt_answers',
        verbose_name='Выбранный ответ',
        blank=True,
        null=True,
    )
    question_text = models.TextField('Текст вопроса')
    selected_answer_text = models.CharField('Текст выбранного ответа', max_length=255, blank=True)
    is_correct = models.BooleanField('Ответ верный', default=False)

    class Meta:
        ordering = ['attempt', 'question__order', 'id']
        verbose_name = 'Ответ в попытке теста'
        verbose_name_plural = 'Ответы в попытках тестов'

    def __str__(self):
        return f'{self.attempt} - {self.question_text[:60]}'
