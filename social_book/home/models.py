from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
# Custom User Model

class Cuser(models.Model):
    user_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    user_name = models.CharField(max_length=255,unique=True)
    user_date_of_birth = models.DateField()
    user_gender = models.CharField(max_length=10)  # Example: 'Male', 'Female', 'Other'
    user_location = models.CharField(max_length=255)
    user_image = models.ImageField(upload_to='user_images', default='blank-profile-picture.png')
    email = models.EmailField(max_length=255, unique=True)
<<<<<<< Updated upstream
    password = models.CharField(max_length=255)  # Plain password field (will be hashed before saving)
=======
    password = models.CharField(max_length=255)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(null=True, blank=True)
    banned_at = models.DateTimeField(null=True, blank=True)
>>>>>>> Stashed changes

    def set_password(self, raw_password):
        """Hashes the password before saving it to the database."""
        self.password = make_password(raw_password)  # Hash the password before storing it

    def check_password(self, raw_password):
        """Checks if the entered password matches the stored hashed password."""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)  # Verify the password

    def __str__(self):
        return self.user_name


# Profile Model


# Author Model
class Author(models.Model):
    author_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    name = models.CharField(max_length=255)  # Author's name
    bio = models.TextField(blank=True, null=True)  # Author's biography (optional)
    date_of_birth = models.DateField(blank=True, null=True)  # Author's date of birth (optional)
    author_image = models.ImageField(upload_to='author_images', default='blank-profile-picture.png')

    def __str__(self):
        return self.name


# Book Model
class Book(models.Model):
    book_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    book_name = models.CharField(max_length=255)  # Book name
    author_id = models.ForeignKey(Author, on_delete=models.CASCADE)  # Foreign key to Author model
    genre = models.CharField(max_length=100, default='Unknown')  # Genre of the book
    image = models.ImageField(upload_to='book_images', default='blank-profile-picture.png')  # Image of the book
    created_at = models.DateTimeField(auto_now_add=True)  # New field

    def __str__(self):
        return self.book_name
    
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    book_id = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)  # Corrected to 'User' from 'auth.User'
    review_text = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review for {self.book.book_name} by {self.user.user_name}'
