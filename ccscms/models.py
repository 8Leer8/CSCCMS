from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils import timezone
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator, MaxValueValidator
import os

def upload_to(instance, filename):
    """Generate upload path for files"""
    model_name = instance.__class__.__name__.lower()
    return os.path.join(model_name, filename)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(default=True)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

    class Meta:
        abstract = True

class AccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('account_type', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class Account(AbstractUser):
    username = None
    email = models.EmailField('email address', unique=True)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, null=True, blank=True)
    contact_number = models.CharField(
        max_length=20, null=True, blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    profile_img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    password = models.CharField(max_length=255)
    ACCOUNT_TYPES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True, default=None)
    is_online = models.BooleanField(default=False)
    login_time = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    
    objects = AccountManager()
    
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="account_groups",
        related_query_name="account",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="account_permissions",
        related_query_name="account",
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstname', 'lastname', 'contact_number', 'account_type']

    class Meta:
        db_table = 'account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['lastname', 'firstname']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_online']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.email})"

class Status(SoftDeleteModel):
    STATUS_TYPES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    type = models.CharField(max_length=50, choices=STATUS_TYPES)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'status'
        verbose_name_plural = 'statuses'
        ordering = ['type']
class Scope(models.Model):
    type = models.CharField(
        max_length=50,
        unique=True,
        null=True,
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scope'
        ordering = ['type']

    def __str__(self):
        return self.type
class Category(SoftDeleteModel):
    CATEGORY_TYPES = (
        ('research', 'Research'),
        ('academics', 'Academics'),
        ('achievements', 'Achievements'),
        ('special', 'Special'),
        ('theaters', 'Theaters'),
        ('parties', 'Parties'),
        ('drinks', 'Drinks'),
        ('food', 'Food'),
    )
    scope = models.ForeignKey(
        Scope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='scope_id'  # Explicit column name
    )
    category = models.CharField(max_length=50, choices=CATEGORY_TYPES)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'category'
        verbose_name_plural = 'categories'
        ordering = ['category']

class Audience(SoftDeleteModel):
    AUDIENCE_TYPES = (
        ('general', 'General'),
        ('students', 'Students'),
        ('teachers', 'Teachers'),
        ('faculties', 'Faculties'),
    )
    type = models.CharField(max_length=50, choices=AUDIENCE_TYPES)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'audience'
        ordering = ['type']

class College(SoftDeleteModel):
    name = models.CharField(max_length=100)
    college_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(regex='^[A-Z]{2,10}$', message='College code must be uppercase letters')]
    )
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'college'
        ordering = ['name']

class Department(SoftDeleteModel):
    name = models.CharField(max_length=100)
    depart_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(regex='^[A-Z]{2,10}$', message='Department code must be uppercase letters')]
    )
    description = models.TextField(null=True, blank=True)
    college = models.ForeignKey(College, on_delete=models.PROTECT, related_name='departments')
    
    class Meta:
        db_table = 'department'
        ordering = ['college', 'name']

class PositionType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Position(SoftDeleteModel):
    name = models.CharField(max_length=100)
    position_type = models.ForeignKey(PositionType, on_delete=models.CASCADE, null=True, blank=True)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'position'
        ordering = ['name']

class Officer(SoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('present', 'Present'), ('past', 'Past')],
        default='present'
    )
    supervisor = models.CharField(max_length=100, null=True, blank=True)
    supervisor_img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    start_in_sy = models.CharField(max_length=20)
    end_in_sy = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'officer'
        ordering = ['status', 'name']
        indexes = [
            models.Index(fields=['status']),
        ]

class OfficerMember(SoftDeleteModel):
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name='members')
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, null=True, blank=True)
    profile_img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    start_term = models.DateField()
    end_term = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'officer_member'
        ordering = ['officer', 'position', 'lastname']
        indexes = [
            models.Index(fields=['officer']),
            models.Index(fields=['position']),
            models.Index(fields=['department']),
            models.Index(fields=['lastname', 'firstname']),
        ]

class Committee(SoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'committee'
        ordering = ['name']
        verbose_name_plural = 'committees'

class CommitteeMember(SoftDeleteModel):
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='members')
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    joined_at = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'committee_member'
        ordering = ['committee', 'role', 'lastname']
        indexes = [
            models.Index(fields=['committee']),
            models.Index(fields=['email']),
        ]

class Faculty(SoftDeleteModel):
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    college = models.ForeignKey(College, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    designation = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    faculty_img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    office_location = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faculty'
        ordering = ['lastname', 'firstname']
        verbose_name_plural = 'faculty'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['college', 'department']),
            models.Index(fields=['lastname', 'firstname']),
        ]

class User(SoftDeleteModel):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    username = models.CharField(max_length=50, unique=True)
    student_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        validators=[RegexValidator(regex='^[0-9-]{8,20}$', message='Student number must be numeric with optional dashes')]
    )
    COR_img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    
    class Meta:
        db_table = 'user'
        ordering = ['account__lastname', 'account__firstname']

class Admin(SoftDeleteModel):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, primary_key=True, db_column='admin_id')
    adminname = models.CharField(max_length=50, unique=True)
    admin_type = models.CharField(
        max_length=10,
        choices=[('head-admin', 'Head Admin'), ('admin', 'Admin')]
    )
    
    class Meta:
        db_table = 'admin'
        ordering = ['admin_type', 'account__lastname']

class ComplaintType(SoftDeleteModel):
    type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'complaint_type'
        ordering = ['type']

class Complaint(SoftDeleteModel):
    complaint_type = models.ForeignKey(ComplaintType, on_delete=models.PROTECT)
    description = models.TextField()
    complain_img = models.ImageField(upload_to=upload_to, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    remarks = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('solved', 'Solved')],
        default='pending'
    )
    remark_info = models.TextField(null=True, blank=True)
    admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'complaint'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['complaint_type']),
            models.Index(fields=['remarks']),
            models.Index(fields=['created_at']),
        ]

class Announcement(SoftDeleteModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    context = models.TextField()
    content = models.TextField()
    admin = models.ForeignKey(Admin, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=[('expired', 'Expired'), ('active', 'Active'), ('scheduled', 'Scheduled')],
        default='active'
    )
    start_publish_on = models.DateField()
    end_publish_on = models.DateField()
    landmark = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    date_post = models.DateField(null=True, blank=True)
    time_post = models.TimeField(null=True, blank=True)
    image = models.ImageField(upload_to='announcements/', null=True, blank=True)
    
    audiences = models.ManyToManyField(Audience, through='AnnouncementAudience')
    
    class Meta:
        db_table = 'announcement'
        ordering = ['-start_publish_on']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['start_publish_on', 'end_publish_on']),
        ]

class AnnouncementAudience(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, db_column='announcement_id')
    audience = models.ForeignKey(Audience, on_delete=models.CASCADE, db_column='audience_id')
    
    class Meta:
        db_table = 'announcement_audience_list'
        unique_together = ('announcement', 'audience')

class Post(SoftDeleteModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    context = models.TextField()
    content = models.TextField()
    admin = models.ForeignKey(Admin, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=[('expired', 'Expired'), ('active', 'Active'), ('scheduled', 'Scheduled')],
        default='active'
    )
    start_publish_on = models.DateField()
    end_publish_on = models.DateField()
    
    class Meta:
        db_table = 'post'
        ordering = ['-start_publish_on']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['start_publish_on', 'end_publish_on']),
        ]

class PostImage(SoftDeleteModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=upload_to)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'post_image'
        ordering = ['post', '-created_at']

class GalleryPost(SoftDeleteModel):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    admin = models.ForeignKey(Admin, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'gallery_post'
        ordering = ['-created_at']

class GalleryPostImage(SoftDeleteModel):
    gallery_post = models.ForeignKey(GalleryPost, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=upload_to)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'gallery_post_image'
        ordering = ['gallery_post', '-created_at']

class EventLabel(SoftDeleteModel):
    type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'event_label'
        ordering = ['type']

class EventType(SoftDeleteModel):
    type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'event_type'
        ordering = ['type']

class Event(SoftDeleteModel):
    name = models.CharField(max_length=100)
    context = models.TextField()
    description = models.TextField()
    event_img = models.ImageField(upload_to=upload_to, db_column='event_img', null=True, blank=True)
    landmark = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=255)
    start_at = models.TimeField()
    end_at = models.TimeField()
    date_event = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=[('expired', 'Expired'), ('active', 'Active'), ('scheduled', 'Scheduled')],
        default='active'
    )
    start_publish_on = models.DateField()
    end_publish_on = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    admin = models.ForeignKey(Admin, on_delete=models.PROTECT, db_column='admin_id')
    
    audiences = models.ManyToManyField(Audience, through='EventAudience')
    labels = models.ManyToManyField(EventLabel, through='EventLabelList')
    types = models.ManyToManyField(EventType, through='EventTypeList')
    
    class Meta:
        db_table = 'event'
        ordering = ['-date_event', '-start_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['date_event']),
            models.Index(fields=['start_publish_on', 'end_publish_on']),
        ]

class EventAudience(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='event_id')
    audience = models.ForeignKey(Audience, on_delete=models.CASCADE, db_column='audience_id')
    
    class Meta:
        db_table = 'event_audience_list'
        unique_together = ('event', 'audience')

class EventLabelList(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='event_id')
    event_label = models.ForeignKey(EventLabel, on_delete=models.CASCADE, db_column='event_label_id')
    
    class Meta:
        db_table = 'event_label_list'
        unique_together = ('event', 'event_label')

class EventTypeList(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='event_id')
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, db_column='event_type_id')
    
    class Meta:
        db_table = 'event_type_list'
        unique_together = ('event', 'event_type')

class Accomplishment(SoftDeleteModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    context = models.TextField()
    content = models.TextField()
    accomplish_on = models.DateField()
    impact = models.TextField(null=True, blank=True)
    recognition = models.TextField(null=True, blank=True)
    admin = models.ForeignKey(Admin, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accomplishment'
        ordering = ['-accomplish_on']
        indexes = [
            models.Index(fields=['category']),
        ]

class AccomplishmentImage(SoftDeleteModel):
    accomplishment = models.ForeignKey(Accomplishment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=upload_to)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accomplishment_image'
        ordering = ['accomplishment', '-created_at']

class Achievement(SoftDeleteModel):
    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    heading = models.CharField(max_length=255, blank=True, null=True)
    context = models.TextField(blank=True, null=True)  # Short summary or paragraph
    content = models.TextField(blank=True, null=True)  # Optional full details

    # Optional fields for flexibility
    team_name = models.CharField(max_length=255, blank=True, null=True)
    person_in_charge = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # Support full date range OR just a year
    awarded_on = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    awarded_by = models.CharField(max_length=100, blank=True, null=True)
    admin = models.ForeignKey('Admin', on_delete=models.PROTECT)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'achievement'
        ordering = ['-awarded_on']
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

class AchievementImage(SoftDeleteModel):
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=upload_to)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'achievement_image'
        ordering = ['achievement', '-created_at']

class Transparency(SoftDeleteModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    context = models.TextField()
    description = models.TextField()
    date = models.DateField()
    document = models.FileField(upload_to='transparency_docs/', null=True, blank=True)
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    admin = models.ForeignKey(Admin, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transparency'
        ordering = ['-date']
        verbose_name_plural = 'transparency documents'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]

class Volunteer(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'volunteer'
        ordering = ['user__account__lastname', 'user__account__firstname']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]

class VolunteerAnnouncement(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, db_column='volunteer_id')
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, db_column='announcement_id')
    
    class Meta:
        db_table = 'volunteer_announcement_list'
        unique_together = ('volunteer', 'announcement')

class VolunteerEvent(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, db_column='volunteer_id')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='event_id')
    
    class Meta:
        db_table = 'volunteer_event_list'
        unique_together = ('volunteer', 'event')
class FeedbackType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback_type = models.ForeignKey(FeedbackType, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'feedback'
        ordering = ['-created_at']

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'visitor_log'
        ordering = ['-last_active']

class PasswordReset(models.Model):
    email = models.EmailField()
    reset_token = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'password_reset'
        ordering = ['-created_at']

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    )
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    record_id = models.IntegerField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
            models.Index(fields=['created_at']),
        ]