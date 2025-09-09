from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('applications/', views.view_applications, name='view_applications'),
    # path('approve/<int:application_id>/', views.approve_application, name='approve_application'),
    path('approve/<int:app_id>/', views.approve_application, name='approve_application'),
]
