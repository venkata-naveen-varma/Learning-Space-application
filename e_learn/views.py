from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Institution, Course, UserCourseRelation, Assignment, AssignmentGrades, UserInstitutionRelation

def home(request):
    """ Dashboard of the application """
    return render(request, 'home.html')

def signup_func(request, user_type):
    """function to perform registration operation for a new user"""
    if request.method == 'POST':
        if user_type == "institution":
            new_name = request.POST.get('name')
        else:
            new_first_name = request.POST.get('first_name')
            new_last_name = request.POST.get('last_name')
        new_email = request.POST.get('email')
        new_password1 = request.POST.get('password1')
        new_password2 = request.POST.get('password2')

        if new_password1 != new_password2:
            if user_type == "institution":
                return render(request, 'institution_signup.html', {'msg': "Passwords do not match!!!"})
            elif user_type == "student":
                return render(request, 'student_signup.html', {'msg': "Passwords do not match!!!"})
            else:
                return render(request, 'instructor_signup.html', {'msg': "Passwords do not match!!!"})
        else:
            if user_type == "institution":
                new_user = User(first_name=new_name, username=new_email, email=new_email, password=new_password1, is_institution=True)
                new_user.save()
                new_institution = Institution(name=new_name, user=new_user)
                new_institution.save()
                return render(request, 'login.html')
            elif user_type == "student":
                new_user = User(first_name=new_first_name, last_name=new_last_name, email=new_email, password=new_password1, is_student=True, username=new_email)
                new_user.save()
                institution_obj = Institution.objects.get(user=request.user)
                new_relation = UserInstitutionRelation(institution=institution_obj, user=new_user)
                new_relation.save()
                return render(request, 'institution_home.html', {'msg': "Student Registered Successfully!"})
            else:
                new_user = User(first_name=new_first_name, last_name=new_last_name, email=new_email, password=new_password1, is_instructor=True, username=new_email)
                new_user.save()
                institution_obj = Institution.objects.get(user=request.user)
                new_relation = UserInstitutionRelation(institution=institution_obj, user=new_user)
                new_relation.save()
                return render(request, 'institution_home.html', {'msg': "Instructor Registered Successfully!"})
    else:
        if user_type == "institution":
            return render(request, 'institution_signup.html')
        elif user_type == "student":
            return render(request, 'student_signup.html')
        else:
            return render(request, 'instructor_signup.html')

def student_signup(request):
    """ Create a new Student, path='student/signup' """
    return signup_func(request, "student")

def instructor_signup(request):
    """ Create a new Instructor, path='instructor/signup' """
    return signup_func(request, "instructor")

def institution_signup(request):
    """ Create a new Institution, path='institution/signup' """
    return signup_func(request, "institution")

def login_user(request):
    """ Login for both Students and Instructors, path='login' """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except Exception as e:
            return render(request, 'login.html', {'msg': "Username or Password is incorrect!!!"})
        if user is not None:
            user_password = user.password
            if password == user_password:
                login(request, user)
                if user.is_institution:
                    return redirect('institution_home')
                elif user.is_student:
                    return redirect('student_home')
                else:
                    return redirect('instructor_home')
            else:
                return render(request, 'login.html', {'msg': "Username or Password is incorrect!!!"})
        else:
            return render(request, 'login.html', {'msg': "Username or Password is incorrect!!!"})
    else:
        return render(request, 'login.html')

@login_required(login_url='logout')
def logout_user(request):
    """ logout users, path='logout' """
    logout(request)
    return redirect('login')

@login_required(login_url='institution_login')
def institution_home(request):
    """ Institution's Home Page, path=institution/home """
    return render(request, 'institution_home.html')

@login_required(login_url='login')
def student_home(request):
    """ Student's Home Page, path='student/home' """
    return render(request, 'student_home.html')

@login_required(login_url='login')
def instructor_home(request):
    """ Instructor's Home Page, path=instructor/home """
    return render(request, 'instructor_home.html')

def view_users(request):
    """Shows all the users details in the Users model, path='users/view'"""
    return render(request, 'view_users.html', {'user_lst': User.objects.all()})
