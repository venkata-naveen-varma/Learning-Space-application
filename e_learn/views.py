from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Institution, Course, UserCourseRelation, Assignment, AssignmentGrades, UserInstitutionRelation, Subscription

def home(request):
    """ Dashboard of the application """
    return render(request, 'home.html')

def signup_func(request, user_type):
    """function to perform registration operation for a new user"""
    if request.method == 'POST':
        if user_type == "institution":
            new_name = request.session["institution_details"]["name"]
            new_email = request.session["institution_details"]["email"]
            new_password1 = request.session["institution_details"]["password"]
            new_password2 = new_password1
            amount = request.session["institution_details"]["amount"]
            currency = request.session["institution_details"]["currency"]
            del request.session["institution_details"]
        else:
            new_first_name = request.POST.get('first_name')
            new_last_name = request.POST.get('last_name')
            new_password1 = request.POST.get('password1')
            new_password2 = request.POST.get('password2')
            new_email = request.POST.get('email')
        try:
            username_exists = User.objects.get(username=new_email)
        except Exception as e:
            username_exists = None

        if username_exists is not None:
            msg = {'msg': "Username/Email already exists!"}
            if user_type == "institution":
                return render(request, 'institution_signup.html', msg)
            elif user_type == "student":
                return render(request, 'student_signup.html', msg)
            else:
                return render(request, 'instructor_signup.html', msg)

        if new_password1 != new_password2:
            msg = {'msg': "Passwords do not match!"}
            if user_type == "institution":
                return render(request, 'institution_signup.html', msg)
            elif user_type == "student":
                return render(request, 'student_signup.html', msg)
            else:
                return render(request, 'instructor_signup.html', msg)
        else:
            if user_type == "institution":
                new_user = User(first_name=new_name, username=new_email, email=new_email, password=new_password1, is_institution=True)
                new_user.save()
                new_institution = Institution(name=new_name, user=new_user)
                new_institution.save()
                new_subscription = Subscription(user=new_user, amount_paid=amount, currency=currency, is_basic=True)
                new_subscription.save()
                return render(request, 'login.html')
            elif user_type == "student":
                new_user = User(first_name=new_first_name, last_name=new_last_name, email=new_email, password=new_password1, is_student=True, username=new_email)
                new_user.save()
                institution_obj = Institution.objects.get(user=request.user)
                new_relation = UserInstitutionRelation(institution=institution_obj, user=new_user, is_student=True)
                new_relation.save()
                return render(request, 'institution_home.html', {'msg': "Student Registered Successfully!"})
            else:
                new_user = User(first_name=new_first_name, last_name=new_last_name, email=new_email, password=new_password1, is_instructor=True, username=new_email)
                new_user.save()
                institution_obj = Institution.objects.get(user=request.user)
                new_relation = UserInstitutionRelation(institution=institution_obj, user=new_user, is_instructor=True)
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

def payment(request):
    """ Validate institution details and Payment gateway page, path='payment' """
    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_email = request.POST.get('email')
        new_password1 = request.POST.get('password1')
        new_password2 = request.POST.get('password2')
        currency = request.POST.get('currency')
        try:
            username_found = User.objects.get(username=new_email)
        except Exception as e:
            username_found = None
        if username_found is None:
            if new_password1 == new_password2:
                plan = request.POST.get('plan')
                if plan == "basic":
                    amount_to_be_paid = 2000
                else:
                    amount_to_be_paid = 3500
                if currency == 'USD':
                    amount_to_be_paid = amount_to_be_paid*0.74
                institution_details = {"name": new_name, "email": new_email, "password": new_password1, "amount": amount_to_be_paid, "plan": plan, "currency": currency}
                request.session["institution_details"] = institution_details
                return render(request, 'payment.html', institution_details)
            else:
                return render(request, 'institution_signup.html', {'msg': "Passwords do not match!!!"})
        else:
            return render(request, 'institution_signup.html', {'msg': "Institution name already exists! Try a different name!"})
    return render(request, 'institution_signup.html')

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

@login_required(login_url='institution_login')
def create_course(request):
    """ Add a new Course. Operation is to be done only by an institution, path='course/create' """
    if request.method == 'POST':
        course_name = request.POST.get('name')
        course_description = request.POST.get('course_description')
        try:
            course_found = Course.objects.get(name=course_name)
        except Exception as e:
            course_found = None
        current_institution = Institution.objects.get(user=request.user)
        if course_found is None:
            new_course = Course(name=course_name, description=course_description, institution=current_institution)
            new_course.save()
            return render(request, 'institution_home.html', {'msg': "Course created successfully!"})
        else:
            return render(request, 'create_course.html', {'msg': "Course name already exists! Try a different name!"})
    else:
        return render(request, 'create_course.html')

@login_required(login_url='institution_login')
def course_list(request):
    """ Listing all courses of an Institution, path='course/list """
    try:
        current_institution = Institution.objects.get(user=request.user)
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Institution details not found!'})
    try:
        course_lst = Course.objects.filter(institution=current_institution)
        return render(request, 'course_list.html', {'course_list': course_lst, 'course_exist': True})
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Course not created yet, try creating a new course!'})

@login_required(login_url='institution_login')
def student_list(request):
    """ Listing all students of an Institution, path='student/list """
    try:
        current_institution = Institution.objects.get(user=request.user)
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Institution details not found!'})
    try:
        details_lst = UserInstitutionRelation.objects.filter(institution=current_institution, is_student=True)
        student_lst = []
        for i in details_lst:
            student_lst.append(i.user)
        return render(request, 'institution_users_list.html', {'user_list': student_lst, 'student_exist': True})
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Students not registered yet, try registering a new student!'})

@login_required(login_url='institution_login')
def instructor_list(request):
    """ Listing all instructors of an Institution, path='instructor/list """
    try:
        current_institution = Institution.objects.get(user=request.user)
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Institution details not found!'})
    try:
        details_lst = UserInstitutionRelation.objects.filter(institution=current_institution, is_instructor=True)
        instructor_lst = []
        for i in details_lst:
            instructor_lst.append(i.user)
        return render(request, 'institution_users_list.html', {'user_list': instructor_lst, 'instructor_exist': True})
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Students not registered yet, try registering a new student!'})

# def add_student_to_course(request):
#     """ Add a student to a course, path='institution/course_student'"""
#     return render(request, '.html', {'user_lst': User.objects.all()})
