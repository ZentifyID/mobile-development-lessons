from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AnswerForm,
    KnowledgeTestForm,
    LessonForm,
    ModuleForm,
    PracticeSubmissionReviewForm,
    PracticeSubmissionForm,
    PracticeTaskForm,
    QuestionForm,
    StudentRegistrationForm,
)
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
from .services import attach_display_attempts, get_display_attempts_by_test, summarize_test_progress


CONTENT_FORMS = {
    'module': {
        'form': ModuleForm,
        'model': Module,
        'title': 'модуль',
        'plural': 'модули',
        'back': 'admin_content',
    },
    'lesson': {
        'form': LessonForm,
        'model': Lesson,
        'title': 'урок',
        'plural': 'уроки',
        'back': 'admin_content',
    },
    'practice': {
        'form': PracticeTaskForm,
        'model': PracticeTask,
        'title': 'практическое задание',
        'plural': 'практические задания',
        'back': 'admin_content',
    },
    'test': {
        'form': KnowledgeTestForm,
        'model': KnowledgeTest,
        'title': 'тест',
        'plural': 'тесты',
        'back': 'admin_content',
    },
    'question': {
        'form': QuestionForm,
        'model': Question,
        'title': 'вопрос',
        'plural': 'вопросы',
        'back': 'admin_content',
    },
    'answer': {
        'form': AnswerForm,
        'model': Answer,
        'title': 'ответ',
        'plural': 'ответы',
        'back': 'admin_content',
    },
}


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def get_published_tests():
    return list(
        KnowledgeTest.objects.filter(
            is_published=True,
            lesson__is_published=True,
            lesson__module__is_published=True,
        ).select_related('lesson', 'lesson__module')
    )


def build_user_learning_stats(user, published_tests=None, total_lessons=None):
    if published_tests is None:
        published_tests = get_published_tests()
    if total_lessons is None:
        total_lessons = Lesson.objects.filter(is_published=True, module__is_published=True).count()

    completed_count = LessonProgress.objects.filter(
        user=user,
        lesson__is_published=True,
        lesson__module__is_published=True,
    ).count()
    attempts = TestAttempt.objects.filter(user=user).select_related('test', 'test__lesson')
    display_attempts = get_display_attempts_by_test(published_tests, attempts)
    display_attempt_values = [attempt for attempt in display_attempts.values() if attempt]
    passed_tests = sum(1 for attempt in display_attempt_values if attempt.is_passed)
    average_test_percent = (
        round(sum((display_attempts[test.pk].percent if display_attempts[test.pk] else 0) for test in published_tests) / len(published_tests))
        if published_tests
        else 0
    )
    practice_submissions = PracticeSubmission.objects.filter(
        user=user,
        task__lesson__is_published=True,
        task__lesson__module__is_published=True,
    )

    return {
        'user': user,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'progress_percent': round((completed_count / total_lessons) * 100) if total_lessons else 0,
        'passed_tests': passed_tests,
        'total_tests': len(published_tests),
        'average_test_percent': average_test_percent,
        'attempt_count': attempts.count(),
        'practice_count': practice_submissions.count(),
        'checked_practice_count': practice_submissions.filter(is_checked=True).count(),
        'display_attempts': display_attempts,
    }


class StudentLoginView(LoginView):
    template_name = 'learning/login.html'


class StudentLogoutView(LogoutView):
    pass


def home(request):
    modules = (
        Module.objects.filter(is_published=True)
        .prefetch_related(
            Prefetch(
                'lessons',
                queryset=Lesson.objects.filter(is_published=True),
                to_attr='published_lessons',
            )
        )
        .order_by('order', 'title')
    )
    latest_lessons = Lesson.objects.filter(
        is_published=True,
        module__is_published=True,
    ).select_related('module')[:4]
    stats = {
        'modules': modules.count(),
        'lessons': Lesson.objects.filter(is_published=True, module__is_published=True).count(),
        'practice_tasks': PracticeTask.objects.filter(
            lesson__is_published=True,
            lesson__module__is_published=True,
        ).count(),
        'tests': KnowledgeTest.objects.filter(
            is_published=True,
            lesson__is_published=True,
            lesson__module__is_published=True,
        ).count(),
    }

    return render(
        request,
        'learning/home.html',
        {
            'modules': modules,
            'latest_lessons': latest_lessons,
            'stats': stats,
        },
    )


def module_list(request):
    modules = (
        Module.objects.filter(is_published=True)
        .prefetch_related(
            Prefetch(
                'lessons',
                queryset=Lesson.objects.filter(is_published=True),
                to_attr='published_lessons',
            )
        )
        .order_by('order', 'title')
    )
    return render(request, 'learning/module_list.html', {'modules': modules})


def lesson_detail(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related('module').prefetch_related('practice_tasks', 'knowledge_tests'),
        pk=pk,
        is_published=True,
        module__is_published=True,
    )
    is_completed = False
    lesson_tests = list(lesson.knowledge_tests.all())
    if request.user.is_authenticated:
        is_completed = LessonProgress.objects.filter(user=request.user, lesson=lesson).exists()
        test_attempts = TestAttempt.objects.filter(
            user=request.user,
            test__in=lesson_tests,
        ).order_by('-created_at')
        attach_display_attempts(lesson_tests, test_attempts)
        for test in lesson_tests:
            test.last_attempt = test.display_attempt

    return render(
        request,
        'learning/lesson_detail.html',
        {
            'lesson': lesson,
            'lesson_tests': lesson_tests,
            'is_completed': is_completed,
        },
    )


def practice_list(request):
    tasks = PracticeTask.objects.filter(
        lesson__is_published=True,
        lesson__module__is_published=True,
    ).select_related('lesson', 'lesson__module')
    return render(request, 'learning/practice_list.html', {'tasks': tasks})


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация завершена. Можно продолжать обучение.')
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'learning/register.html', {'form': form})


@login_required
def dashboard(request):
    total_lessons = Lesson.objects.filter(is_published=True, module__is_published=True).count()
    completed_lessons = LessonProgress.objects.filter(
        user=request.user,
        lesson__is_published=True,
        lesson__module__is_published=True,
    ).select_related('lesson', 'lesson__module')
    completed_count = completed_lessons.count()
    progress_percent = round((completed_count / total_lessons) * 100) if total_lessons else 0
    modules = (
        Module.objects.filter(is_published=True)
        .prefetch_related(
            Prefetch(
                'lessons',
                queryset=Lesson.objects.filter(is_published=True).prefetch_related('knowledge_tests'),
            )
        )
    )
    completed_lesson_ids = set(completed_lessons.values_list('lesson_id', flat=True))
    attempts = TestAttempt.objects.filter(user=request.user).select_related('test', 'test__lesson')
    practice_submissions = PracticeSubmission.objects.filter(user=request.user).select_related(
        'task',
        'task__lesson',
        'task__lesson__module',
    )
    module_list = list(modules)
    dashboard_tests = []
    for module in module_list:
        for lesson in module.lessons.all():
            lesson.dashboard_tests = [
                test for test in lesson.knowledge_tests.all() if test.is_published
            ]
            dashboard_tests.extend(lesson.dashboard_tests)
    attach_display_attempts(dashboard_tests, attempts.order_by('-created_at'))
    test_progress = summarize_test_progress(dashboard_tests)

    return render(
        request,
        'learning/dashboard.html',
        {
            'total_lessons': total_lessons,
            'completed_count': completed_count,
            'progress_percent': progress_percent,
            'completed_lessons': completed_lessons[:5],
            'modules': module_list,
            'completed_lesson_ids': completed_lesson_ids,
            'passed_tests': test_progress['passed_tests'],
            'average_test_percent': test_progress['average_test_percent'],
            'test_attempts': attempts[:5],
            'practice_submissions': practice_submissions[:5],
        },
    )


@login_required
@user_passes_test(is_staff_user)
def admin_content(request):
    modules = (
        Module.objects.all()
        .prefetch_related(
            Prefetch(
                'lessons',
                queryset=Lesson.objects.prefetch_related(
                    'practice_tasks',
                    Prefetch(
                        'knowledge_tests',
                        queryset=KnowledgeTest.objects.prefetch_related(
                            Prefetch('questions', queryset=Question.objects.prefetch_related('answers'))
                        ),
                    ),
                ),
            )
        )
        .order_by('order', 'title')
    )
    return render(request, 'learning/admin_content.html', {'modules': modules})


def get_content_initial(content_type, request):
    initial = {}
    if content_type == 'lesson' and request.GET.get('module'):
        initial['module'] = request.GET['module']
    elif content_type in {'practice', 'test'} and request.GET.get('lesson'):
        initial['lesson'] = request.GET['lesson']
    elif content_type == 'question' and request.GET.get('test'):
        initial['test'] = request.GET['test']
    elif content_type == 'answer' and request.GET.get('question'):
        initial['question'] = request.GET['question']
    return initial


@login_required
@user_passes_test(is_staff_user)
def admin_content_create(request, content_type):
    config = get_object_or_404_like(CONTENT_FORMS, content_type)
    form_class = config['form']
    form = form_class(request.POST or None, initial=get_content_initial(content_type, request))
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, f'{config["title"].capitalize()} сохранен.')
        return redirect('admin_content')

    return render(
        request,
        'learning/admin_content_form.html',
        {
            'form': form,
            'config': config,
            'object': None,
            'form_title': f'Создать {config["title"]}',
        },
    )


@login_required
@user_passes_test(is_staff_user)
def admin_content_edit(request, content_type, pk):
    config = get_object_or_404_like(CONTENT_FORMS, content_type)
    obj = get_object_or_404(config['model'], pk=pk)
    form = config['form'](request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{config["title"].capitalize()} обновлен.')
        return redirect('admin_content')

    return render(
        request,
        'learning/admin_content_form.html',
        {
            'form': form,
            'config': config,
            'object': obj,
            'form_title': f'Редактировать {config["title"]}',
        },
    )


def get_object_or_404_like(mapping, key):
    value = mapping.get(key)
    if value is None:
        from django.http import Http404

        raise Http404('Unknown content type')
    return value


@login_required
@user_passes_test(is_staff_user)
def admin_submissions(request):
    status = request.GET.get('status', 'all')
    submissions = PracticeSubmission.objects.select_related(
        'user',
        'task',
        'task__lesson',
        'task__lesson__module',
    ).order_by('-updated_at')

    if status == 'pending':
        submissions = submissions.filter(is_checked=False)
    elif status == 'checked':
        submissions = submissions.filter(is_checked=True)
    else:
        status = 'all'

    totals = {
        'all': PracticeSubmission.objects.count(),
        'pending': PracticeSubmission.objects.filter(is_checked=False).count(),
        'checked': PracticeSubmission.objects.filter(is_checked=True).count(),
    }

    return render(
        request,
        'learning/admin_submissions.html',
        {
            'submissions': submissions,
            'status': status,
            'totals': totals,
        },
    )


@login_required
@user_passes_test(is_staff_user)
def admin_submission_detail(request, pk):
    submission = get_object_or_404(
        PracticeSubmission.objects.select_related(
            'user',
            'task',
            'task__lesson',
            'task__lesson__module',
        ),
        pk=pk,
    )
    form = PracticeSubmissionReviewForm(request.POST or None, instance=submission)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Проверка практической работы сохранена.')
        return redirect('admin_submission_detail', pk=submission.pk)

    return render(
        request,
        'learning/admin_submission_detail.html',
        {
            'submission': submission,
            'form': form,
        },
    )


@login_required
@user_passes_test(is_staff_user)
def admin_statistics(request):
    published_tests = get_published_tests()
    total_lessons = Lesson.objects.filter(is_published=True, module__is_published=True).count()
    students = User.objects.filter(is_staff=False, is_superuser=False).order_by('last_name', 'first_name', 'username')
    student_stats = [
        build_user_learning_stats(student, published_tests=published_tests, total_lessons=total_lessons)
        for student in students
    ]
    totals = {
        'students': len(student_stats),
        'completed_lessons': sum(stats['completed_count'] for stats in student_stats),
        'passed_tests': sum(stats['passed_tests'] for stats in student_stats),
        'practice_submissions': sum(stats['practice_count'] for stats in student_stats),
    }

    return render(
        request,
        'learning/admin_statistics.html',
        {
            'student_stats': student_stats,
            'totals': totals,
            'total_lessons': total_lessons,
            'total_tests': len(published_tests),
        },
    )


@login_required
@user_passes_test(is_staff_user)
def admin_user_statistics(request, pk):
    student = get_object_or_404(User, pk=pk, is_staff=False, is_superuser=False)
    published_tests = get_published_tests()
    stats = build_user_learning_stats(student, published_tests=published_tests)
    test_rows = [
        {
            'test': test,
            'attempt': stats['display_attempts'][test.pk],
            'percent': stats['display_attempts'][test.pk].percent if stats['display_attempts'][test.pk] else 0,
        }
        for test in published_tests
    ]
    completed_lessons = LessonProgress.objects.filter(
        user=student,
        lesson__is_published=True,
        lesson__module__is_published=True,
    ).select_related('lesson', 'lesson__module')[:10]
    attempts = TestAttempt.objects.filter(user=student).select_related('test', 'test__lesson')[:10]
    submissions = PracticeSubmission.objects.filter(user=student).select_related(
        'task',
        'task__lesson',
        'task__lesson__module',
    )[:10]

    return render(
        request,
        'learning/admin_user_statistics.html',
        {
            'student': student,
            'stats': stats,
            'test_rows': test_rows,
            'completed_lessons': completed_lessons,
            'attempts': attempts,
            'submissions': submissions,
        },
    )


@login_required
@require_POST
def complete_lesson(request, pk):
    lesson = get_object_or_404(
        Lesson,
        pk=pk,
        is_published=True,
        module__is_published=True,
    )
    LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    messages.success(request, 'Урок отмечен как изученный.')
    return redirect(lesson)


@login_required
def test_detail(request, pk):
    knowledge_test = get_object_or_404(
        KnowledgeTest.objects.select_related('lesson', 'lesson__module').prefetch_related(
            Prefetch('questions', queryset=Question.objects.prefetch_related('answers'))
        ),
        pk=pk,
        is_published=True,
        lesson__is_published=True,
        lesson__module__is_published=True,
    )
    questions = list(knowledge_test.questions.all())

    if request.method == 'POST':
        total_questions = len(questions)
        score = 0
        selected_answers = {}

        for question in questions:
            answer_id = request.POST.get(f'question_{question.pk}')
            if not answer_id:
                selected_answers[question.pk] = None
                continue

            selected_answer = next(
                (answer for answer in question.answers.all() if str(answer.pk) == answer_id),
                None,
            )
            selected_answers[question.pk] = selected_answer
            correct_answer_ids = {
                str(answer.pk)
                for answer in question.answers.all()
                if answer.is_correct
            }
            if answer_id in correct_answer_ids:
                score += 1

        percent = round((score / total_questions) * 100) if total_questions else 0
        with transaction.atomic():
            attempt = TestAttempt.objects.create(
                user=request.user,
                test=knowledge_test,
                score=score,
                total_questions=total_questions,
                percent=percent,
                is_passed=percent >= knowledge_test.passing_percent,
            )
            TestAttemptAnswer.objects.bulk_create(
                [
                    TestAttemptAnswer(
                        attempt=attempt,
                        question=question,
                        selected_answer=selected_answers[question.pk],
                        question_text=question.text,
                        selected_answer_text=selected_answers[question.pk].text if selected_answers[question.pk] else '',
                        is_correct=bool(selected_answers[question.pk] and selected_answers[question.pk].is_correct),
                    )
                    for question in questions
                ]
            )

        return render(
            request,
            'learning/test_result.html',
            {
                'knowledge_test': knowledge_test,
                'attempt': attempt,
            },
        )

    last_attempt = TestAttempt.objects.filter(user=request.user, test=knowledge_test).first()
    return render(
        request,
        'learning/test_detail.html',
        {
            'knowledge_test': knowledge_test,
            'questions': questions,
            'last_attempt': last_attempt,
        },
    )


@login_required
def practice_detail(request, pk):
    task = get_object_or_404(
        PracticeTask.objects.select_related('lesson', 'lesson__module'),
        pk=pk,
        lesson__is_published=True,
        lesson__module__is_published=True,
    )
    submission = PracticeSubmission.objects.filter(user=request.user, task=task).first()

    if request.method == 'POST':
        form = PracticeSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.task = task
            submission.is_checked = False
            submission.save()
            messages.success(request, 'Практическая работа отправлена.')
            return redirect(task)
    else:
        form = PracticeSubmissionForm(instance=submission)

    return render(
        request,
        'learning/practice_detail.html',
        {
            'task': task,
            'submission': submission,
            'form': form,
        },
    )
