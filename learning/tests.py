from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import (
    Answer,
    KnowledgeTest,
    Lesson,
    LessonProgress,
    Module,
    PracticeSubmission,
    PracticeTask,
    Question,
    TestAttempt,
    TestAttemptAnswer,
)
from .services import get_display_attempts_by_test


class AccountViewsTests(TestCase):
    def setUp(self):
        self.module = Module.objects.create(title='Тестовый модуль', order=1)
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Тестовый урок',
            content='Материал урока',
            order=1,
        )
        self.practice_task = PracticeTask.objects.create(
            lesson=self.lesson,
            title='Практическое задание',
            objective='Проверить отправку работы',
            assignment='Опишите выполненную работу.',
            order=1,
        )
        self.knowledge_test = KnowledgeTest.objects.create(
            lesson=self.lesson,
            title='Проверочный тест',
            passing_percent=60,
        )
        self.question = Question.objects.create(
            test=self.knowledge_test,
            text='Какой ответ правильный?',
            order=1,
        )
        self.correct_answer = Answer.objects.create(
            question=self.question,
            text='Правильный ответ',
            is_correct=True,
            order=1,
        )
        Answer.objects.create(
            question=self.question,
            text='Неправильный ответ',
            is_correct=False,
            order=2,
        )
        self.user = User.objects.create_user(username='student', password='StrongPass123')
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='Admin12345!',
        )

    def test_register_page_is_available(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_admin_statistics_requires_staff_user(self):
        self.client.login(username='student', password='StrongPass123')

        response = self.client.get(reverse('admin_statistics'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_staff_user_can_view_admin_statistics(self):
        LessonProgress.objects.create(user=self.user, lesson=self.lesson)
        TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=1,
            total_questions=1,
            percent=100,
            is_passed=True,
        )
        PracticeSubmission.objects.create(
            user=self.user,
            task=self.practice_task,
            answer_text='Done',
            is_checked=True,
        )
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.get(reverse('admin_statistics'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student')
        self.assertContains(response, '1 / 1')
        self.assertContains(response, reverse('admin_user_statistics', kwargs={'pk': self.user.pk}))

    def test_staff_user_can_view_single_user_statistics(self):
        TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=1,
            total_questions=1,
            percent=100,
            is_passed=True,
        )
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.get(reverse('admin_user_statistics', kwargs={'pk': self.user.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.knowledge_test.title)
        self.assertContains(response, '100%')

    def test_staff_statistics_does_not_open_staff_users_as_students(self):
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.get(reverse('admin_user_statistics', kwargs={'pk': self.admin_user.pk}))

        self.assertEqual(response.status_code, 404)

    def test_admin_content_requires_staff_user(self):
        self.client.login(username='student', password='StrongPass123')

        response = self.client.get(reverse('admin_content'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_staff_user_can_open_admin_content(self):
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.get(reverse('admin_content'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Управление материалами')
        self.assertContains(response, 'Добавить модуль')

    def test_staff_user_can_view_practice_submissions(self):
        PracticeSubmission.objects.create(
            user=self.user,
            task=self.practice_task,
            answer_text='Submitted practice answer',
        )
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.get(reverse('admin_submissions'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отправленные работы')
        self.assertContains(response, 'Submitted practice answer')
        self.assertContains(response, self.user.username)

    def test_staff_user_can_review_practice_submission(self):
        submission = PracticeSubmission.objects.create(
            user=self.user,
            task=self.practice_task,
            answer_text='Submitted practice answer',
        )
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.post(
            reverse('admin_submission_detail', kwargs={'pk': submission.pk}),
            {
                'teacher_comment': 'Работа проверена.',
                'is_checked': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_submission_detail', kwargs={'pk': submission.pk}))
        submission.refresh_from_db()
        self.assertTrue(submission.is_checked)
        self.assertEqual(submission.teacher_comment, 'Работа проверена.')

    def test_staff_user_can_create_module_from_admin_content(self):
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.post(
            reverse('admin_content_create', kwargs={'content_type': 'module'}),
            {
                'title': 'New admin module',
                'description': 'Created from content manager',
                'order': 20,
                'is_published': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_content'))
        self.assertTrue(Module.objects.filter(title='New admin module').exists())

    def test_staff_user_can_create_lesson_from_admin_content(self):
        self.client.login(username='admin', password='Admin12345!')

        response = self.client.post(
            reverse('admin_content_create', kwargs={'content_type': 'lesson'}),
            {
                'module': self.module.pk,
                'title': 'New admin lesson',
                'goal': 'Goal',
                'content': 'Lesson content',
                'order': 10,
                'is_published': 'on',
            },
        )

        self.assertRedirects(response, reverse('admin_content'))
        self.assertTrue(Lesson.objects.filter(title='New admin lesson', module=self.module).exists())

    def test_public_lists_hide_unpublished_lesson_content(self):
        hidden_lesson = Lesson.objects.create(
            module=self.module,
            title='Hidden lesson',
            content='Hidden content',
            order=2,
            is_published=False,
        )
        hidden_task = PracticeTask.objects.create(
            lesson=hidden_lesson,
            title='Hidden practice task',
            assignment='Hidden assignment',
            order=1,
        )

        home_response = self.client.get(reverse('home'))
        module_response = self.client.get(reverse('module_list'))
        practice_response = self.client.get(reverse('practice_list'))

        self.assertEqual(home_response.status_code, 200)
        self.assertContains(home_response, '1 уроков')
        self.assertNotContains(home_response, '2 уроков')
        self.assertEqual(module_response.status_code, 200)
        self.assertNotContains(module_response, hidden_lesson.title)
        self.assertEqual(practice_response.status_code, 200)
        self.assertNotContains(practice_response, hidden_task.title)

    def test_percent_fields_validate_range(self):
        self.knowledge_test.passing_percent = 101
        with self.assertRaises(ValidationError):
            self.knowledge_test.full_clean()

        attempt = TestAttempt(
            user=self.user,
            test=self.knowledge_test,
            score=1,
            total_questions=1,
            percent=101,
            is_passed=True,
        )
        with self.assertRaises(ValidationError):
            attempt.full_clean()

    def test_display_attempt_service_does_not_depend_on_input_order(self):
        first_attempt = TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=0,
            total_questions=1,
            percent=0,
            is_passed=False,
        )
        latest_attempt = TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=1,
            total_questions=1,
            percent=60,
            is_passed=True,
        )

        display_attempts = get_display_attempts_by_test(
            [self.knowledge_test],
            [first_attempt, latest_attempt],
        )

        self.assertEqual(display_attempts[self.knowledge_test.pk], latest_attempt)

    def test_dashboard_shows_lesson_test_results(self):
        failed_test = KnowledgeTest.objects.create(
            lesson=self.lesson,
            title='Failed dashboard test',
            passing_percent=60,
            order=2,
        )
        perfect_test = KnowledgeTest.objects.create(
            lesson=self.lesson,
            title='Perfect dashboard test',
            passing_percent=60,
            order=3,
        )
        not_started_test = KnowledgeTest.objects.create(
            lesson=self.lesson,
            title='Not started dashboard test',
            passing_percent=60,
            order=4,
        )
        TestAttempt.objects.create(
            user=self.user,
            test=failed_test,
            score=0,
            total_questions=1,
            percent=0,
            is_passed=False,
        )
        TestAttempt.objects.create(
            user=self.user,
            test=perfect_test,
            score=1,
            total_questions=1,
            percent=100,
            is_passed=True,
        )
        TestAttempt.objects.create(
            user=self.user,
            test=perfect_test,
            score=0,
            total_questions=1,
            percent=0,
            is_passed=False,
        )
        self.client.login(username='student', password='StrongPass123')

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Failed dashboard test: 0%')
        self.assertContains(response, 'lesson-test-result failed')
        self.assertContains(response, 'Perfect dashboard test: 100%')
        self.assertContains(response, 'lesson-test-result passed')
        self.assertContains(response, 'Not started dashboard test: 0%')
        self.assertContains(response, 'lesson-test-result pending')
        self.assertNotContains(response, 'Perfect dashboard test: 0%')
        published_test_count = KnowledgeTest.objects.filter(
            is_published=True,
            lesson__is_published=True,
            lesson__module__is_published=True,
        ).count()
        self.assertEqual(response.context['passed_tests'], 1)
        self.assertEqual(response.context['average_test_percent'], round(100 / published_test_count))

    def test_authenticated_user_can_complete_lesson(self):
        self.client.login(username='student', password='StrongPass123')

        response = self.client.post(reverse('complete_lesson', kwargs={'pk': self.lesson.pk}))

        self.assertRedirects(response, self.lesson.get_absolute_url())
        self.assertTrue(
            LessonProgress.objects.filter(user=self.user, lesson=self.lesson).exists()
        )

    def test_test_page_requires_login(self):
        response = self.client.get(self.knowledge_test.get_absolute_url())

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_authenticated_user_can_pass_test(self):
        self.client.login(username='student', password='StrongPass123')

        response = self.client.post(
            self.knowledge_test.get_absolute_url(),
            {f'question_{self.question.pk}': str(self.correct_answer.pk)},
        )

        self.assertEqual(response.status_code, 200)
        attempt = TestAttempt.objects.get(user=self.user, test=self.knowledge_test)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.percent, 100)
        self.assertTrue(attempt.is_passed)
        attempt_answer = TestAttemptAnswer.objects.get(attempt=attempt)
        self.assertEqual(attempt_answer.question, self.question)
        self.assertEqual(attempt_answer.selected_answer, self.correct_answer)
        self.assertEqual(attempt_answer.question_text, self.question.text)
        self.assertEqual(attempt_answer.selected_answer_text, self.correct_answer.text)
        self.assertTrue(attempt_answer.is_correct)

    def test_lesson_page_marks_completed_test_attempt(self):
        TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=1,
            total_questions=1,
            percent=100,
            is_passed=True,
        )
        self.client.login(username='student', password='StrongPass123')

        response = self.client.get(self.lesson.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test-status passed')
        self.assertContains(response, '100%')
        self.assertContains(response, 'test-repeat')
        self.assertContains(response, 'Пройти ещё раз')

    def test_lesson_page_keeps_perfect_test_result(self):
        TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=1,
            total_questions=1,
            percent=100,
            is_passed=True,
        )
        TestAttempt.objects.create(
            user=self.user,
            test=self.knowledge_test,
            score=0,
            total_questions=1,
            percent=0,
            is_passed=False,
        )
        self.client.login(username='student', password='StrongPass123')

        response = self.client.get(self.lesson.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test-status passed')
        self.assertContains(response, 'Тест пройден')
        self.assertContains(response, '100%')
        self.assertNotContains(response, 'Тест не пройден')

    def test_practice_detail_requires_login(self):
        response = self.client.get(self.practice_task.get_absolute_url())

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_authenticated_user_can_submit_practice_work(self):
        self.client.login(username='student', password='StrongPass123')

        response = self.client.post(
            self.practice_task.get_absolute_url(),
            {'answer_text': 'Работа выполнена, результат проверен.'},
        )

        self.assertRedirects(response, self.practice_task.get_absolute_url())
        submission = PracticeSubmission.objects.get(user=self.user, task=self.practice_task)
        self.assertEqual(submission.answer_text, 'Работа выполнена, результат проверен.')
        self.assertFalse(submission.is_checked)
