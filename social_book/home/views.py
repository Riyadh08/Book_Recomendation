from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from .models import Cuser,Book,Author,Review
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
@login_required(login_url='signin')
def index(request):
    return render(request, 'index.html')

from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.models import User
from .models import Cuser
from datetime import datetime

def signup(request):
    if request.method == 'POST':
        # Collect form data
        user_name = request.POST['user_name']
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
        user = User.objects.create_user(username=user_name, email=email, password=password1)
        
        # Create the Cuser object and link it to the User
        cuser = Cuser(
            user=user,  # Link the Cuser to the User object
            user_date_of_birth=dob,
            user_gender=gender,
            user_location=location,
            user_image=user_image
        )
        cuser.save()

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




# @login_required(login_url='signin')
# def profile(request,pk):
#     return render(request, 'profile.html')



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
def author(request,pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, 'author_profile.html', {'author': author})

@login_required(login_url='signin')
def profile(request):
    user = request.user  # Get the current logged-in user
    # Use get_object_or_404 to avoid errors if Cuser profile does not exist
    profile = get_object_or_404(Cuser, user__username=user.username)

    context = {
        'profile': profile  # Pass the user profile to the template
    }

    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def book(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Get the most recent review
    recent_review = book.reviews.order_by('-created_at').first()

    # Paginate all reviews (5 per page)
    all_reviews = book.reviews.order_by('-created_at')
    paginator = Paginator(all_reviews, 5)
    page_number = request.GET.get('page', 1)
    reviews = paginator.get_page(page_number)

    context = {
        'book': book,
        'recent_review': recent_review,
        'reviews': reviews,
        'average_rating': book.average_rating(),
        'total_ratings': book.total_ratings(),
    }

    return render(request, 'book_profile.html', context)


@login_required(login_url='signin')
def reviews_list(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    reviews = book.reviews.order_by('-created_at')  # Latest first
    paginator = Paginator(reviews, 5)  # 5 reviews per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    reviews_data = [
    {
        'user': review.user_id.username,
        'profile': review.user_id.cuser.user_image.url if hasattr(review.user_id, 'cuser') and review.user_id.cuser.user_image else '/media/blank-profile-picture.png',
        'rating': review.rating,
        'review_text': review.review_text,
    }
    for review in page_obj
    ]


    return JsonResponse({
        'reviews': reviews_data,
        'has_next': page_obj.has_next(),
    })





@login_required(login_url='signin')
@csrf_exempt
def submit_review(request, book_id):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            review_text = data.get('review')
            rating = data.get('rating')

            # Validate the input
            if not review_text or not rating:
                return JsonResponse({'success': False, 'message': 'Review and rating are required.'}, status=400)

            # Fetch the book object
            try:
                book = Book.objects.get(pk=book_id)
            except Book.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Book not found.'}, status=404)

            # Fetch the current authenticated user
            user = request.user  # `request.user` will give you the currently logged-in user

            # Create the review
            review = Review.objects.create(
                book_id=book,  # Correct foreign key assignment for book
                user_id=user,  # Correct foreign key assignment for user
                review_text=review_text,
                rating=int(rating)
            )

            return JsonResponse({'success': True, 'message': 'Review submitted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
