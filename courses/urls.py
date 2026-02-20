from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/verify/', views.verify_token, name='auth-verify'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    
    # User
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<slug:slug>/modules/', views.CourseModuleListView.as_view(), name='course-modules'),
    path('courses/<slug:slug>/enroll/', views.enroll_in_course, name='course-enroll'),
    
    # Modules
    path('modules/<int:module_id>/lessons/', views.ModuleLessonListView.as_view(), name='module-lessons'),
    
    # Enrollments
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/<int:enrollment_id>/progress/', views.EnrollmentProgressView.as_view(), name='enrollment-progress'),
    path('enrollments/<int:enrollment_id>/lessons/<int:lesson_id>/complete/', views.complete_lesson, name='complete-lesson'),
]