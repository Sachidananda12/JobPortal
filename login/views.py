from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Job, JobApplication,UserProfile
from django.core.mail import send_mail
from django.core.mail import EmailMessage, BadHeaderError
from smtplib import SMTPException
import logging

# Home Page
def home(request):
    return render(request, 'home.html')

# Sign Up View
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        full_name = request.POST['full_name']
        email = request.POST['email']
        phone = request.POST['phone']
        gender = request.POST['gender']
        job_profile = request.POST.get('job_profile', '')  # or 'job_profile_name' if not changed
        image = request.FILES.get('image')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')

        user = User.objects.create_user(username=username, password=password, email=email)
        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            gender=gender,
            image=image,
            job_profile=job_profile
        )

        messages.success(request, "Signup successful. Please login.")
        return redirect('login')

    return render(request, 'signup.html')


# Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.username == 'admin':
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

# User Dashboard
from .models import Job, UserProfile
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q

@login_required
def dashboard(request):
    query = request.GET.get('q')
    if query:
        jobs = Job.objects.filter(
            Q(title__icontains=query) | Q(company__icontains=query)
        ).order_by('-created_at')
    else:
        jobs = Job.objects.all().order_by('-created_at')
    
    # Fetch user profile
    profile = None
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    # ✅ Calculate profile completion percentage
    percent = 0
    stroke_offset = 377  # circle circumference

    if profile:
        total_fields = 5  # full_name, phone, gender, job_profile, image
        filled_fields = sum([
            bool(profile.full_name),
            bool(profile.phone),
            bool(profile.gender),
            bool(profile.job_profile),
            bool(profile.image)
        ])
        percent = int((filled_fields / total_fields) * 100)
        stroke_offset = 377 - (377 * percent / 100)

    context = {
        'jobs': jobs,
        'query': query,
        'profile': profile,
        'percent': percent,
        'stroke_offset': stroke_offset
    }
    return render(request, 'dashboard.html', context)
    
# Admin Dashboard
@login_required
def admin_dashboard(request):
    if request.user.username != 'admin':
        return redirect('dashboard')  # Redirect to user dashboard if not admin

    if request.method == 'POST':
        # Collect job posting data from form
        title = request.POST['title']
        company = request.POST['company']
        location = request.POST['location']
        job_type = request.POST['job_type']
        description = request.POST['description']

        Job.objects.create(
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            description=description,
            posted_by=request.user
        )
        messages.success(request, '✅ Job posted successfully!')
        return redirect('admin_dashboard')

    # Stats for dashboard cards
    jobs = Job.objects.all().order_by('-created_at')
    total_applications = JobApplication.objects.count()
    approved_count = JobApplication.objects.filter(approved=True).count()
    pending_count = JobApplication.objects.filter(approved=False).count()

    context = {
        'jobs': jobs,
        'total_applications': total_applications,
        'approved_count': approved_count,
        'pending_count': pending_count,
    }

    return render(request, 'admin_dashboard.html', context)# Apply Job View


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Try to prefill from user profile
    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == 'POST':
        name = request.POST.get('name') or request.user.get_full_name()
        experience = request.POST.get('experience')
        resume = request.FILES.get('resume')

        # Validate file upload
        if not resume:
            messages.error(request, '⚠️ Please upload your resume before submitting.')
            return redirect('apply_job', job_id=job.id)

        JobApplication.objects.create(
            job=job,
            applicant=request.user,
            name=name,
            experience=experience,
            resume=resume
        )
        messages.success(request, '✅ Application submitted successfully!')
        return redirect('dashboard')

    return render(request, 'apply_job.html', {
        'job': job,
        'profile': profile,
    })





@login_required
def view_applications(request):
    if request.user.username != 'admin':
        return redirect('dashboard')

    applications = JobApplication.objects.select_related('job', 'applicant').order_by('-applied_at')
    return render(request, 'view_applications.html', {'applications': applications})



    





@login_required
def approve_application(request, app_id):
    application = get_object_or_404(JobApplication, id=app_id)

    if application.approved:
        messages.info(request, 'This application has already been approved.')
        return redirect('view_applications')

    if request.method == 'POST':
        company_email = request.POST.get('company_email')
        try:
            # ✅ 1. Send email to the company
            email_to_company = EmailMessage(
                subject=f"Recommended Applicant: {application.name} for {application.job.title}",
                body=(
                    f"Dear Hiring Team,\n\n"
                    f"We are pleased to recommend the following candidate for your open position:\n\n"
                    f"Job Title: {application.job.title}\n"
                    f"Company: {application.job.company}\n"
                    f"Candidate Name: {application.name}\n\n"
                    f"The applicant has met the initial criteria and appears to be a suitable fit for your organization.\n\n"
                    f"Please find their resume attached for your consideration.\n\n"
                    f"Best regards,\n"
                    f"YourJob Admin Team\n"
                    f"yourjob@example.com"
                ),
                from_email='sachidanandasahoo16@gmail.com',
                to=[company_email],
            )
            email_to_company.attach_file(application.resume.path)
            email_to_company.send(fail_silently=False)

            # ✅ 2. Send email to the applicant
            email_to_user = EmailMessage(
                subject=f"Your Application for {application.job.title} Has Been Approved",
                body=(
                    f"Dear {application.name},\n\n"
                    f"Congratulations!\n\n"
                    f"We’re pleased to inform you that your application for the position of "
                    f"'{application.job.title}' at {application.job.company} has been approved by our team.\n\n"
                    f"Your profile has been forwarded to the company for further consideration. "
                    f"Best of luck with the next steps!\n\n"
                    f"Warm regards,\n"
                    f"The YourJob Team\n"
                    f"yourjob@example.com"
                ),
                from_email='sachidanandasahoo16@gmail.com',
                to=[application.applicant.email],
            )
            email_to_user.send(fail_silently=False)

            # ✅ Mark the application as approved
            application.approved = True
            application.save()

            messages.success(request, '✅ Application approved and emails sent successfully.')

        except BadHeaderError:
            messages.error(request, "❌ Invalid header found.")
        except SMTPException as e:
            messages.error(request, f"❌ SMTP error: {str(e)}")
        except Exception as e:
            messages.error(request, f"❌ Unexpected error: {str(e)}")

        return redirect('view_applications')

    return redirect('view_applications')

# Logout View
def logout_view(request):
    logout(request)
    return redirect('home')
