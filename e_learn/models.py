import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)
    is_institution = models.BooleanField(default=False)

class Institution(models.Model):
    name = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

class Subscription(models.Model):
    currency_choices = [
        ('CAD', 'CANADA'),
        ('USD', 'AMERICA')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    currency = models.CharField(choices=currency_choices, default='CAD', max_length=3)
    is_basic = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)

class UserInstitutionRelation(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Course(models.Model):
    name = models.CharField(max_length=60)
    # Institution that created the course
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)

class UserCourseRelation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    final_grade = models.IntegerField(blank=True)

class Notes(models.Model):
    name = models.TextField()
    content = models.TextField()
    notes_doc = models.FileField(upload_to="./notes")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_on = models.DateField(default=timezone.now)

class Assignment(models.Model):
    name = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    deadline = models.DateField()
    created_on = models.DateField(default=timezone.now)
    assignment_doc = models.FileField()

class AssignmentGrades(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    grade = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
