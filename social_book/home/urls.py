from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.search, name='search'),
    path('book/<int:pk>/', views.book, name='book'),
    path('author/<int:pk>/', views.author, name='author'),
    path('book/<int:book_id>/reviews', views.reviews_list, name='reviews_list'),
    path('submit-review/<int:book_id>/', views.submit_review, name='submit_review'),
    path('author/<int:pk>/load-more-books/', views.load_more_books, name='load_more_books'), # New endpoint for loading more books
     path('chatbot_page/', views.chatbot_page, name='chatbot_page'),  # Render chatbot.html
    path('chatbot/', views.chatbot, name='chatbot'),  # Chatbot API

]
