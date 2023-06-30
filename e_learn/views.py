from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Institution, Course, UserCourseRelation, Assignment, AssignmentGrades, UserInstitutionRelation, Subscription, Notes
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.core.mail import send_mail
import os
from django.contrib.auth.hashers import make_password


def home(request):
    """ Dashboard of the application """
    return render(request, 'home.html')

def check_user_plan(user_data):
    """ function to know if a user has a premium plan or not """
    try:
        institutionUser_relation = UserInstitutionRelation.objects.get(user=user_data)
        institution_details = Institution.objects.get(pk=institutionUser_relation.institution)
        subscription_details = Subscription.objects.get(user=institution_details.user)
        if subscription_details.is_basic:
            return False
        return True
    except Exception as e:
        print(e)
        return False

def send_email(recipient_mail_list, data, topic):
    """ function to send messages through emails """
    if topic == "signup":
        subject = "New account created."
        message = data
    if topic == "":
        pass
    from_email = settings.EMAIL_HOST_USER
    recipient_list = recipient_mail_list
    send_mail(subject, message, from_email, recipient_list, fail_silently=True)


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
            plan = request.session["institution_details"]["plan"]
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
                new_user = User(first_name=new_name, username=new_email, email=new_email, password=make_password(new_password1), is_institution=True)
                new_user.save()
                new_institution = Institution(name=new_name, user=new_user)
                new_institution.save()
                if plan == "basic":
                    new_subscription = Subscription(user=new_user, amount_paid=amount, currency=currency, is_basic=True)
                else:
                    new_subscription = Subscription(user=new_user, amount_paid=amount, currency=currency, is_premium=True)
                new_subscription.save()
                # mailing welcome message
                email_data = "Welcome to the learning space.\n\n Transaction details\n Amount paid: {}\n Currency: {}\n Subscribed plan: {} \n\nYou can start accessing the website from http://127.0.0.1:8000/login".format(amount, currency, plan)
                send_email([new_email], email_data, "signup")
                return render(request, 'login.html', {'msg': "Registered Successfully!"})
            elif user_type == "student":
                new_user = User(first_name=new_first_name, last_name=new_last_name, email=new_email,
                                password=make_password(new_password1), is_student=True, username=new_email)
                new_user.save()
                institution_obj = Institution.objects.get(user=request.user)
                new_relation = UserInstitutionRelation(institution=institution_obj, user=new_user, is_student=True)
                new_relation.save()
                # mailing student credentials
                email_data = "Welcome to the learning space. You are enrolled as a Student.\nChange your password as early as possible.\nYour current credentials are,\nEmail: " + str(
                    new_email) + "\nPassword: " + str(new_password1)
                send_email([new_email], email_data, "signup")
                return render(request, 'institution_home.html', {'msg': "Student Registered Successfully!"})
            else:
                new_user = User(first_name=new_first_name, last_name=new_last_name, email=new_email,
                                password=make_password(new_password1), is_instructor=True, username=new_email)
                new_user.save()
                institution_obj = Institution.objects.get(user=request.user)
                new_relation = UserInstitutionRelation(institution=institution_obj, user=new_user, is_instructor=True)
                new_relation.save()
                # mailing instructor credentials
                email_data = "Welcome to learning space. You are enrolled as an Instructor.\nChange your password as early as possible.\nYour current credentials are,\nEmail: " + str(
                    new_email) + "\nPassword: " + str(new_password1)
                send_email([new_email], email_data, "signup")
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
                    amount_to_be_paid = amount_to_be_paid * 0.74
                institution_details = {"name": new_name, "email": new_email, "password": new_password1,
                                       "amount": amount_to_be_paid, "plan": plan, "currency": currency}
                request.session["institution_details"] = institution_details
                return render(request, 'payment.html', institution_details)
            else:
                return render(request, 'institution_signup.html', {'msg': "Passwords do not match!!!"})
        else:
            return render(request, 'institution_signup.html',
                          {'msg': "Institution name already exists! Try a different name!"})
    return render(request, 'institution_signup.html')


class LoginUserView(View):
    """ class based view to perform login operation, path='login' """
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        return render(self.request, self.template_name)

    def post(self, request, *args, **kwargs):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            if user.is_institution:
                return redirect('institution_home')
            elif user.is_student:
                return redirect('student_home')
            else:
                return redirect('instructor_home')
        else:
            return render(self.request, self.template_name, {'msg': "Username or Password is incorrect!!!"})


@login_required(login_url='logout')
def logout_user(request):
    """ logout users, path='logout' """
    logout(request)
    return redirect('login')


@login_required(login_url='institution_login')
def institution_home(request):
    """ Institution's Home Page, path=institution/home """
    send_data = {}
    requested_profile = request.GET.get('request_profile')
    req_update_profile = request.GET.get('req_update_profile')
    if req_update_profile is not None:
        send_data['user_details'] = request.user
        send_data['req_update_profile'] = True
        return render(request, 'institution_home.html', send_data)
    # update profile details
    if request.method == 'POST':
        institution_name = request.POST.get('institution_name')
        new_password = request.POST.get('password')
        user_details = User.objects.get(pk=request.user.id)
        institution_details = Institution.objects.get(user=request.user)
        user_details.first_name = institution_name
        user_details.password = make_password(new_password)
        institution_details.name = institution_name
        user_details.save()
        institution_details.save()
        requested_profile = True
        send_data['msg'] = 'Profile updated successfully.'
    # display profile details
    if requested_profile is not None:
        subscription_details = Subscription.objects.get(user=request.user)
        if subscription_details.is_basic:
            plan = "Basic"
        else:
            plan = "Premium"
        send_data['plan'] = plan
        send_data['user_details'] = User.objects.get(pk=request.user.id)
        send_data['requested_profile'] = True
        return render(request, 'institution_home.html', send_data)
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


def common_home(request):
    """ function to display student and instructor home details """
    courses_lst = user_courses(request)
    send_data = {}
    requested_profile = request.GET.get('request_profile')
    # display update form to user
    if request.GET.get('req_update_profile') is not None:
        send_data['user_details'] = request.user
        send_data['req_update_profile'] = True
        return send_data
    # update profile details
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        new_password = request.POST.get('password')
        user_details = User.objects.get(pk=request.user.id)
        user_details.first_name = first_name
        user_details.last_name = last_name
        user_details.password = make_password(new_password)
        user_details.save()
        requested_profile = True
        send_data['msg'] = 'Profile updated successfully.'
    # display profile details
    if requested_profile is not None:
        send_data['user_details'] = User.objects.get(pk=request.user.id)
        send_data['requested_profile'] = True
        return send_data
    # display course list
    if courses_lst is None or len(courses_lst) == 0:
        send_data = {'msg': "You don't have any courses to display."}
        return send_data
    send_data = {'course_list': courses_lst, 'course_exist': True}
    return send_data


@login_required(login_url='login')
def student_home(request):
    """ Student's Home Page, path='student/home'
    features: profile, home, Course list
    """
    send_data = common_home(request)
    return render(request, 'student_home.html', send_data)


@login_required(login_url='login')
def instructor_home(request):
    """ Instructor's Home Page, path=instructor/home
    features: profile, home, Course list
    """
    send_data = common_home(request)
    return render(request, 'instructor_home.html', send_data)


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
            return render(request, 'institution_home.html',
                          {'msg': 'Course not created yet, try creating a new course!'})
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
            return render(request, 'institution_home.html',
                          {'msg': 'Students not registered yet, try registering a new student!'})
        return render(request, 'institution_users_list.html', {'user_list': student_lst, 'student_exist': True})
    except Exception as e:
        print(e)
        return render(request, 'institution_home.html',
                      {'msg': 'Students not registered yet, try registering a new student!'})


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
            return render(request, 'institution_home.html',
                          {'msg': 'Instructors not registered yet, try registering a new Instructor!'})
        return render(request, 'institution_users_list.html', {'user_list': instructor_lst, 'instructor_exist': True})
    except Exception as e:
        return render(request, 'institution_home.html',
                      {'msg': 'Instructors not registered yet, try registering a new Instructor!'})


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
        return render(request, "course_data_to_institution.html",
                      {'course_details': course, 'msg': "No Student or Instructor is assigned to this course yet."})
    if data["instructor"] is None:
        instructor_exists = False
    if len(data["students_lst"]) == 0:
        students_exists = False
    send_data = {'course_details': data["course"], 'students_lst': data["students_lst"],
                 'instructor': data["instructor"], 'instructor_exists': instructor_exists,
                 'students_exists': students_exists}
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
        # check if it is a premium user or not and send email
        is_premium_user = check_user_plan(user_details)
        if is_premium_user:
            msg = "Student added to course successfully."
            email_data = "Now you can access the course '{}' in the Learning Space through  http://127.0.0.1:8000/login".format(course_details.name)
            send_email([user_details.email], email_data, "add_student_to_course")
    else:
        course_id = request.GET.get('course_id')
        course_details = Course.objects.get(id=course_id)

    data = institution_users(request, "student")
    if not data["users_exist"]:
        return render(request, 'student_signup.html',
                      {"msg": 'Students not registered in the institution yet, try registering a new student!'})
    relations = UserCourseRelation.objects.filter(course=course_details)
    students_lst = []
    relations_user = []
    for relation in relations:
        relations_user.append(relation.user)
    for user in data["users_lst"]:
        if user not in relations_user:
            students_lst.append(user)
    if len(relations) != 0 and len(students_lst) == 0:
        return render(request, 'add_students_to_course.html',
                      {'course_details': course_details, 'msg': "No new students to add to this course."})
    if len(relations) == 0:
        students_lst = data["users_lst"]
    if msg is not None:
        return render(request, 'add_students_to_course.html',
                      {"course_details": course_details, "students_lst": students_lst,
                       "student_exists": data["users_exist"], "msg": msg})
    return render(request, 'add_students_to_course.html',
                  {"course_details": course_details, "students_lst": students_lst,
                   "student_exists": data["users_exist"]})


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
        return render(request, 'instructor_signup.html',
                      {"msg": 'Instructors not registered in the institution yet, try registering a new instructor!'})
    relations = UserCourseRelation.objects.filter(course=course_details)
    instructors_lst = []
    relations_user = []
    for relation in relations:
        relations_user.append(relation.user)
    for user in data["users_lst"]:
        if user not in relations_user:
            instructors_lst.append(user)
    if len(relations) != 0 and len(instructors_lst) == 0:
        return render(request, 'add_instructor_to_course.html',
                      {'course_details': course_details, 'msg': "No new instructors to add to this course."})
    elif len(relations) == 0:
        instructors_lst = data["users_lst"]
    if msg is not None:
        return render(request, 'add_instructor_to_course.html',
                      {"course_details": course_details, "instructors_lst": instructors_lst,
                       "instructor_exists": data["users_exist"], "msg": msg})
    return render(request, 'add_instructor_to_course.html',
                  {"course_details": course_details, "instructors_lst": instructors_lst,
                   "instructor_exists": data["users_exist"]})


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


def course_notes(course_id):
    """ function to fetch all notes of a course """
    try:
        notes_data = Notes.objects.filter(course=course_id)
        if len(notes_data) == 0 or notes_data is None:
            return None
        for notes in notes_data:
            notes.notes_doc = str(notes.notes_doc).split('/')[-1]
        return notes_data
    except Exception as e:
        return None


def course_assignments(course_id):
    """ function to fetch all assignments of a course """
    try:
        assignments_data = Assignment.objects.filter(course=course_id)
        if len(assignments_data) == 0 or assignments_data is None:
            return None
        for assignment_record in assignments_data:
            assignment_record.assignment_doc = str(assignment_record.assignment_doc).split('/')[-1]
        return assignments_data
    except Exception as e:
        print(e)
        return None


def create_assignmentgrade_relation(assignment_details, course_id):
    """ function to create assignmentgrade relations in the DB """
    course_students = course_users(course_id)['students_lst']
    for student in course_students:
        new_relation = AssignmentGrades(grade=None, assignment=assignment_details, user=student)
        new_relation.save()


@login_required(login_url='login')
def download(request):
    """ download lecture notes and assignments, path='download/<notes or assignment id>' """
    notes_id = request.GET.get('notes_id')
    assignment_id = request.GET.get('assignment_id')
    assignmentgrade_id = request.GEt.get('assignmentgrade_id')
    # download notes file
    if notes_id is not None:
        notes = get_object_or_404(Notes, pk=notes_id)
        response = HttpResponse(notes.notes_doc, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{notes.notes_doc.name}"'
    # download assignment file
    elif assignment_id is not None:
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        response = HttpResponse(assignment.assignment_doc, content_type='application/pdf')
        filename = str(assignment.assignment_doc.name).split("/")[-1]
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # download submission
    else:
        assignment = get_object_or_404(AssignmentGrades, pk=assignmentgrade_id)
        response = HttpResponse(assignment.assignment_doc, content_type='application/pdf')
        filename = str(assignment.assignment_doc.name).split("/")[-1]
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url='login')
def instructor_course_details(request):
    """ display course details(notes, assignments, students) for instructor(user), path='instructor/course' with different query parameters
    features: Course details, Students, Lectures(notes), Assignment
    """
    course_id = request.GET.get('course_id')
    assignment_id = request.GET.get('assignment_id')
    # students
    req_students = request.GET.get('request_students')
    req_update_final_grade = request.GET.get('request_update_final_grade')
    # notes
    req_notes = request.GET.get('request_notes')
    req_notes_create = request.GET.get('request_notes_create')
    req_update_notes = request.GET.get('request_update_notes')
    req_remove_notes = request.GET.get('remove_notes')
    # assignments
    req_assignments = request.GET.get('request_assignments')
    req_assignment_create = request.GET.get('request_assignment_create')
    req_update_assignment = request.GET.get('request_update_assignment')
    req_remove_assignment = request.GET.get('remove_assignment')
    # grades
    req_grades = request.GET.get('request_grades')
    req_update_grade = request.GET.get('request_update_grade')
    course_data = Course.objects.get(pk=course_id)
    send_data = {"course_details": course_data}
    requested_notes = False
    requested_students = False
    requested_assignments = False
    requested_grades = False
    if req_students is not None:
        requested_students = True
        send_data['requested_students'] = True
    elif req_notes is not None:
        requested_notes = True
        send_data['requested_notes'] = True
    elif req_notes_create is not None:
        send_data['requested_notes_create'] = True
        return render(request, 'course_data_to_instructor.html', send_data)
    elif req_assignment_create is not None:
        send_data['requested_assignment_create'] = True
        return render(request, 'course_data_to_instructor.html', send_data)
    elif req_grades is not None:
        send_data['requested_grades'] = True
        requested_grades = True
    # perform database operations for lecture notes and assignments
    elif request.method == 'POST':
        # Add new notes
        if request.GET.get('notes'):
            notes_name = request.POST.get('notes_name')
            notes_doc = request.FILES.get("notes_doc")
            # create a new notes record
            if request.GET.get('update') is None:
                if notes_doc:
                    new_notes = Notes(name=notes_name, course=course_data, notes_doc=notes_doc)
                else:
                    new_notes = Notes(name=notes_name, course=course_data)
                new_notes.save()
            # update a notes record
            else:
                notes_id = request.GET.get('notes_id')
                notes_doc = request.FILES.get("notes_doc")
                notes_obj = Notes.objects.get(pk=notes_id)
                file_path = "./media/" + str(notes_obj.notes_doc)
                if notes_doc is not None:
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        os.remove(file_path)
                    notes_obj.notes_doc = notes_doc
                notes_obj.name = notes_name
                notes_obj.save()
            # display all notes
            requested_notes = True
            send_data['requested_notes'] = requested_notes
        # Add new assignment
        elif request.GET.get('assignment'):
            assignment_name = request.POST.get('assignment_name')
            assignment_deadline = request.POST.get('assignment_deadline')
            assignment_gradepoints = request.POST.get('assignment_gradepoints')
            assignment_doc = request.FILES.get("assignment_doc")
            # create a new assignment record
            if request.GET.get('update') is None:
                if assignment_doc:
                    new_assignment = Assignment(name=assignment_name,
                                                deadline=assignment_deadline, course=course_data,
                                                grade_points=assignment_gradepoints, assignment_doc=assignment_doc)
                else:
                    new_assignment = Assignment(name=assignment_name,
                                                deadline=assignment_deadline, course=course_data,
                                                grade_points=assignment_gradepoints)
                new_assignment.save()
                create_assignmentgrade_relation(new_assignment, course_id)
            # update an assignment record
            else:
                assignment_id = request.GET.get('assignment_id')
                assignment_obj = Assignment.objects.get(pk=assignment_id)
                assignment_doc = request.FILES.get("assignment_doc")
                file_path = "./media/" + str(assignment_obj.assignment_doc)
                if assignment_doc is not None and assignment_doc != '':
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        os.remove(file_path)
                    assignment_obj.assignment_doc = assignment_doc
                assignment_obj.name = assignment_name
                if assignment_deadline is not None and assignment_deadline != '':
                    assignment_obj.deadline = assignment_deadline
                assignment_obj.grade_points = assignment_gradepoints
                assignment_obj.save()
            # display all assignments
            requested_assignments = True
            send_data['requested_assignments'] = requested_assignments
        # update grade of an assignment
        elif request.GET.get('grade'):
            assignment_id = request.GET.get('assignment_id')
            record_id = request.GET.get('student_record')
            new_grade = request.POST.get('grade')
            assignmentgrade_obj = AssignmentGrades.objects.get(pk=record_id)
            assignmentgrade_obj.grade = new_grade
            assignmentgrade_obj.save()
            requested_grades = True
            send_data['requested_grades'] = requested_grades
        # update final grade of a student
        else:
            assignment_id = request.GET.get('assignment_id')
            record_id = request.GET.get('student_record')
            new_grade = request.POST.get('grade')
            usercourserelation_obj = UserCourseRelation.objects.get(pk=record_id)
            usercourserelation_obj.final_grade = new_grade
            usercourserelation_obj.save()
            requested_students = True
            send_data['requested_students'] = requested_students
    elif req_remove_notes is not None:
        notes_id = request.GET.get('notes_id')
        try:
            notes_obj = Notes.objects.get(pk=notes_id)
            delete_file_path = "./media/" + str(notes_obj.notes_doc)
            os.remove(delete_file_path)
            notes_obj.delete()
        except Exception as e:
            pass
        # display all notes
        requested_notes = True
        send_data['requested_notes'] = requested_notes
    elif req_remove_assignment is not None:
        assignment_id = request.GET.get('assignment_id')
        try:
            assignment_obj = Assignment.objects.get(pk=assignment_id)
            delete_file_path = "./media/" + str(assignment_obj.assignment_doc)
            if os.path.exists(delete_file_path) and os.path.isfile(delete_file_path):
                os.remove(delete_file_path)
            assignments_data = AssignmentGrades.objects.filter(assignment=assignment_obj)
            for assignment in assignments_data:
                delete_file_path = "./media/" + str(assignment.assignment_doc)
                if os.path.exists(delete_file_path) and os.path.isfile(delete_file_path):
                    os.remove(delete_file_path)
            assignment_obj.delete()
        except Exception as e:
            pass
        # display all assignment
        requested_assignments = True
        send_data['requested_assignments'] = requested_assignments
    elif req_update_notes is not None:
        notes_id = request.GET.get('notes_id')
        notes_details = Notes.objects.get(pk=notes_id)
        send_data['requested_update_notes'] = True
        send_data['notes_details'] = notes_details
        return render(request, 'course_data_to_instructor.html', send_data)
    elif req_assignments is not None:
        requested_assignments = True
        send_data['requested_assignments'] = True
    elif req_update_assignment is not None:
        assignment_id = request.GET.get('assignment_id')
        assignment_details = Assignment.objects.get(pk=assignment_id)
        deadline = str(assignment_details.deadline).replace(" ", "T")
        deadline = deadline.replace("+00:00", "")
        send_data['deadline'] = deadline
        send_data['requested_update_assignment'] = True
        send_data['assignment_details'] = assignment_details
        return render(request, 'course_data_to_instructor.html', send_data)
    elif req_update_grade is not None:
        send_data['requested_grades'] = True
        send_data['requested_grade_update'] = True
        requested_grades = True
    elif req_update_final_grade is not None:
        send_data['requested_final_grade_update'] = True
        requested_students = True
        send_data['requested_students'] = requested_students

    # display assignments of a course
    if requested_assignments:
        assignments_data = course_assignments(course_id)
        if assignments_data is None:
            send_data['msg'] = "No assignments created for this course."
            return render(request, 'course_data_to_instructor.html', send_data)
        send_data['assignment_list'] = assignments_data

        return render(request, 'course_data_to_instructor.html', send_data)

    # display notes of a course
    if requested_notes:
        notes_data = course_notes(course_id)
        if notes_data is None:
            send_data['msg'] = "No notes created for this course."
            return render(request, 'course_data_to_instructor.html', send_data)
        send_data['notes_list'] = notes_data
        return render(request, 'course_data_to_instructor.html', send_data)

    # display students of a course
    if requested_students:
        users_data = UserCourseRelation.objects.filter(course=course_id)
        students_exists = True
        students_lst = []
        if users_data is None or len(users_data) == 0:
            students_exists = False
            students_lst = users_data
        else:
            for user_record in users_data:
                if user_record.user.is_student:
                    students_lst.append(user_record)
        send_data['students_lst'] = students_lst
        send_data['students_exists'] = students_exists

    # display assignment grade details
    if requested_grades:
        assignment_details = Assignment.objects.get(pk=assignment_id)
        users_data = course_users(course_id=course_id)
        if users_data is None:
            return render(request, "instructor_home.html")
        students_exists = True
        if len(users_data["students_lst"]) == 0:
            send_data['msg'] = "No students in the course yet."
            return render(request, "course_data_to_instructor.html", send_data)
        students_lst = AssignmentGrades.objects.filter(assignment=assignment_id)
        for student in students_lst:
            student.assignment_doc = str(student.assignment_doc.name).split('/')[-1]
        send_data["students_lst"] = students_lst
        send_data["assignment_details"] = assignment_details
    return render(request, "course_data_to_instructor.html", send_data)


def get_user_assignment_data(user_data, assignment_id):
    """ function to fetch assignment data of a user """
    try:
        assignments_data = Assignment.objects.get(pk=assignment_id)
        assignment_grades_relation = AssignmentGrades.objects.get(user=user_data, assignment=assignment_id)
        assignments_data.assignmentgrades = assignment_grades_relation
        # renaming the filenames to display to user
        assignments_data.assignmentgrades.assignment_doc = \
        str(assignments_data.assignmentgrades.assignment_doc).split('/')[-1]
        assignments_data.assignment_doc = str(assignments_data.assignment_doc).split('/')[-1]
        return assignments_data
    except Exception as e:
        print(e)
        return None


@login_required(login_url='login')
def student_course_details(request):
    """ display course details(notes, assignments, students) for instructor(user), path='instructor/course' with different query parameters
    features: Course details, Instructor, Lectures(notes), Assignments
    """
    send_data = {}
    template = "course_data_to_student.html"
    course_id = request.GET.get('course_id')
    course_data = None
    if course_id is not None or course_id != '':
        course_data = Course.objects.get(pk=course_id)
        final_grade = UserCourseRelation.objects.get(course=course_id, user=request.user).final_grade
        send_data["course_details"] = course_data
        send_data["final_grade"] = final_grade
    assignment_id = request.GET.get('assignment_id')
    # notes
    req_notes = request.GET.get('request_notes')
    # assignments
    req_assignments = request.GET.get('request_assignments')
    req_specific_assignment = request.GET.get('req_specific_assignment')
    req_upload_doc = request.GET.get('upload_doc')
    requested_notes = False
    requested_assignments = False
    if req_notes is not None:
        requested_notes = True
        send_data['requested_notes'] = True
    elif req_assignments is not None:
        requested_assignments = True
        send_data['requested_assignments'] = True
    elif req_specific_assignment is not None:
        send_data["req_specific_assignment"] = True
    elif req_upload_doc is not None:
        req_specific_assignment = True
        assignment_doc = request.FILES.get("assignment_doc")
        assignmentgrade_id = request.GET.get('assignmentgrade_id')
        assignment_obj = AssignmentGrades.objects.get(pk=assignmentgrade_id)
        file_path = "./media/" + str(assignment_obj.assignment_doc)
        if assignment_doc is not None and assignment_doc != '':
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
            assignment_obj.assignment_doc = assignment_doc
            assignment_obj.submitted_status = True
            assignment_obj.save()
        send_data['msg'] = "Assignment Submitted Successfully."

    # display details of specific assignment
    if req_specific_assignment is not None:
        user_assignment_data = get_user_assignment_data(request.user, assignment_id)
        send_data["assignment_data"] = user_assignment_data
        send_data["req_specific_assignment"] = True
        return render(request, template, send_data)

    # display assignments of a course
    if requested_assignments:
        assignments_data = course_assignments(course_id)
        if assignments_data is None:
            send_data['msg'] = "No assignments created for this course."
            return render(request, template, send_data)
        for assignment in assignments_data:
            assignmentgrade_record = AssignmentGrades.objects.get(assignment_id=assignment.id, user=request.user)
            assignment.status = assignmentgrade_record.submitted_status
            assignment.grade = assignmentgrade_record.grade
        send_data['assignment_list'] = assignments_data
        return render(request, template, send_data)

    # display notes of a course
    if requested_notes:
        notes_data = course_notes(course_id)
        if notes_data is None:
            send_data['msg'] = "No notes created for this course."
            return render(request, template, send_data)
        send_data['notes_list'] = notes_data
        return render(request, template, send_data)
    return render(request, template, send_data)
