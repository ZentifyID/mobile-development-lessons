from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Answer, KnowledgeTest, Lesson, Module, PracticeSubmission, PracticeTask, Question


class AdminModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.setdefault('class', 'admin-input')


class ModuleForm(AdminModelForm):
    class Meta:
        model = Module
        fields = ('title', 'description', 'order', 'is_published')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class LessonForm(AdminModelForm):
    class Meta:
        model = Lesson
        fields = ('module', 'title', 'goal', 'content', 'order', 'is_published')
        widgets = {
            'goal': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }


class PracticeTaskForm(AdminModelForm):
    class Meta:
        model = PracticeTask
        fields = ('lesson', 'title', 'objective', 'assignment', 'order')
        widgets = {
            'objective': forms.Textarea(attrs={'rows': 3}),
            'assignment': forms.Textarea(attrs={'rows': 8}),
        }


class KnowledgeTestForm(AdminModelForm):
    class Meta:
        model = KnowledgeTest
        fields = ('lesson', 'title', 'description', 'passing_percent', 'order', 'is_published')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class QuestionForm(AdminModelForm):
    class Meta:
        model = Question
        fields = ('test', 'text', 'order')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
        }


class AnswerForm(AdminModelForm):
    class Meta:
        model = Answer
        fields = ('question', 'text', 'is_correct', 'order')


class StudentRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }


class PracticeSubmissionForm(forms.ModelForm):
    class Meta:
        model = PracticeSubmission
        fields = ('answer_text', 'attached_file')
        labels = {
            'answer_text': 'Ответ',
            'attached_file': 'Файл с выполненной работой',
        }
        widgets = {
            'answer_text': forms.Textarea(
                attrs={
                    'rows': 8,
                    'placeholder': 'Опишите выполненную работу, основные шаги и результат.',
                }
            )
        }


class PracticeSubmissionReviewForm(AdminModelForm):
    class Meta:
        model = PracticeSubmission
        fields = ('teacher_comment', 'is_checked')
        labels = {
            'teacher_comment': 'Комментарий преподавателя',
            'is_checked': 'Работа проверена',
        }
        widgets = {
            'teacher_comment': forms.Textarea(attrs={'rows': 5}),
        }
