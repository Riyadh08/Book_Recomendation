# 📚 Social Book Recommendation Platform

A comprehensive Django-based social book recommendation platform that combines intelligent AI recommendations with social networking features for book lovers.

## 🌟 Key Features

### 🔐 User Authentication & Profiles
- **User Registration & Login**: Secure authentication system with custom user profiles
- **Profile Management**: Users can update their profile information including:
  - Profile picture upload
  - Date of birth, gender, and location
  - View reading statistics (books read, currently reading, want to read)
- **User Profiles**: View other users' profiles and their reading activity
- **Account Management**: Admin can ban/unban users with reason tracking

### 📖 Book Management
- **Book Catalog**: Comprehensive book database with:
  - Book titles, authors, genres
  - Book cover images
  - Marketing/purchase links
  - Creation timestamps
- **Book Profiles**: Detailed book pages showing:
  - Average ratings and total review count
  - All user reviews with pagination
  - Reading status options
  - Purchase links

### ✍️ Reviews & Ratings System
- **Write Reviews**: Users can submit reviews with ratings (1-5 stars)
- **Update Reviews**: Edit existing reviews for books
- **Review Display**: 
  - Most recent review highlighted
  - Paginated review lists
  - User profile pictures in reviews
- **Rating Aggregation**: Automatic calculation of average ratings per book

### 👤 Author Management
- **Author Profiles**: Detailed author pages featuring:
  - Author biography
  - Date of birth and death
  - Author profile images
  - List of books by the author (sorted by rating)
  - Follower count
- **Follow Authors**: Users can follow their favorite authors
- **Author Following**: See books from followed authors on the homepage

### 🔍 Advanced Search Functionality
- **Multi-Criteria Search**: Search by:
  - Book name
  - Author name
  - Genre
- **Real-time Search API**: AJAX-powered search with instant results
- **Search History**: Tracks recent searches per user
- **Trending Searches**: Discover popular books based on search analytics
- **Search Analytics**: Tracks search counts and user engagement

### 📚 Reading Lists
- **Personal Reading Lists**: Organize books into three categories:
  - **Read**: Books you've completed
  - **Currently Reading**: Books in progress
  - **Want to Read**: Books on your wishlist
- **Public Reading Lists**: View other users' reading lists
- **Status Management**: Easy update/remove functionality for reading status

### 🤖 AI-Powered Recommendation Chatbot
- **Hybrid Recommendation System**: Combines two advanced techniques:
  - **Content-Based Filtering**: Uses TF-IDF vectorization and cosine similarity
  - **Collaborative Filtering**: Matrix factorization (SVD) for user-based recommendations
- **Intelligent Chatbot**: Interactive chatbot that:
  - Provides book recommendations based on book titles, authors, or genres
  - Answers questions about genres, authors, and ratings
  - Searches the book database intelligently
- **Personalized Recommendations**: 
  - User-specific recommendations when logged in
  - General recommendations for guests
  - Fallback mechanisms for robust performance

### 🏠 Personalized Homepage
- **For Authenticated Users**:
  - Recent reviews from followed authors
  - Popular books (highest rated with minimum reviews)
  - New books (recently added)
  - Books from followed authors
- **For Guests**:
  - Popular books showcase
  - New books section
  - Guest-friendly browsing

### 👨‍💼 Admin Panel
- **Comprehensive Dashboard**: Overview of:
  - Total users, books, authors, and reviews
  - Recent reviews
  - Popular books
- **Book Management**:
  - Add, edit, and manage books
  - Upload book images
  - Set marketing links
- **Author Management**:
  - Add, edit, and delete authors
  - Upload author images
  - Manage author biographies
- **User Management**:
  - View all users
  - Ban/unban users with reason tracking
  - View user statistics

### 🎨 User Interface
- **Modern Design**: Clean and responsive UI
- **AJAX Integration**: Smooth, dynamic interactions
- **Pagination**: Efficient handling of large datasets
- **Image Uploads**: Support for book covers, author images, and user profiles

## 🛠️ Technology Stack

- **Backend**: Django 3.2+
- **Database**: SQLite3
- **Machine Learning**:
  - scikit-learn (TF-IDF, Cosine Similarity, SVD)
  - pandas & numpy for data processing
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Tailwind CSS, UIKit

## 📁 Project Structure

```
social_book/
├── home/                    # Main application
│   ├── models.py           # Database models (User, Book, Author, Review, etc.)
│   ├── views.py            # View functions
│   ├── admin_views.py      # Admin panel views
│   ├── recommendation_model.py  # AI recommendation system
│   └── urls.py             # URL routing
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User-uploaded files
└── manage.py              # Django management script
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd social_book
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django pandas numpy scikit-learn
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main site: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/myadmin/`
     - Default credentials: `admin` / `1234`

## 📊 Database Models

- **Cuser**: Extended user profile with additional information
- **Author**: Author information and metadata
- **Book**: Book catalog with ratings and reviews
- **Review**: User reviews and ratings for books
- **FollowAuthor**: User-author following relationships
- **RecentSearch**: Search history and analytics
- **ReadingStatus**: User reading list management

## 🎯 Key Functionalities

### For Users
- ✅ Sign up and create profile
- ✅ Search books, authors, and genres
- ✅ View book and author profiles
- ✅ Write and edit reviews
- ✅ Rate books (1-5 stars)
- ✅ Follow favorite authors
- ✅ Manage reading lists
- ✅ Get AI-powered book recommendations
- ✅ View trending books
- ✅ Browse other users' profiles and reading lists

### For Admins
- ✅ Manage books (add, edit, delete)
- ✅ Manage authors (add, edit, delete)
- ✅ Manage users (view, ban, unban)
- ✅ View platform statistics
- ✅ Monitor recent activity

## 🔧 Configuration

The project uses Django's default settings. Key configurations in `social_book/settings.py`:
- Database: SQLite3 (can be changed to PostgreSQL/MySQL)
- Media files: Stored in `media/` directory
- Static files: Served from `static/` directory

## 📝 Notes

- The recommendation system uses a CSV dataset located at `static/assets/dataset/Final_Dataset.csv`
- Admin credentials are hardcoded (should be changed for production)
- The platform supports both authenticated and guest browsing

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Developed as a social book recommendation platform combining machine learning with social networking features.

---

**Happy Reading! 📖✨**

