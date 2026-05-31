from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.StudentLoginView.as_view(), name='login'),
    path('accounts/logout/', views.StudentLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-content/', views.admin_content, name='admin_content'),
    path('admin-content/<str:content_type>/new/', views.admin_content_create, name='admin_content_create'),
    path('admin-content/<str:content_type>/<int:pk>/edit/', views.admin_content_edit, name='admin_content_edit'),
    path('admin-submissions/', views.admin_submissions, name='admin_submissions'),
    path('admin-submissions/<int:pk>/', views.admin_submission_detail, name='admin_submission_detail'),
    path('admin-stats/', views.admin_statistics, name='admin_statistics'),
    path('admin-stats/users/<int:pk>/', views.admin_user_statistics, name='admin_user_statistics'),
    path('modules/', views.module_list, name='module_list'),
    path('lessons/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:pk>/complete/', views.complete_lesson, name='complete_lesson'),
    path('tests/<int:pk>/', views.test_detail, name='test_detail'),
    path('practice/', views.practice_list, name='practice_list'),
    path('practice/<int:pk>/', views.practice_detail, name='practice_detail'),
]
