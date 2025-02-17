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
<<<<<<< Updated upstream
@login_required(login_url='signin')
=======
from django.db.models import Avg, Q, Count
from django.utils import timezone
from django.urls import reverse
from django.db import transaction
from functools import wraps

def user_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if admin is trying to access user pages
        if request.session.get('is_admin'):
            messages.error(request, 'Please log out of admin panel to access user pages')
            return redirect('admin_dashboard')
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@user_login_required
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
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
=======
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            with transaction.atomic():
                user = auth.authenticate(username=username, password=password)
                
                if user is not None:
                    # Check if user is banned
                    try:
                        cuser = Cuser.objects.get(user=user)
                        if cuser.is_banned:
                            messages.error(request, f'Your account has been banned. Reason: {cuser.ban_reason}')
                            return render(request, 'signin.html')
                    except Cuser.DoesNotExist:
                        pass
                    
                    auth.login(request, user)
                    return redirect('index')
                else:
                    messages.error(request, 'Invalid credentials')
                    return render(request, 'signin.html')
                    
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'signin.html')
            
    # If user is already logged in, redirect to index
    if request.user.is_authenticated:
        return redirect('index')
        
    return render(request, 'signin.html')
    

>>>>>>> Stashed changes

@user_login_required
def logout(request):
    try:
        with transaction.atomic():
            auth.logout(request)
            return redirect('signin')
    except Exception as e:
        messages.error(request, 'An error occurred during logout. Please try again.')
        return redirect('index')




@login_required(login_url='signin')
def profile(request,pk):
    return render(request, 'profile.html')



@user_login_required
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




# @login_required(login_url='signin')
# def book(request, pk):
#     # Get the book by its primary key (pk)
#     book = get_object_or_404(Book, pk=pk)

#     # Render the book_profile.html template with the book data
#     return render(request, 'book_profile.html', {'book': book})



<<<<<<< Updated upstream
@login_required(login_url='signin')
def author(request,pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, 'author_profile.html', {'author': author})
=======
@user_login_required
def author(request, pk):
    author = get_object_or_404(Author, pk=pk)
    books = Book.objects.filter(author_id=author).annotate(average_rating=Avg('reviews__rating')).order_by('-average_rating')
    return render(request, 'author_profile.html', {'author': author, 'books': books[:4]})

@user_login_required
def load_more_books(request, pk):
    author = get_object_or_404(Author, pk=pk)
    page = int(request.GET.get('page', 1))
    books = Book.objects.filter(author_id=author).annotate(average_rating=Avg('reviews__rating')).order_by('-average_rating')
    
    paginator = Paginator(books, 4)  # 4 books per page
    books_page = paginator.page(page)
    
    books_data = []
    for book in books_page:
        books_data.append({
            'title': book.book_name,
            'rating': book.average_rating,
            'image': book.image.url,
            'url': book.get_absolute_url()
        })
    
    return JsonResponse({'books': books_data, 'has_next': books_page.has_next()})


>>>>>>> Stashed changes

@user_login_required
def profile(request):
    user = request.user  # Get the current logged-in user
    # Use get_object_or_404 to avoid errors if Cuser profile does not exist
    profile = get_object_or_404(Cuser, user_name=user.username)

    context = {
        'profile': profile  # Pass the user profile to the template
    }

    return render(request, 'profile.html', context)

@user_login_required
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
    }

    return render(request, 'book_profile.html', context)


@user_login_required
def reviews_list(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    reviews = book.reviews.order_by('-created_at')  # Latest first
    paginator = Paginator(reviews, 5)  # 5 reviews per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    reviews_data = [
        {
            'user': review.user_id.username,
            'profile': review.user_id.profile_picture.url if hasattr(review.user_id, 'profile_picture') else 'https://via.placeholder.com/50',  # Profile picture
            'rating': review.rating,
            'review_text': review.review_text,
        }
        for review in page_obj
    ]

    return JsonResponse({
        'reviews': reviews_data,
        'has_next': page_obj.has_next(),
    })





@user_login_required
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
<<<<<<< Updated upstream
=======


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import os

# Load the recommendation model (your function or logic for recommendations)
from .recommendation_model import content_based_recommendations

# Load the dataset once to use across requests
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_path = os.path.join(BASE_DIR, 'static', 'assets', 'dataset', 'Final_Dataset.csv')
df = pd.read_csv(dataset_path)

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        # Parse user input
        data = json.loads(request.body.decode('utf-8'))
        user_input = data.get('query', '').strip().lower()
        print(f"User Input: {user_input}")  # Debugging

        if not user_input:
            return JsonResponse({"response": "Please provide a book title or author name for recommendations."})

        # Search in the dataset
        filtered_books = df[
            (df['Title'].str.lower().str.contains(user_input)) | 
            (df['Author'].str.lower().str.contains(user_input))
        ]
        print(f"Filtered Books: {filtered_books}")  # Debugging

        if filtered_books.empty:
            return JsonResponse({"response": f"Sorry, I couldn't find any books matching '{user_input}'."})

        # Use the first matching book's ID for recommendations
        book_id = filtered_books.iloc[0]['Book_ID']
        print(f"Selected Book ID: {book_id}")  # Debugging

        recommendations = content_based_recommendations(book_id=book_id, n=5)
        print(f"Recommendations: {recommendations}")  # Debugging

        recommended_books = recommendations.to_dict(orient='records')
        return JsonResponse({
            "response": f"Here are some book recommendations based on '{filtered_books.iloc[0]['Title']}' by {filtered_books.iloc[0]['Author']}:",
            "recommendations": recommended_books
        })

    return JsonResponse({"response": "Welcome to the Book Recommendation Chatbot!"})



from django.shortcuts import render

def chatbot_page(request):
    return render(request, 'chatbot.html')
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Author, FollowAuthor

@user_login_required
@csrf_exempt  # If using AJAX requests without CSRF token
def follow_author(request):
    if request.method == "POST":
        data = json.loads(request.body)
        author_id = data.get("author_id")
        action = data.get("action")  # Expect "follow" or "unfollow"

        author = get_object_or_404(Author, author_id=author_id)
        
        if action == "follow":
            # Prevent duplicate follows
            follow_instance, created = FollowAuthor.objects.get_or_create(follower=request.user, following=author)
            if created:
                return JsonResponse({"success": True, "message": "Followed successfully."})
            else:
                return JsonResponse({"success": False, "message": "Already following this author."}, status=400)
        
        elif action == "unfollow":
            follow_instance = FollowAuthor.objects.filter(follower=request.user, following=author).first()
            if follow_instance:
                follow_instance.delete()
                return JsonResponse({"success": True, "message": "Unfollowed successfully."})

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

@user_login_required
def api_search(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    if search_type in ['all', 'books']:
        # Search books
        books = Book.objects.filter(
            Q(book_name__icontains=query) |
            Q(author_id__name__icontains=query) |
            Q(genre__icontains=query)
        ).select_related('author_id').distinct()[:5]
        
        for book in books:
            results.append({
                'title': book.book_name,
                'subtitle': f"by {book.author_id.name} • {book.genre}",
                'image': book.image.url,
                'url': reverse('book', args=[book.pk]),
                'type': 'book'
            })
    
    if search_type in ['all', 'authors']:
        # Search authors
        authors = Author.objects.filter(
            Q(name__icontains=query) |
            Q(bio__icontains=query)
        ).distinct()[:5]
        
        for author in authors:
            results.append({
                'title': author.name,
                'subtitle': author.bio[:100] + '...' if author.bio else 'Author',
                'image': author.author_image.url,
                'url': reverse('author', args=[author.pk]),
                'type': 'author'
            })
    
    if search_type in ['all', 'genres']:
        # Search genres (unique genres from books)
        genres = Book.objects.filter(
            genre__icontains=query
        ).values('genre').distinct()[:5]
        
        for genre in genres:
            # Get a representative book for the genre
            sample_book = Book.objects.filter(genre__iexact=genre['genre']).first()
            if sample_book:
                results.append({
                    'title': genre['genre'],
                    'subtitle': f"{Book.objects.filter(genre__iexact=genre['genre']).count()} books",
                    'image': sample_book.image.url,
                    'url': f"/search?genre={genre['genre']}",
                    'type': 'genre'
                })
    
    # Sort results by relevance (exact matches first)
    results.sort(key=lambda x: (
        not x['title'].lower().startswith(query.lower()),  # Exact start matches first
        not query.lower() in x['title'].lower(),           # Contains matches second
        x['title'].lower()                                 # Alphabetical otherwise
    ))
    
    return JsonResponse({'results': results[:10]})  # Limit to top 10 results total
>>>>>>> Stashed changes
