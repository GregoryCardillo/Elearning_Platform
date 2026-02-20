from rest_framework import serializers
from .models import User, Course, Module, Lesson, Enrollment, Progress


# ============================================
# USER SERIALIZERS
# ============================================

class UserPublicSerializer(serializers.ModelSerializer):
    """
    Public user info (shown to other users).
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'bio', 'profile_picture')
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
# LESSON SERIALIZERS (BEFORE MODULE!)
# ============================================

class LessonListSerializer(serializers.ModelSerializer):
    """
    Lesson serializer for list views (less data).
    """
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content_type', 'duration_minutes', 'order', 'is_free')
        read_only_fields = ('id',)


class LessonSerializer(serializers.ModelSerializer):
    """
    Lesson serializer with full details.
    """
    
    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'content_type', 'content',
            'video_url', 'attachments', 'duration_minutes', 'order', 'is_free'
        )
        read_only_fields = ('id',)
    
    def validate_order(self, value):
        """Ensure order is not negative."""
        if value < 0:
            raise serializers.ValidationError("Order cannot be negative.")
        return value
    
    def validate_duration_minutes(self, value):
        """Ensure duration is not negative."""
        if value < 0:
            raise serializers.ValidationError("Duration cannot be negative.")
        return value
    
    def validate_title(self, value):
        """Ensure title is not too short."""
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value
    
    def validate(self, attrs):
        """
        Cross-field validation.
        - If content_type is 'video', video_url should be provided
        - If content_type is 'article', content should be provided
        """
        content_type = attrs.get('content_type')
        video_url = attrs.get('video_url')
        content = attrs.get('content')
        
        if content_type == 'video' and not video_url:
            raise serializers.ValidationError({
                'video_url': 'Video URL is required for video lessons.'
            })
        
        if content_type == 'article' and not content:
            raise serializers.ValidationError({
                'content': 'Content is required for article lessons.'
            })
        
        return attrs


# ============================================
# MODULE SERIALIZERS (AFTER LESSON!)
# ============================================

class ModuleListSerializer(serializers.ModelSerializer):
    """
    Module serializer for list views (without lessons).
    """
    total_lessons = serializers.ReadOnlyField()
    
    class Meta:
        model = Module
        fields = ('id', 'title', 'description', 'order', 'total_lessons')
        read_only_fields = ('id',)


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
    
    def validate_order(self, value):
        """Ensure order is not negative."""
        if value < 0:
            raise serializers.ValidationError("Order cannot be negative.")
        return value


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
    Course serializer for create/update operations.
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


# ============================================
# ENROLLMENT SERIALIZERS
# ============================================

class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Enrollment serializer with course info and progress details.
    """
    course = CourseListSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    next_lesson = serializers.SerializerMethodField()
    completed_lessons_count = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    total_time_spent = serializers.SerializerMethodField()
    estimated_completion_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = (
            'id', 'course', 'enrolled_at', 'completed_at',
            'progress_percentage', 'is_completed', 'is_active',
            'next_lesson', 'completed_lessons_count', 'total_lessons',
            'total_time_spent', 'estimated_completion_date'
        )
        read_only_fields = ('id', 'enrolled_at', 'completed_at', 'is_active')
    
    def get_next_lesson(self, obj):
        """Get the next incomplete lesson."""
        next_lesson = obj.get_next_lesson()
        if next_lesson:
            return {
                'id': next_lesson.id,
                'title': next_lesson.title,
                'module': next_lesson.module.title,
                'order': next_lesson.order
            }
        return None
    
    def get_completed_lessons_count(self, obj):
        """Get count of completed lessons."""
        return obj.get_completed_lessons_count()
    
    def get_total_lessons(self, obj):
        """Get total lessons in the course."""
        return obj.course.total_lessons
    
    def get_total_time_spent(self, obj):
        """Get total time spent in minutes."""
        return obj.get_total_time_spent()
    
    def get_estimated_completion_date(self, obj):
        """Get estimated completion date."""
        estimated_date = obj.calculate_estimated_completion_date()
        return estimated_date.isoformat() if estimated_date else None


class EnrollmentDetailSerializer(EnrollmentSerializer):
    """
    Detailed enrollment serializer with full course details.
    """
    course = CourseDetailSerializer(read_only=True)
    recent_progress = serializers.SerializerMethodField()
    
    class Meta(EnrollmentSerializer.Meta):
        fields = EnrollmentSerializer.Meta.fields + ('recent_progress',)
    
    def get_recent_progress(self, obj):
        """Get 5 most recently accessed lessons."""
        recent = obj.progress_records.select_related(
            'lesson__module'
        ).order_by('-last_accessed')[:5]
        
        return [{
            'lesson_id': p.lesson.id,
            'lesson_title': p.lesson.title,
            'module': p.lesson.module.title,
            'completed': p.completed,
            'last_accessed': p.last_accessed.isoformat() if p.last_accessed else None
        } for p in recent]


# ============================================
# AUTHENTICATION SERIALIZERS
# ============================================

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'role')
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs
    
    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value
    
    def validate_role(self, value):
        """Ensure role is valid."""
        if value not in ['student', 'instructor']:
            raise serializers.ValidationError('Role must be either student or instructor.')
        return value
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')  # Remove confirm password
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)  # Hash password
        user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate credentials."""
        from django.contrib.auth import authenticate
        
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password".')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, min_length=8, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, write_only=True, min_length=8, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """Validate new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs
    
    def validate_old_password(self, value):
        """Check if old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value