"""
Custom User model extending Django AbstractUser.
Adds role-based access: ADMIN vs SUPER_ADMIN.
The Super Admin uses /django-admin/; Admins use /portal/.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        SUPER_ADMIN = 'super_admin', _('Super Admin')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        verbose_name=_('Role'),
    )
    email = models.EmailField(unique=True, verbose_name=_('Email Address'))

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_portal_admin(self):
        """True for both Admin and Super Admin — allows portal access."""
        return self.is_active and (self.role in [self.Role.ADMIN, self.Role.SUPER_ADMIN] or self.is_staff)
