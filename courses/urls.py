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
    
    # Courses (Public)
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<slug:slug>/modules/', views.CourseModuleListView.as_view(), name='course-modules'),
    path('courses/<slug:slug>/enroll/', views.enroll_in_course, name='course-enroll'),
    path('courses/<slug:slug>/progress/', views.CourseProgressSummaryView.as_view(), name='course-progress-summary'),
    
    # Instructor (Course Management)
    path('instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor-courses'),
    path('courses/<slug:slug>/students/', views.CourseStudentsView.as_view(), name='course-students'),
    path('courses/<slug:slug>/modules/create/', views.ModuleCreateView.as_view(), name='module-create'),
    path('modules/<int:module_id>/lessons/create/', views.LessonCreateView.as_view(), name='lesson-create'),
    
    # Modules
    path('modules/<int:module_id>/lessons/', views.ModuleLessonListView.as_view(), name='module-lessons'),
    
    # Student Dashboard
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student-dashboard'),
    
    # Enrollments (Students)
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('enrollments/<int:enrollment_id>/progress/', views.EnrollmentProgressView.as_view(), name='enrollment-progress'),
    path('enrollments/<int:enrollment_id>/unenroll/', views.unenroll_from_course, name='unenroll'),
    path('enrollments/<int:enrollment_id>/certificate/', views.enrollment_certificate, name='enrollment-certificate'),
    
    # Progress Tracking
    path('enrollments/<int:enrollment_id>/lessons/<int:lesson_id>/complete/', views.complete_lesson, name='complete-lesson'),
    path('enrollments/<int:enrollment_id>/lessons/<int:lesson_id>/reset/', views.reset_lesson_progress, name='reset-lesson'),
]