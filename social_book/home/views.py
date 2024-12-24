from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from .models import Cuser,Book,Author
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib.auth.models import User
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
        if User.objects.filter(username=user_name).exists():
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
        user = Cuser(user_name=user_name, email=email, user_date_of_birth=dob, user_gender=gender, user_location=location, user_image=user_image)
        user.set_password(password1)  # Hash the password before saving
        user.save()
        user2 = User.objects.create_user(username=user_name, email=email, password=password1)
        user2.save()
        # Authenticate and log the user in
        user_login = auth.authenticate(username=user_name, password=password1)
        if user_login is not None:
            auth.login(request, user_login)
            return redirect('/')  # Redirect to root URL

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




@login_required(login_url='signin')
def profile(request,pk):
    return render(request, 'profile.html')



@login_required(login_url='signin')
def search(request):
    results = None
    if request.method == 'POST':
        # Get search parameters
        book_name = request.POST.get('book_name', '').strip()
        author_name = request.POST.get('author', '').strip()
        genre = request.POST.get('genre', '').strip()

        # Perform the query
        results = Book.objects.all()

        if book_name:
            results = results.filter(book_name__icontains=book_name)

        if author_name:
            results = results.filter(author_id__name__icontains=author_name)

        if genre:
            # Handle comma-separated genres
            search_genres = [g.strip().lower() for g in genre.split(',')]
            for g in search_genres:
                results = results.filter(genre__icontains=g)

        if not results.exists():
            results = None
    return render(request, 'search.html', {'results': results})




@login_required(login_url='signin')
def book(request, pk):
    # Get the book by its primary key (pk)
    book = get_object_or_404(Book, pk=pk)

    # Render the book_profile.html template with the book data
    return render(request, 'book_profile.html', {'book': book})



@login_required(login_url='signin')
def author(request,pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, 'author_profile.html', {'author': author})

@login_required(login_url='signin')
def profile(request):
    user = request.user  # Get the current logged-in user
    # Use get_object_or_404 to avoid errors if Cuser profile does not exist
    profile = get_object_or_404(Cuser, user_name=user.username)

    context = {
        'profile': profile  # Pass the user profile to the template
    }

    return render(request, 'profile.html', context)