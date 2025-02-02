from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from .models import Cuser,Book,Author,Review,FollowAuthor
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Avg, Q, Count
from django.utils import timezone
from django.urls import reverse

@login_required(login_url='signin')
def index(request):
    # Get authors followed by the user
    followed_authors = Author.objects.filter(followers__follower=request.user)
    
    # Get recent reviews from users following the same authors
    recent_reviews = Review.objects.filter(
        Q(book_id__author_id__in=followed_authors) |  # Reviews of followed authors' books
        Q(user_id__in=User.objects.filter(following__following__in=followed_authors))  # Reviews by users following same authors
    ).select_related(
        'user_id',
        'book_id',
        'book_id__author_id',
        'user_id__cuser'
    ).order_by('-created_at')[:10]

    # Get popular books (books with highest average rating and minimum 3 reviews)
    popular_books = Book.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        num_reviews=Count('reviews')
    ).filter(
        num_reviews__gte=3
    ).order_by('-avg_rating')[:8]

    # Get new books (added in the last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_books = Book.objects.filter(
        reviews__created_at__gte=thirty_days_ago
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        num_reviews=Count('reviews')
    ).distinct().order_by('-reviews__created_at')[:8]

    # Get followed authors' recent books
    followed_books = Book.objects.filter(
        author_id__in=followed_authors
    ).order_by('-reviews__created_at').distinct()[:5]

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
    results = Book.objects.all()

    # Get search parameters
    book_name = request.GET.get('book_name', '').strip()
    author_name = request.GET.get('author', '').strip()
    genre = request.GET.get('genre', '').strip()

    query = Q()
    if book_name:
        query &= Q(book_name__icontains=book_name)
    if author_name:
        query &= Q(author_id__name__icontains=author_name)
    if genre:
        query &= Q(genre__icontains=genre)

    results = results.filter(query).annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')

    paginator = Paginator(results, 5)
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
            'avg_rating': book.avg_rating or 0,
            'total_ratings': book.reviews.count(),
        } for book in page_obj]
        return JsonResponse({'books': books_data, 'has_next': page_obj.has_next()})

    return render(request, 'search.html', {'results': page_obj})


from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required(login_url='signin')
def author(request, pk):
    author = get_object_or_404(Author, pk=pk)
    books = Book.objects.filter(author_id=author).annotate(average_rating=Avg('reviews__rating')).order_by('-average_rating')
    return render(request, 'author_profile.html', {'author': author, 'books': books[:4]})

@login_required(login_url='signin')
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



@login_required(login_url='signin')
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
        if 'user_image' in request.FILES:
            cuser.user_image = request.FILES['user_image']
        
        user.save()
        cuser.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    # Get user's reviews
    user_reviews = Review.objects.filter(user_id=request.user).select_related('book_id').order_by('-created_at')
    
    context = {
        'profile': request.user.cuser,
        'user_reviews': user_reviews,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def book(request, pk):
    print(f"Rendering book profile for book ID: {pk}")
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

@login_required
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

@login_required(login_url='signin')
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
