from django.shortcuts import render, redirect
from django.contrib import messages, auth
from .models import User
from django.contrib.auth.decorators import login_required
from datetime import datetime
# Create your views here.


@login_required(login_url='signin')
def index(request):
    return render(request, 'index.html')


def signup(request):
    if request.method == 'POST':
        # Collect form data
        user_name = request.POST['user_name']  # Field name matches your model
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        date_of_birth = request.POST['user_date_of_birth']
        gender = request.POST['user_gender']
        location = request.POST['user_location']
        user_image = request.FILES.get('user_image')  # Handle image upload

        # Password match validation
        if password1 != password2:
            messages.info(request, 'Passwords do not match.')
            return redirect('signup')

        # Username and email uniqueness checks
        if User.objects.filter(user_name=user_name).exists():
            messages.info(request, 'Username is already taken.')
            return redirect('signup')
        elif User.objects.filter(email=email).exists():
            messages.info(request, 'Email is already taken.')
            return redirect('signup')

        # Convert date_of_birth to a date object
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()  # Ensure the date is in correct format
        except ValueError:
            messages.info(request, 'Invalid date of birth format.')
            return redirect('signup')

        # Create the User object
        user = User(user_name=user_name, email=email, user_date_of_birth=dob, user_gender=gender, user_location=location, user_image=user_image)
        user.set_password(password1)  # Hash the password before saving
        user.save()

        # Authenticate and log the user in
        user_login = auth.authenticate(username=user_name, password=password1)
        auth.login(request, user_login)

        return redirect('index')  # Redirect to settings page after successful sign up

    else:
        return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid credentials...')
            return redirect('signin')
    else:
        return render(request, 'signin.html')



@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')
