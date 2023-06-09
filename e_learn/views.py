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
                return render(request, 'login.html', {'msg': "Registered Successfully!"})
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

def user_courses(request):
    """ function to get all courses of a user """
    try:
        relation_lst = UserCourseRelation.objects.filter(user=request.user)
        courses_lst = []
        for c in relation_lst:
            courses_lst.append(c.course)
        return courses_lst
    except Exception as e:
        return None

@login_required(login_url='login')
def student_home(request):
    """ Student's Home Page, path='student/home' """
    courses_lst = user_courses(request)
    if courses_lst is None or len(courses_lst) == 0:
        return render(request, 'student_home.html', {'msg': "You don't have any courses to display."})
    return render(request, 'student_home.html', {'course_list': courses_lst, 'course_exist': True})

@login_required(login_url='login')
def instructor_home(request):
    """ Instructor's Home Page, path=instructor/home """
    courses_lst = user_courses(request)
    if courses_lst is None or len(courses_lst) == 0:
        return render(request, 'instructor_home.html', {'msg': "You don't have any courses to display."})
    return render(request, 'instructor_home.html', {'course_list': courses_lst, 'course_exist': True})

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
        if len(course_lst) == 0:
            return render(request, 'institution_home.html', {'msg': 'Course not created yet, try creating a new course!'})
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
        if len(student_lst) == 0:
            return render(request, 'institution_home.html', {'msg': 'Students not registered yet, try registering a new student!'})
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
        if len(instructor_lst) == 0:
            return render(request, 'institution_home.html', {'msg': 'Instructors not registered yet, try registering a new Instructor!'})
        return render(request, 'institution_users_list.html', {'user_list': instructor_lst, 'instructor_exist': True})
    except Exception as e:
        return render(request, 'institution_home.html', {'msg': 'Instructors not registered yet, try registering a new Instructor!'})

def course_users(course_id):
    """ function to get all students, instructors of a course from course-id """
    try:
        course = Course.objects.get(id=course_id)
        lst_user_relations = UserCourseRelation.objects.filter(course=course)
        students_lst = []
        instructor = None
        for relation in lst_user_relations:
            if relation.user.is_instructor:
                instructor = relation.user
            else:
                students_lst.append(relation.user)
        if len(students_lst) == 0 and instructor is None:
            return None
        return {"course": course, "students_lst": students_lst, "instructor": instructor}
    except Exception as e:
        return None

@login_required(login_url="institution_login")
def display_course_data(request):
    """ Getting all users of a course and course details to display to institution, path='course/details-all' """
    course_id = request.GET.get('course_id')
    send_data = {}
    try:
        if course_id is None:
            course_id = request.session["course_id"]
            del request.session["course_id"]
    except Exception as e:
        return redirect('logout')
    data = course_users(course_id)
    students_exists = True
    instructor_exists = True
    if data is None:
        course = Course.objects.get(id=course_id)
        return render(request, "course_data_to_institution.html", {'course_details': course, 'msg': "No Student or Instructor is assigned to this course yet."})
    if data["instructor"] is None:
        instructor_exists = False
    if len(data["students_lst"]) == 0:
        students_exists = False
    send_data = {'course_details': data["course"], 'students_lst': data["students_lst"], 'instructor': data["instructor"], 'instructor_exists': instructor_exists, 'students_exists': students_exists}
    return render(request, "course_data_to_institution.html", send_data)

def institution_users(request, user_type):
    """ function to get a list of all students or instructors in an institution """
    current_institution = Institution.objects.get(user=request.user)
    users_exist = False
    users_lst = []
    try:
        if user_type == "student":
            details_lst = UserInstitutionRelation.objects.filter(institution=current_institution, is_student=True)
        else:
            details_lst = UserInstitutionRelation.objects.filter(institution=current_institution, is_instructor=True)
        for i in details_lst:
            users_lst.append(i.user)
        if len(users_lst) != 0:
            users_exist = True
        return {"users_exist": users_exist, "users_lst": users_lst}
    except Exception as e:
        return {"users_exist": users_exist, "users_lst": users_lst}


@login_required(login_url="institution_login")
def display_add_students_to_course(request):
    """ Get a list of all students in the institution and add student to a course, path='course/add-students '"""
    msg = None
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        user_id = request.POST.get('user_id')
        course_details = Course.objects.get(id=int(course_id))
        user_details = User.objects.get(id=user_id)
        new_relation = UserCourseRelation(user=user_details, course=course_details, is_student=True)
        new_relation.save()
        msg = "Student added to course successfully."
    else:
        course_id = request.GET.get('course_id')
        course_details = Course.objects.get(id=course_id)

    data = institution_users(request, "student")
    if not data["users_exist"]:
        return render(request, 'student_signup.html', {"msg": 'Students not registered in the institution yet, try registering a new student!'})
    relations = UserCourseRelation.objects.filter(course=course_details)
    students_lst = []
    relations_user = []
    for relation in relations:
        relations_user.append(relation.user)
    for user in data["users_lst"]:
        if user not in relations_user:
            students_lst.append(user)
    if len(relations) != 0 and len(students_lst) == 0:
        return render(request, 'add_students_to_course.html', {'course_details': course_details, 'msg': "No new students to add to this course."})
    if len(relations) == 0:
        students_lst = data["users_lst"]
    if msg is not None:
        return render(request, 'add_students_to_course.html', {"course_details": course_details, "students_lst": students_lst, "student_exists": data["users_exist"], "msg": msg})
    return render(request, 'add_students_to_course.html', {"course_details": course_details, "students_lst": students_lst, "student_exists": data["users_exist"]})

@login_required(login_url="institution_login")
def display_add_instructor_to_course(request):
    """ display instructor of a course, path='course/add-instructor'. One Course has only one instructor"""
    msg = None
    # add or update user
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        user_id = request.POST.get('user_id')
        course_details = Course.objects.get(id=int(course_id))
        user_details = User.objects.get(id=user_id)
        try:
            course_relation = UserCourseRelation.objects.get(course=course_details, is_instructor=True)
        except Exception as e:
            course_relation = None
        if course_relation is None:
            # insert user
            new_relation = UserCourseRelation(user=user_details, course=course_details, is_instructor=True)
            new_relation.save()
        else:
            # update user
            course_relation.user = user_details
            course_relation.save()
        request.session["course_id"] = course_id
        return redirect("complete_course_details")

    course_id = request.GET.get('course_id')
    course_details = Course.objects.get(id=course_id)

    data = institution_users(request, "instructor")
    if not data["users_exist"]:
        return render(request, 'instructor_signup.html', {"msg": 'Instructors not registered in the institution yet, try registering a new instructor!'})
    relations = UserCourseRelation.objects.filter(course=course_details)
    instructors_lst = []
    relations_user = []
    for relation in relations:
        relations_user.append(relation.user)
    for user in data["users_lst"]:
        if user not in relations_user:
            instructors_lst.append(user)
    if len(relations) != 0 and len(instructors_lst) == 0:
        return render(request, 'add_instructor_to_course.html', {'course_details': course_details, 'msg': "No new instructors to add to this course."})
    elif len(relations) == 0:
        instructors_lst = data["users_lst"]
    if msg is not None:
        return render(request, 'add_instructor_to_course.html', {"course_details": course_details, "instructors_lst": instructors_lst, "instructor_exists": data["users_exist"], "msg": msg})
    return render(request, 'add_instructor_to_course.html', {"course_details": course_details, "instructors_lst": instructors_lst, "instructor_exists": data["users_exist"]})

@login_required(login_url='institution_login')
def remove_course(request):
    """ Remove a course from the institution, path='course/remove' """
    course_id = request.GET.get('course_id')
    try:
        course_details = Course.objects.get(pk=course_id)
    except Exception as e:
        request.session['course_id'] = course_id
        return redirect('complete_course_details')
    course_details.delete()
    return redirect('course_list')

@login_required(login_url='institution_login')
def remove_user_from_course(request):
    """ Remove Student, Instructor from a course, path='course/remove-user' """
    course_id = request.POST.get('course_id')
    user_id = request.POST.get('user_id')
    try:
        user_course_relation = UserCourseRelation.objects.get(course=course_id, user=user_id)
    except Exception as e:
        request.session['course_id'] = course_id
        return redirect('complete_course_details')
    user_course_relation.delete()
    request.session['course_id'] = course_id
    return redirect('complete_course_details')

