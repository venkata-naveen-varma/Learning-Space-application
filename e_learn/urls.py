from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.LoginUserView.as_view(), name='login'),
    path('logout', views.logout_user, name='logout'),

    path('student/signup', views.student_signup, name='student_signup'),
    path('student/home', views.student_home, name='student_home'),
    path('student/list', views.student_list, name='student_list'),
    path('student/course', views.student_course_details, name='student_course_details'),

    path('instructor/signup', views.instructor_signup, name='instructor_signup'),
    path('instructor/home', views.instructor_home, name='instructor_home'),
    path('instructor/list', views.instructor_list, name='instructor_list'),
    path('instructor/course', views.instructor_course_details, name='instructor_course_details'),

    path('payment', views.payment, name='payment'),

    path('institution/signup', views.institution_signup, name='institution_signup'),
    path('institution/home', views.institution_home, name='institution_home'),

    path('course/create', views.create_course, name='create_course'),
    path('course/list', views.course_list, name='course_list'),
    path('course/details-all', views.display_course_data, name='complete_course_details'),
    path('course/add-students', views.display_add_students_to_course, name='add_students_to_course'),
    path('course/add-insturctor', views.display_add_instructor_to_course, name='add_instructor_to_course'),
    path('course/remove', views.remove_course, name='remove_course'),
    path('course/remove-user', views.remove_user_from_course, name='remove_user_from_course'),

    path('download', views.download, name='download'),
    # path('test', views.test_password, name='test')
]
