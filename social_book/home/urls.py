from django.urls import path
from . import views, admin_views

urlpatterns = [
    # Main site URLs
    path('', views.signin, name='signin'),  # Make signin the homepage
    path('home/', views.index, name='index'),  # Move index to /home/
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.search, name='search'),
    path('book/<int:pk>/', views.book, name='book'),
    path('author/<int:pk>/', views.author, name='author'),
    path('book/<int:book_id>/reviews', views.reviews_list, name='reviews_list'),
    path('submit-review/<int:book_id>/', views.submit_review, name='submit_review'),
<<<<<<< Updated upstream

=======
    path('author/<int:pk>/load-more-books/', views.load_more_books, name='load_more_books'),
    path('chatbot_page/', views.chatbot_page, name='chatbot_page'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path("follow-author/", views.follow_author, name="follow-author"),
    path('api/search/', views.api_search, name='api_search'),
    
    # Custom Admin URLs - make sure these are before other patterns
    path('myadmin/', admin_views.admin_login, name='admin_login'),
    path('myadmin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('myadmin/logout/', admin_views.admin_logout, name='admin_logout'),
    path('myadmin/books/', admin_views.admin_books, name='admin_books'),
    path('myadmin/authors/', admin_views.admin_authors, name='admin_authors'),
    path('myadmin/users/', admin_views.admin_users, name='admin_users'),
    path('myadmin/back-to-site/', admin_views.back_to_site, name='back_to_site'),
>>>>>>> Stashed changes
]

# Custom error handlers for admin section
handler403 = 'home.admin_views.admin_error_handler'
handler404 = 'home.admin_views.admin_error_handler'
handler500 = 'home.admin_views.admin_error_handler'
