from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        email = self.normalize_email(email) 

        return self.create_user(email, password, **extra_fields)
    
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    id_number = models.CharField(max_length=10, blank=False, unique=True, default=None)
    location = models.CharField(max_length=255, blank=True, null=True, default=None)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_of_birth = models.DateField(null=True, blank=True)
    agree = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    verification_link = models.CharField(max_length=255, blank=True)
    verification_link_created_at = models.DateTimeField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=12, blank=True, null=True, unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def save(self, *args, **kwargs):
        if self.phone_number and not self.phone_number.startswith('254'):
            self.phone_number = f'254{self.phone_number}'

        if not self.username:
            self.username = self.email

        super().save(*args, **kwargs)

        
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    objects = CustomUserManager()
    
    def full_name(self):
        parts = [part for part in [self.first_name, self.middle_name, self.last_name] if part]
        return ' '.join(parts)

    

    full_name.short_description = 'Name'
    full_name.allow_tags = True
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

