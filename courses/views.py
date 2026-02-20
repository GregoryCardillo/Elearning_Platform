from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404

from .models import Course, Module, Lesson, Enrollment, Progress
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseWriteSerializer,
    ModuleSerializer,
    LessonSerializer,
    EnrollmentSerializer,
    ProgressSerializer,
    UserProfileSerializer,
)


# ============================================
# USER VIEWS
# ============================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/users/me/  → Get current user profile
    PUT  /api/users/me/  → Update current user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user


# ============================================
# COURSE VIEWS
# ============================================

class CourseListView(generics.ListCreateAPIView):
    """
    GET  /api/courses/  → List all published courses
    POST /api/courses/  → Create a new course (instructors only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return published courses with optimized queries."""
        return Course.objects.filter(
            status='published'
        ).select_related(
            'instructor'
        ).prefetch_related(
            'modules__lessons',
            'enrollments'
        )
    
    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method == 'POST':
            return CourseWriteSerializer
        return CourseListSerializer


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/courses/{slug}/  → Get course details
    PUT    /api/courses/{slug}/  → Update course (owner only)
    DELETE /api/courses/{slug}/  → Delete course (owner only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Course.objects.select_related(
            'instructor'
        ).prefetch_related(
            'modules__lessons',
            'enrollments'
        )
    
    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CourseWriteSerializer
        return CourseDetailSerializer
    
    def get_serializer_context(self):
        """Pass request to serializer for is_enrolled check."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ============================================
# MODULE VIEWS
# ============================================

class CourseModuleListView(generics.ListAPIView):
    """
    GET /api/courses/{slug}/modules/  → List all modules in a course
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get modules for a specific course."""
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        return Module.objects.filter(
            course=course
        ).prefetch_related('lessons')


# ============================================
# LESSON VIEWS
# ============================================

class ModuleLessonListView(generics.ListAPIView):
    """
    GET /api/modules/{module_id}/lessons/  → List all lessons in a module
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get lessons for a specific module."""
        module = get_object_or_404(Module, id=self.kwargs['module_id'])
        return Lesson.objects.filter(module=module)


# ============================================
# ENROLLMENT VIEWS
# ============================================

class EnrollmentListView(generics.ListAPIView):
    """
    GET /api/enrollments/  → List current user's enrollments
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's enrollments."""
        return Enrollment.objects.filter(
            student=self.request.user,
            is_active=True
        ).select_related(
            'course__instructor'
        ).prefetch_related(
            'progress_records'
        )


@api_view(['POST'])
def enroll_in_course(request, slug):
    """
    POST /api/courses/{slug}/enroll/  → Enroll in a course
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not request.user.is_student:
        return Response(
            {'error': 'Only students can enroll in courses.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    course = get_object_or_404(Course, slug=slug, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return Response(
            {'error': 'You are already enrolled in this course.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create enrollment (signal will create Progress records automatically)
    enrollment = Enrollment.objects.create(
        student=request.user,
        course=course
    )
    
    serializer = EnrollmentSerializer(enrollment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================
# PROGRESS VIEWS
# ============================================

class EnrollmentProgressView(generics.ListAPIView):
    """
    GET /api/enrollments/{enrollment_id}/progress/  → Get progress for an enrollment
    """
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get progress records for a specific enrollment."""
        enrollment = get_object_or_404(
            Enrollment,
            id=self.kwargs['enrollment_id'],
            student=self.request.user  # Ensure ownership
        )
        return Progress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson__module')


@api_view(['POST'])
def complete_lesson(request, enrollment_id, lesson_id):
    """
    POST /api/enrollments/{enrollment_id}/lessons/{lesson_id}/complete/
    → Mark a lesson as completed
    """
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user
    )
    
    progress = get_object_or_404(
        Progress,
        enrollment=enrollment,
        lesson_id=lesson_id
    )
    
    progress.mark_complete()
    
    serializer = ProgressSerializer(progress)
    return Response({
        'message': 'Lesson marked as completed!',
        'progress': serializer.data,
        'course_progress': f"{enrollment.progress_percentage}%"
    })