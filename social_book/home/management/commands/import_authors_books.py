from django.core.management.base import BaseCommand
from home.models import Author, Book
from django.core.files import File
from django.conf import settings
import csv
import os
from datetime import datetime
from urllib.parse import unquote

class Command(BaseCommand):
    help = 'Import authors and books from final_author.csv'

    def handle(self, *args, **kwargs):
        # Dictionary to keep track of author IDs
        author_map = {}  # {author_name: author_id}
        current_author_id = 1  # For auto-incrementing author IDs

        csv_file_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'dataset', 'final_author.csv')

        # First pass: Process authors
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                author_name = row['Author Name'].strip()
                if not author_name or author_name.upper() == 'N/A':
                    continue

                if author_name not in author_map:
                    # Create new author
                    try:
                        # Parse dates if available
                        birth_date = None
                        death_date = None
                        if row.get('Birth Date'):
                            birth_date = datetime.strptime(row['Birth Date'], '%d-%b-%y').date()
                        if row.get('Death Date'):
                            death_date = datetime.strptime(row['Death Date'], '%d-%b-%y').date()

                        # Create author instance
                        author = Author.objects.create(
                            author_id=current_author_id,
                            name=author_name,
                            date_of_birth=birth_date,
                            date_of_death=death_date,
                            bio=row.get('Biography', '')
                        )

                        # Handle author image
                        image_url = row.get('Author Image URL', '')
                        if image_url:
                            # Extract filename from URL
                            image_filename = unquote(image_url.split('/')[-1])
                            image_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'images', 'authors', image_filename)
                            if os.path.exists(image_path):
                                with open(image_path, 'rb') as img_file:
                                    author.author_image.save(image_filename, File(img_file), save=True)

                        author_map[author_name] = current_author_id
                        current_author_id += 1
                        self.stdout.write(f"Created author: {author_name}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error creating author {author_name}: {str(e)}"))

        # Second pass: Process books
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    author_name = row['Author Name'].strip()
                    if not author_name or author_name.upper() == 'N/A':
                        continue

                    author_id = author_map.get(author_name)
                    if not author_id:
                        self.stdout.write(self.style.WARNING(f"Skipping book: Author not found: {author_name}"))
                        continue

                    # Create book
                    book_name = row['Title'].strip()
                    if not Book.objects.filter(book_name=book_name, author_id_id=author_id).exists():
                        book = Book.objects.create(
                            book_name=book_name,
                            author_id_id=author_id,
                            genre=row.get('Genres', 'Unknown')
                        )

                        # Handle book image
                        image_url = row.get('URL_y', '')  # Assuming URL_y is the book image URL
                        if image_url:
                            image_filename = unquote(image_url.split('/')[-1])
                            image_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'images', 'books', image_filename)
                            if os.path.exists(image_path):
                                with open(image_path, 'rb') as img_file:
                                    book.image.save(image_filename, File(img_file), save=True)

                        self.stdout.write(f"Created book: {book_name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row: {str(e)}"))

        self.stdout.write(self.style.SUCCESS('Data import completed')) 