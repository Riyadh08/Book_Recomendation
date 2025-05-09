from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.urls import reverse

from django.contrib.auth.models import User

# Custom Cuser Model
class Cuser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cuser", primary_key=True)
    user_date_of_birth = models.DateField()
    user_gender = models.CharField(max_length=10)  # Example: 'Male', 'Female', 'Other'
    user_location = models.CharField(max_length=255)
    user_image = models.ImageField(upload_to='user_images', default='blank-profile-picture.png')
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(null=True, blank=True)
    banned_at = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.user.username


# Author Model
class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    author_image = models.ImageField(upload_to='author_images', default='blank-profile-picture.png')

    def __str__(self):
        return self.name


# Book Model
class Book(models.Model):
    book_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    book_name = models.CharField(max_length=255)  # Book name
    author_id = models.ForeignKey(Author, on_delete=models.CASCADE)  # Foreign key to Author model
    genre = models.CharField(max_length=100, default='Unknown')  # Genre of the book
    image = models.ImageField(upload_to='book_images/', default='defalut_book_image.jpg')  # Image of the book
    created_at = models.DateTimeField(auto_now_add=True)  # New field
    marketing_link = models.URLField(
        max_length=500, 
        default='https://www.rokomari.com/book',
        help_text='Link to purchase the book (e.g., Rokomari)'
    )

    def average_rating(self):
        return self.reviews.aggregate(average=Avg('rating'))['average'] or 0

    def total_ratings(self):
        return self.reviews.count()
    
    def get_absolute_url(self): 
        return reverse('book', args=[self.pk])

    def __str__(self):
        return self.book_name
    
# Review Model
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    book_id = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)  # Corrected to 'User' from 'auth.User'
    review_text = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.book.book_name} by {self.user.user_name}'

from django.db import models
from django.contrib.auth.models import User
from .models import Author  # Assuming you have the Author model already

# FollowAuthor Model
class FollowAuthor(models.Model):
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(Author, related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # Prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.following.name}"

# RecentSearch Model
class RecentSearch(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    search_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def add_search_results(cls, books):
        for book in books:
            # Update existing entry if book already exists
            cls.objects.filter(book=book).delete()
            
            # Create new entry
            cls.objects.create(book=book)
            
            # Keep only the most recent 50 entries
            if cls.objects.count() > 50:
                # Delete the oldest entries beyond 50
                to_delete = cls.objects.order_by('-created_at')[50:]
                cls.objects.filter(id__in=to_delete).delete()

# ReadingStatus Model
class ReadingStatus(models.Model):
    STATUS_CHOICES = [
        ('read', 'Read'),
        ('reading', 'Currently Reading'),
        ('want_to_read', 'Want to Read'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_statuses')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reading_statuses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')  # Prevent duplicate entries
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.book_name} ({self.get_status_display()})"

