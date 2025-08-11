from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.db import transaction
from django.db.models import Avg, Q, Count, Sum, FloatField, ExpressionWrapper
from django.utils import timezone
from django.core.files.base import File
from django.conf import settings
from django.db import models
from datetime import datetime, timedelta
from urllib.parse import unquote
import json
import csv
import os
import logging
import pandas as pd
from functools import wraps

from .models import Cuser, Book, Author, Review, FollowAuthor, RecentSearch, ReadingStatus
from .recommendation_model import bot, df


logger = logging.getLogger(__name__)

def user_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if admin is trying to access user pages
        if request.session.get('is_admin'):
            messages.error(request, 'Please log out of admin panel to access user pages')
            return redirect('admin_dashboard')
        # List of views that don't require authentication
        public_views = ['book', 'author', 'search', 'trending_searches', 'index']
        
        # Get the view name from the function
        view_name = view_func.__name__
        
        # Allow access to public views without authentication
        if view_name in public_views:
            return view_func(request, *args, **kwargs)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Store the requested URL in session for redirect after login
            request.session['next'] = request.get_full_path()
            return redirect('signin')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@user_login_required
def index(request):
    # Handle guest user
    if request.GET.get('guest') == 'true' and not request.user.is_authenticated:
        # Get popular books (books with highest average rating and minimum 3 reviews)
        popular_books = Book.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            num_reviews=Count('reviews')
        ).filter(
            num_reviews__gte=3
        ).order_by('-avg_rating')[:8]

        # Get new books (added in the last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_books = Book.objects.all().order_by('-created_at')[:6]

        context = {
            'popular_books': popular_books,
            'new_books': new_books,
            'is_guest': True
        }
        
        return render(request, 'index.html', context)

    # Regular authenticated user view...
    followed_authors = Author.objects.filter(followers__follower=request.user)
   # print(followed_authors)
    # Get recent reviews from users following the same authors
    recent_reviews = Review.objects.filter(
        Q(book_id__author_id__in=followed_authors) |  # Reviews of followed authors' books
        Q(user_id__in=User.objects.filter(following__following__in=followed_authors))  # Reviews by users following same authors
    ).select_related(
        'user_id',
        'book_id',
        'book_id__author_id',
        'user_id__cuser'
    ).order_by('-created_at')[:30]

    # Get popular books (books with highest average rating and minimum 3 reviews)
    popular_books = Book.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        num_reviews=Count('reviews')
    ).filter(
        num_reviews__gte=3
    ).order_by('-avg_rating')[:8]
   # print(request.user)
    # Get new books (added in the last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)

# Fetch the 10 most recently added books from the last 30 days
    new_books = Book.objects.all().order_by('-created_at')[:8]  # Order by newest first and limit to 10

    # Get followed authors' recent books
    followed_books = Book.objects.filter(
        author_id__in=followed_authors
    ).order_by('-reviews__created_at').distinct()[:5]
   # print(new_books)
    context = {
        'recent_reviews': recent_reviews,
        'popular_books': popular_books,
        'new_books': new_books,
        'followed_authors': followed_authors,
        'followed_books': followed_books,
    }
    
    return render(request, 'index.html', context)

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
        image = request.FILES.get('user_image')  # Handle image upload

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
            user_image=image,
            email = email
        )
        cuser.set_password(password1)
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            with transaction.atomic():
                # Check if the user is admin
                if username == 'admin' and password == '1234':
                    # Set a session variable to indicate admin login
                    request.session['is_admin'] = True
                    return redirect('/myadmin/dashboard/')

                # Authenticate regular users
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
                    # Redirect to stored 'next' URL if it exists
                    next_url = request.session.get('next')
                    if next_url:
                        del request.session['next']
                        return redirect(next_url)
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
     

@user_login_required
def logout(request):
    try:
        with transaction.atomic():
            auth.logout(request)
            return redirect('signin')
    except Exception as e:
        messages.error(request, 'An error occurred during logout. Please try again.')
        return redirect('index')


@user_login_required
def search(request):
    results = Book.objects.all()

    # Get search parameters
    book_name = request.GET.get('book_name', '').strip()
    author_name = request.GET.get('author', '').strip()
    genre = request.GET.get('genre', '').strip()

    # Check if any parameters were submitted but all are empty
    if request.GET and not any([book_name, author_name, genre]):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No search parameters provided'}, status=400)
        messages.error(request, 'Please fill at least one search parameter')
        return render(request, 'search.html', {'results': None})

    # If any search parameter is provided
    if any([book_name, author_name, genre]):
        query = Q()
        if book_name:
            query &= Q(book_name__icontains=book_name)
        if author_name:
            query &= Q(author_id__name__icontains=author_name)
        if genre:
            query &= Q(genre__icontains=genre)

        results = results.filter(query).order_by('-created_at')
        try:
            if request.user.is_authenticated:
                user = request.user
                for book in results[:50]:
                    with transaction.atomic():
                        obj, created = RecentSearch.objects.get_or_create(
                            user=user,
                            book=book,
                            defaults={'search_count': 1, 'created_at': timezone.now()}
                        )
                        if not created:
                            obj.search_count += 1
                            obj.created_at = timezone.now()
                            obj.save()
        except Exception as e:
            print(f"Error updating recent searches: {e}")
    else:
        return render(request, 'search.html', {'results': None})

    paginator = Paginator(results, 10)  # Increased items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        books_data = [{
            'book_id': book.pk,
            'book_name': book.book_name,
            'image': book.image.url if book.image else '',
            'author_id': book.author_id.pk,
            'author_name': book.author_id.name,
            'genre': book.genre,
            'avg_rating': book.average_rating(),
            'total_ratings': book.reviews.count(),
        } for book in page_obj]
        return JsonResponse({
            'books': books_data, 
            'has_next': page_obj.has_next(),
            'total_results': results.count()
        })

    return render(request, 'search.html', {
        'results': page_obj,
        'total_results': results.count() if results else 0
    })


@user_login_required
def trending_searches(request):
    # Annotate each book with total search_count and unique user count, then calculate average_count
    trending = (
        RecentSearch.objects
        .values('book')
        .annotate(
            total_search_count=Sum('search_count'),
            unique_user_count=Count('user', distinct=True),
            average_count=ExpressionWrapper(
                Sum('search_count') / Count('user', distinct=True),
                output_field=FloatField()
            )
        )
        .order_by('-average_count', '-total_search_count')[:50]
    )
    # Get the book IDs in order
    book_ids = [item['book'] for item in trending]
    # Fetch book objects and preserve order
    books = list(Book.objects.filter(pk__in=book_ids))
    books_dict = {book.pk: book for book in books}
    # Prepare the trending list in the correct order
    trending_books = [books_dict[book_id] for book_id in book_ids if book_id in books_dict]

    paginator = Paginator(trending_books, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        books_data = [{
            'book_id': book.pk,
            'book_name': book.book_name,
            'image': book.image.url if book.image else '',
            'author_id': book.author_id.pk,
            'author_name': book.author_id.name,
            'genre': book.genre,
            'avg_rating': book.average_rating(),
            'total_ratings': book.reviews.count(),
        } for book in page_obj]
        return JsonResponse({'books': books_data, 'has_next': page_obj.has_next()})

    return render(request, 'search.html', {
        'results': page_obj,
        'is_trending': True
    })


@user_login_required
def author(request, pk):
    author = get_object_or_404(Author, pk=pk)
    books = Book.objects.filter(author_id=author).annotate(average_rating=Avg('reviews__rating')).order_by('-average_rating')
    # Fetch the followers count
    followers_count = FollowAuthor.objects.filter(following=author).count()
    # Check if the logged-in user is following the author
    if request.user.is_authenticated:
        is_following = FollowAuthor.objects.filter(following=author, follower=request.user).exists()
    else:
        is_following=False    
    return render(request, 'author_profile.html', {
        'author': author,
        'books': books[:4],  # Limit to the top 4 books
        'followers_count': followers_count,
        'is_following': is_following,
    })

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


@user_login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        cuser = user.cuser

        # Update user data
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        
        # Update cuser data
        cuser.user_date_of_birth = datetime.strptime(request.POST.get('date_of_birth'), '%Y-%m-%d').date()
        cuser.user_gender = request.POST.get('gender', cuser.user_gender)
        cuser.user_location = request.POST.get('location', cuser.user_location)
        
        # Handle profile image update
        image = request.FILES.get('user_image')
        if image:
            cuser.user_image = image
        
        user.save()
        cuser.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    # Get user's reviews
    user_reviews = Review.objects.filter(user_id=request.user).select_related('book_id').order_by('-created_at')
    
    # Get reading status counts
    reading_statuses = {
        'read_count': ReadingStatus.objects.filter(user=request.user, status='read').count(),
        'reading_count': ReadingStatus.objects.filter(user=request.user, status='reading').count(),
        'want_to_read_count': ReadingStatus.objects.filter(user=request.user, status='want_to_read').count(),
    }
    
    context = {
        'profile': request.user.cuser,
        'user_reviews': user_reviews,
        'reading_statuses': reading_statuses,
    }
    return render(request, 'profile.html', context)

@user_login_required
def book(request, pk):
   # print(f"Rendering book profile for book ID: {pk}")
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


@user_login_required
@csrf_exempt
def submit_review(request, book_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            review_text = data.get('review')
            rating = data.get('rating')

            if not review_text or not rating:
                return JsonResponse({'success': False, 'message': 'Review and rating are required.'}, status=400)

            book = get_object_or_404(Book, pk=book_id)
            user = request.user

            # Check if user has already reviewed this book
            existing_review = Review.objects.filter(book_id=book, user_id=user).first()
            
            if existing_review:
                # Update existing review
                existing_review.review_text = review_text
                existing_review.rating = int(rating)
                existing_review.save()
                message = 'Review updated successfully!'
            else:
                # Create new review
                Review.objects.create(
                    book_id=book,
                    user_id=user,
                    review_text=review_text,
                    rating=int(rating)
                )
                message = 'Review submitted successfully!'

            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)




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
       # print(f"User Input: {user_input}")  # Debugging

        if not user_input:
            return JsonResponse({"response": "Please provide a book title or author name for recommendations."})

        # Search in the dataset
        filtered_books = df[
            (df['Title'].str.lower().str.contains(user_input)) | 
            (df['Author'].str.lower().str.contains(user_input))|
            (df['Genres'].str.lower().str.contains(user_input))
        ]
        #print(f"Filtered Books: {filtered_books}")  # Debugging

        if filtered_books.empty:
            return JsonResponse({"response": f"Sorry, I couldn't find any books matching '{user_input}'."})

        # Use the first matching book's ID for recommendations
        book_id = filtered_books.iloc[0]['Book_ID']
       # print(f"Selected Book ID: {book_id}")  # Debugging

        # recommendations = content_based_recommendations(book_id=book_id, n=5)
        if request.user.is_authenticated:
            recommendations = bot.recommend(user_id=request.user.id, book_id=book_id, n=5)
        else:
            recommendations = bot.recommend(book_id=book_id, n=5)

        # recommendations = bot.recommend(user_id=request.user.id, book_id=book_id, n=5)
        #recommendations = bot.recommend(book_id=book_id, n=5)
        #recommendations = bot.recommend(book_id=book_id, n=5)
        recommended_books = recommendations.to_dict(orient='records')
        
        # Create a list to store recommendations with database IDs
        final_recommendations = []
        
        for book in recommended_books:
            # Try to find the corresponding book in your database
            try:
                db_book = Book.objects.get(book_name__iexact=book['Title'])
                logger.info(f"Found match: Dataset title '{book['Title']}' -> DB book ID {db_book.pk}")
                final_recommendations.append({
                    'Title': book['Title'],
                    'Author': book['Author'],
                    'Genres': book['Genres'],
                    'Book_ID': db_book.pk,  # Use the database book ID instead of dataset ID
                    'Image': db_book.image.url if db_book.image else None
                })
            except Book.DoesNotExist:
                logger.warning(f"No match found in database for book: {book['Title']}")
                continue
            except Book.MultipleObjectsReturned:
                # If multiple books found, use the first one
                db_book = Book.objects.filter(book_name__iexact=book['Title']).first()
                final_recommendations.append({
                    'Title': book['Title'],
                    'Author': book['Author'],
                    'Genres': book['Genres'],
                    'Book_ID': db_book.pk,
                    'Image': db_book.image.url if db_book.image else None
                })

        return JsonResponse({
            "response": f"Here are some book recommendations based on '{filtered_books.iloc[0]['Title']}' by {filtered_books.iloc[0]['Author']}:",
            "recommendations": final_recommendations
        })

    return JsonResponse({"response": "Welcome to the Book Recommendation Chatbot!"})



def chatbot_page(request):
    return render(request, 'chatbot.html')


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

#@user_login_required
def api_search(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    updated_books = []
    now = timezone.now()
    
    if search_type in ['all', 'books']:
        # Search books
        books = Book.objects.filter(
            Q(book_name__icontains=query) |
            Q(author_id__name__icontains=query) |
            Q(genre__icontains=query)
        ).select_related('author_id').distinct()[:5]
        # Update search_count and created_at for found books
        for book in books:
           # Book.objects.filter(pk=book.pk).update(search_count=models.F('search_count') + 1, created_at=now)
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
                'type': 'author',
             
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
                    'type': 'genre',
                  
                })
    
    # Sort results by relevance (exact matches first)
    results.sort(key=lambda x: (
        not x['title'].lower().startswith(query.lower()),  # Exact start matches first
        not query.lower() in x['title'].lower(),           # Contains matches second
        x['title'].lower()                                 # Alphabetical otherwise
    ))
    
    return JsonResponse({'results': results[:10]})  # Limit to top 10 results total

def parse_date_manually(date_str):
    try:
       # print(f"Parsing date: {date_str}")
        # Clean the string
        date_str = date_str.strip().replace('\n', '').replace('  ', ' ')
        
        # Split by comma to separate year from month and day
        main_part, year = date_str.rsplit(',', 1)
        year = year.strip()
        #print(f"Year: {year}")
        # Split the main part to get month and day
        month, day = main_part.rsplit(' ', 1)
        month = month.strip()
        day = day.strip()
        
        # Convert month name to number
        month_dict = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        month_num = month_dict[month]
        
        # Format the date as YYYY-MM-DD
        formatted_date = f"{year}-{month_num}-{day.zfill(2)}"
        #print(f"Formatted date: {formatted_date}")
        return formatted_date
    
    except Exception as e:
        #print(f"Error parsing date '{date_str}': {str(e)}")
        return None
        
@user_login_required
@csrf_exempt
def update_reading_status(request, book_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            status = data.get('status')

            book = get_object_or_404(Book, pk=book_id)
            user = request.user

            if status == 'remove':
                ReadingStatus.objects.filter(user=user, book=book).delete()
                return JsonResponse({'success': True, 'message': 'Book removed from your reading list'})

            if not status or status not in [choice[0] for choice in ReadingStatus.STATUS_CHOICES]:
                return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

            reading_status, created = ReadingStatus.objects.update_or_create(
                user=user,
                book=book,
                defaults={'status': status}
            )

            return JsonResponse({
                'success': True,
                'message': f'Status updated to {reading_status.get_status_display()}',
                'status': reading_status.status
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@user_login_required
def get_reading_status(request, book_id):
    try:
        book = get_object_or_404(Book, pk=book_id)
        reading_status = ReadingStatus.objects.filter(user=request.user, book=book).first()
        
        return JsonResponse({
            'success': True,
            'status': reading_status.status if reading_status else None
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@user_login_required
def reading_list(request, username=None):
    # If username is provided, show that user's reading list
    # Otherwise show the logged-in user's reading list
    if username:
        target_user = get_object_or_404(User, username=username)
    else:
        target_user = request.user

    # Get all reading statuses for the target user
    reading_statuses = ReadingStatus.objects.filter(user=target_user).select_related('book', 'book__author_id')
    
    # Group by status
    read_books = reading_statuses.filter(status='read')
    reading_books = reading_statuses.filter(status='reading')
    want_to_read_books = reading_statuses.filter(status='want_to_read')
    
    context = {
        'read_books': read_books,
        'reading_books': reading_books,
        'want_to_read_books': want_to_read_books,
        'viewed_user': target_user,
        'is_own_list': target_user == request.user
    }
    
    return render(request, 'reading_list.html', context)

@user_login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    
    # Get user's reviews
    user_reviews = Review.objects.filter(user_id=user).select_related('book_id').order_by('-created_at')
    
    # Get reading status counts
    reading_statuses = {
        'read_count': ReadingStatus.objects.filter(user=user, status='read').count(),
        'reading_count': ReadingStatus.objects.filter(user=user, status='reading').count(),
        'want_to_read_count': ReadingStatus.objects.filter(user=user, status='want_to_read').count(),
    }
    
    context = {
        'profile': user.cuser,
        'viewed_user': user,
        'user_reviews': user_reviews,
        'reading_statuses': reading_statuses,
    }
    return render(request, 'profile.html', context)





        