from rest_framework import serializers 
from .models import User, Course, Module, Lesson, Enrollment, Progress

# ==========================================
# USER SERIALIZERS
# ==========================================

class UserPublicSerializer(serializers.ModelSerializer):
    """
    Public user info (shown to other users)
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'bio', 'profile_picture']
        read_only_fields = ('id', 'email', 'role')

    def get_full_name(self, obj):
        return obj.get_full_name()
    
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Detailed user profile (shown to the user themselves).
    """
    full_name = serializers.SerializerMethodField()
    total_enrollments = serializers.SerializerMethodField()
    total_courses_created = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'bio', 'profile_picture', 'date_joined',
            'total_enrollments', 'total_courses_created'
        )
        read_only_fields = ('id', 'email', 'role', 'date_joined')

    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_total_enrollments(self, obj):
        """Total courses enrolled (for students)."""
        return obj.enrollments.count() if obj.is_student else None
    
    def get_total_courses_created(self, obj):
        """Total courses created (for instructors)."""
        return obj.courses_created.count() if obj.is_instructor else None

# ============================================
# LESSON SERIALIZERS
# ============================================

class LessonSerializer(serializers.ModelSerializer):
    """
    Lesson serializer with full details.
    """

    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'content_type', 'content',
            'video_url', 'duration_minutes', 'order', 'is_free'
        )
        read_only_fields = ('id',)

class LessonListSerializer(serializers.ModelSerializer):
    """
    Lesson serializer for list views (less data).
    """
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content_type', 'duration_minutes', 'order', 'is_free')
        read_only_fields = ('id',)

# ============================================
# MODULE SERIALIZERS
# ============================================

class ModuleSerializer(serializers.ModelSerializer):
    """
    Module serializer with nested lessons.
    """
    lessons = LessonListSerializer(many=True, read_only=True)
    total_lessons = serializers.ReadOnlyField()

    class Meta:
        model = Module
        fields = ('id', 'title', 'description', 'order', 'total_lessons', 'lessons')
        read_only_fields = ('id',)

class ModuleListSerializer(serializers.ModelSerializer):
    """
    Module serializer for list  views (without lessons).
    """

    class Meta:
        model = Module
        fields = ('id', 'title', 'description', 'order', 'total_lessons')
        read_only_fields = ('id',)

# ============================================
# COURSE SERIALIZERS
# ============================================

class CourseListSerializer(serializers.ModelSerializer):
    """
    Course serializer for list views (lightweight).
    """

    instructor = UserPublicSerializer(read_only=True)
    total_modules = serializers.ReadOnlyField()
    total_lessons = serializers.ReadOnlyField()
    total_duration = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'instructor',
            'thumbnail', 'level', 'status', 'price',
            'total_modules', 'total_lessons', 'total_duration',
            'created_at'
        )
        read_only_fields = ('id', 'slug', 'created_at')

class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Course serializer for detail views (with nested modules and lessons)
    """

class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Course serializer for detail views (with nested modules and lessons).
    """
    instructor = UserPublicSerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    total_modules = serializers.ReadOnlyField()
    total_lessons = serializers.ReadOnlyField()
    total_duration = serializers.ReadOnlyField()
    total_enrollments = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'instructor',
            'thumbnail', 'level', 'status', 'price', 'modules',
            'total_modules', 'total_lessons', 'total_duration',
            'total_enrollments', 'is_enrolled', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def get_total_enrollments(self, obj):
        """Total number of students enrolled."""
        return obj.enrollments.filter(is_active=True).count()
    
    def get_is_enrolled(self, obj):
        """Check if the current user is enrolled in this course."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(
                student=request.user,
                is_active=True
            ).exists()
        return False

class CourseWriteSerializer(serializers.ModelSerializer):
    """
    Course serializer for create/update operations
    """

    class Meta:
        model = Course
        fields = (
            'title', 'slug', 'description', 'thumbnail',
            'level', 'status', 'price'
        )

    def validate_price(self, value):
        """Ensure price is not negative."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_title(self, value):
        """Ensure title is not too short."""
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        return value
    
    def create(self, validated_data):
        """Automatically assign instructor from request user."""
        request = self.context.get('request')
        validated_data['instructor'] = request.user

    # Auto-generate slug from title
        from django.utils.text import slugify
        validated_data['slug'] = slugify(validated_data['title'])
        
        return super().create(validated_data)
    
# ============================================
# ENROLLMENT SERIALIZERS
# ============================================

class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Enrollment serializer with course info.
    """
    course = CourseListSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()

    class Meta:
        model = Enrollment
        fields = (
            'id', 'course', 'enrolled_at', 'completed_at',
            'progress_percentage', 'is_completed', 'is_active'
        )
        read_only_fields = ('id', 'enrolled_at', 'completed_at', 'is_active')

# ============================================
# PROGRESS SERIALIZERS
# ============================================

class ProgressSerializer(serializers.ModelSerializer):
    """
    Progress serializer with lesson info.
    """
    lesson = LessonListSerializer(read_only=True)
    
    class Meta:
        model = Progress
        fields = ('id', 'lesson', 'completed', 'completed_at', 'last_accessed')
        read_only_fields = ('id', 'completed_at', 'last_accessed')