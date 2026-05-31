from django.contrib import admin

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


admin.site.site_header = 'Разработка мобильных приложений'
admin.site.site_title = 'Разработка мобильных приложений'
admin.site.index_title = 'Управление учебными материалами'


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'is_published')


class PracticeTaskInline(admin.TabularInline):
    model = PracticeTask
    extra = 1
    fields = ('title', 'order')


class KnowledgeTestInline(admin.TabularInline):
    model = KnowledgeTest
    extra = 1
    fields = ('title', 'passing_percent', 'order', 'is_published')


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'order')


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2
    fields = ('text', 'is_correct', 'order')


class TestAttemptAnswerInline(admin.TabularInline):
    model = TestAttemptAnswer
    extra = 0
    fields = ('question_text', 'selected_answer_text', 'is_correct')
    readonly_fields = ('question_text', 'selected_answer_text', 'is_correct')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'lesson_count', 'is_published')
    list_editable = ('order', 'is_published')
    search_fields = ('title', 'description')
    inlines = [LessonInline]

    @admin.display(description='Уроков')
    def lesson_count(self, obj):
        return obj.lessons.count()


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'practice_count', 'test_count', 'is_published')
    list_filter = ('module', 'is_published')
    list_editable = ('order', 'is_published')
    search_fields = ('title', 'goal', 'content')
    inlines = [PracticeTaskInline, KnowledgeTestInline]

    @admin.display(description='Практика')
    def practice_count(self, obj):
        return obj.practice_tasks.count()

    @admin.display(description='Тесты')
    def test_count(self, obj):
        return obj.knowledge_tests.count()


@admin.register(PracticeTask)
class PracticeTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'submission_count', 'order')
    list_filter = ('lesson__module',)
    search_fields = ('title', 'objective', 'assignment')

    @admin.display(description='Отправок')
    def submission_count(self, obj):
        return obj.submissions.count()


@admin.register(PracticeSubmission)
class PracticeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_checked', 'updated_at')
    list_filter = ('is_checked', 'task__lesson__module', 'updated_at')
    list_editable = ('is_checked',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'task__title', 'answer_text')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('mark_checked', 'mark_unchecked')

    @admin.action(description='Отметить выбранные работы как проверенные')
    def mark_checked(self, request, queryset):
        queryset.update(is_checked=True)

    @admin.action(description='Снять отметку проверки')
    def mark_unchecked(self, request, queryset):
        queryset.update(is_checked=False)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed_at')
    list_filter = ('lesson__module', 'completed_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'lesson__title')
    readonly_fields = ('completed_at',)


@admin.register(KnowledgeTest)
class KnowledgeTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'question_count', 'passing_percent', 'order', 'is_published')
    list_filter = ('lesson__module', 'is_published')
    list_editable = ('passing_percent', 'order', 'is_published')
    search_fields = ('title', 'description', 'lesson__title')
    inlines = [QuestionInline]

    @admin.display(description='Вопросов')
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'answer_count', 'order')
    list_filter = ('test__lesson__module', 'test')
    search_fields = ('text', 'test__title')
    inlines = [AnswerInline]

    @admin.display(description='Ответов')
    def answer_count(self, obj):
        return obj.answers.count()


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'question__test')
    list_editable = ('is_correct', 'order')
    search_fields = ('text', 'question__text')


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'total_questions', 'percent', 'is_passed', 'created_at')
    list_filter = ('is_passed', 'test__lesson__module', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'test__title')
    readonly_fields = ('created_at',)
    inlines = [TestAttemptAnswerInline]


@admin.register(TestAttemptAnswer)
class TestAttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question_text', 'selected_answer_text', 'is_correct')
    list_filter = ('is_correct', 'attempt__test__lesson__module')
    search_fields = ('attempt__user__username', 'attempt__test__title', 'question_text', 'selected_answer_text')
    readonly_fields = ('attempt', 'question', 'selected_answer', 'question_text', 'selected_answer_text', 'is_correct')
