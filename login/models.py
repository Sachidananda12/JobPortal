from django.db import models
from django.contrib.auth.models import User

JOB_TYPE_CHOICES = (
    ('full-time', 'Full-Time'),
    ('part-time', 'Part-Time'),
    ('internship', 'Internship'),
    ('remote', 'Remote'),
    ('contract', 'Contract'),
)

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    description = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

# models.py
class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    experience = models.CharField(max_length=255)
    resume = models.FileField(upload_to='resumes/')
    applied_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.job.title}"



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    job_profile = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username



class UserBlog(models.Model):

    def __str__(self):
        return self.user.userblog        
