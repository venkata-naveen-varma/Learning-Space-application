from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),

    path('student/signup', views.student_signup, name='student_signup'),
    path('student/home', views.student_home, name='student_home'),
    path('student/list', views.student_list, name='student_list'),

    path('instructor/signup', views.instructor_signup, name='instructor_signup'),
    path('instructor/home', views.instructor_home, name='instructor_home'),
    path('instructor/list', views.instructor_list, name='instructor_list'),

    path('payment', views.payment, name='payment'),

    path('institution/signup', views.institution_signup, name='institution_signup'),
    path('institution/home', views.institution_home, name='institution_home'),

    path('course/create', views.create_course, name='create_course'),
    path('course/list', views.course_list, name='course_list'),
]
