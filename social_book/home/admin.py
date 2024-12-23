from django import forms
from django.contrib import admin
from .models import Author, Book

# Custom form for Author to enhance the datepicker widget
class AuthorForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',  # HTML5 date input for native browser support
                'class': 'form-control',  # Add custom classes if needed
            }
        ),
        required=False  # Make it optional if needed
    )

    class Meta:
        model = Author
        fields = '__all__'


# Inline model for books to display in the Author admin interface
class BookInline(admin.TabularInline):
    model = Book
    extra = 1  # Number of empty book forms to display by default
    fields = ('book_name', 'genre', 'image')  # Fields to display in the inline form
    show_change_link = True  # Add a link to edit the book


# Register the Author model with enhancements
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    form = AuthorForm  # Use the custom form with enhanced datepicker
    list_display = ('name', 'date_of_birth', 'bio')  # Fields to display in the list view
    search_fields = ('name', 'bio')  # Searchable fields
    list_filter = ('date_of_birth',)  # Filters for the list view  # Inline books associated with the author
    ordering = ('name',)  # Default ordering by name
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'date_of_birth', 'bio')
        }),
        ('Image', {
            'fields': ('author_image',),
        }),
    )


# Register the Book model
@admin.register(Book)
class BookAdmin(admin.ModelAdmin): 
    list_display = ('book_name', 'author_id', 'genre')  # Fields to display in the admin list view
    search_fields = ('book_name', 'genre')  # Fields to include in the search box
    list_filter = ('genre',)  # Filters for the list view
    ordering = ('book_name',)  # Default ordering by book name
    fieldsets = (
        ('Book Information', {
            'fields': ('book_name', 'author_id', 'genre', 'image'),
        }),
    )
