from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Author, Book, User, Cuser, Review
from django.db.models import Count, Avg
from django.core.paginator import Paginator
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.contrib import auth
from django.template import loader
from django.http import HttpResponse

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

def admin_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_login(request):
    # Clear any existing admin session
    if 'is_admin' in request.session:
        del request.session['is_admin']
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            with transaction.atomic():
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    request.session['is_admin'] = True
                    messages.success(request, 'Welcome to Admin Panel')
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Invalid admin credentials')
                    return render(request, 'admin/login.html')
                    
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'admin/login.html')
    
    return render(request, 'admin/login.html')

def admin_logout(request):
    if 'is_admin' in request.session:
        del request.session['is_admin']
    messages.success(request, 'Successfully logged out from admin panel')
    return redirect('signin')

def back_to_site(request):
    if 'is_admin' in request.session:
        del request.session['is_admin']
    return redirect('index')

@admin_login_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_books = Book.objects.count()
    total_authors = Author.objects.count()
    total_reviews = Review.objects.count()
    
    recent_reviews = Review.objects.select_related('user_id', 'book_id').order_by('-created_at')[:5]
    popular_books = Book.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).order_by('-review_count')[:5]
    
    context = {
        'total_users': total_users,
        'total_books': total_books,
        'total_authors': total_authors,
        'total_reviews': total_reviews,
        'recent_reviews': recent_reviews,
        'popular_books': popular_books,
    }
    return render(request, 'admin/dashboard.html', context)

@admin_login_required
def admin_books(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            book_id = request.POST.get('book_id')
            book = get_object_or_404(Book, book_id=book_id)
            book_name = book.book_name
            book.delete()
            messages.success(request, f'Book "{book_name}" has been deleted.')
            return redirect('admin_books')
            
        # Existing book creation/update code...
        book_id = request.POST.get('book_id')
        if book_id:
            book = get_object_or_404(Book, book_id=book_id)
        else:
            book = Book()
        
        book.book_name = request.POST.get('book_name')
        book.author_id = get_object_or_404(Author, author_id=request.POST.get('author_id'))
        book.genre = request.POST.get('genre')
        if 'image' in request.FILES:
            book.image = request.FILES['image']
        book.save()
        
        messages.success(request, 'Book saved successfully!')
        return redirect('admin_books')

    book_id = request.GET.get('edit')
    if book_id:
        # Show edit form
        book = get_object_or_404(Book, book_id=book_id)
        authors = Author.objects.all()
        return render(request, 'admin/book_form.html', {'book': book, 'authors': authors})
    
    if request.GET.get('new'):
        # Show new book form
        authors = Author.objects.all()
        return render(request, 'admin/book_form.html', {'authors': authors})

    # Show book list
    books = Book.objects.select_related('author_id').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/books.html', {'books': page_obj})

@admin_login_required
def admin_authors(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            author_id = request.POST.get('author_id')
            author = get_object_or_404(Author, author_id=author_id)
            author_name = author.name
            author.delete()
            messages.success(request, f'Author "{author_name}" and all their books have been deleted.')
            return redirect('admin_authors')
            
        author_id = request.POST.get('author_id')
        if author_id:
            author = get_object_or_404(Author, author_id=author_id)
        else:
            author = Author()
        
        # Handle required field
        author.name = request.POST.get('name')
        
        # Handle optional date fields
        date_of_birth = request.POST.get('date_of_birth')
        date_of_death = request.POST.get('date_of_death')
        
        # Only set dates if they're provided
        author.date_of_birth = date_of_birth if date_of_birth else None
        author.date_of_death = date_of_death if date_of_death else None
        
        # Handle optional text field
        author.bio = request.POST.get('bio') or None
        
        # Handle optional image
        if 'author_image' in request.FILES:
            author.author_image = request.FILES['author_image']
        
        author.save()
        messages.success(request, 'Author saved successfully!')
        return redirect('admin_authors')

    author_id = request.GET.get('edit')
    if author_id:
        author = get_object_or_404(Author, author_id=author_id)
        return render(request, 'admin/author_form.html', {'author': author})
    
    if request.GET.get('new'):
        return render(request, 'admin/author_form.html')

    authors = Author.objects.annotate(
        book_count=Count('book'),
        avg_rating=Avg('book__reviews__rating')
    )
    
    paginator = Paginator(authors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/authors.html', {'authors': page_obj})

@admin_login_required
def admin_users(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'ban':
            user = get_object_or_404(User, id=user_id)
            
            # Check if trying to ban the current user
            if request.user.id == user.id:
                messages.error(request, 'You cannot ban yourself while logged in.')
                return redirect('admin_users')
                
            description = request.POST.get('description', '')
            
            # Update cuser
            cuser = user.cuser
            cuser.is_banned = True
            cuser.ban_reason = description
            cuser.banned_at = timezone.now()
            cuser.save()
            
            messages.success(request, f'User {user.username} has been banned.')
            return redirect('admin_users')
            
        elif action == 'unban':
            user = get_object_or_404(User, id=request.POST.get('user_id'))
            cuser = user.cuser
            cuser.is_banned = False
            cuser.ban_reason = None
            cuser.banned_at = None
            cuser.save()
            
            user.is_active = True
            user.save()
            
            messages.success(request, f'User has been unbanned.')
            return redirect('admin_users')
    
    users = User.objects.select_related('cuser').annotate(
        review_count=Count('review')
    )
    
    return render(request, 'admin/users.html', {
        'users': users,
        'current_user_id': request.user.id
    })

def admin_error_handler(request, exception=None):
    template = loader.get_template('admin/error.html')
    status = 500
    
    if isinstance(exception, HttpResponseForbidden):
        status = 403
        error_message = "Access Forbidden"
    elif type(exception).__name__ == 'Http404':
        status = 404
        error_message = "Page Not Found"
    else:
        error_message = "Server Error"
    
    context = {
        'error_code': status,
        'error_message': error_message
    }
    
    return HttpResponse(template.render(context, request), status=status) 