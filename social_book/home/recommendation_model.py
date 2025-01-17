# Step 1: Import Libraries
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors  # For efficient similarity search
from sklearn.metrics.pairwise import cosine_similarity
import os
# Step 2: Load the Dataset
# Replace 'your_file.csv' with your dataset file name
# Define the dataset path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_path = os.path.join(BASE_DIR, 'static', 'assets', 'dataset', 'Final_Dataset.csv')

# Load the dataset
df = pd.read_csv(dataset_path)

# Step 3: Handle Missing Values
# Drop rows where essential columns like Book_ID or Content are NaN
df = df.dropna(subset=['Book_ID'])

# Fill missing textual data with empty strings
df['Title'] = df['Title'].fillna('')
df['Author'] = df['Author'].fillna('')
df['Genres'] = df['Genres'].fillna('Unknown')

# Combine Title, Author, and Genres for text-based recommendations
df['Content'] = df['Title'] + " " + df['Author'] + " " + df['Genres']

# Step 4: Fit the TF-IDF model
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df['Content'])  # Sparse matrix

# Step 5: Build Nearest Neighbors Model (Memory-Efficient Option)
knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=len(df)) 
knn.fit(tfidf_matrix)

# Step 6: Define Recommendation Function
def content_based_recommendations(book_id, n=5):
    """
    Recommend similar but distinct books based on content similarity using TF-IDF and KNN.

    Args:
        book_id (int or str): The ID of the book for which to generate recommendations.
        n (int): The number of distinct recommendations to return.

    Returns:
        pd.DataFrame: A dataframe containing recommended books.
    """
    if book_id not in df['Book_ID'].values:
        print(f"Book ID {book_id} not found in the dataset.")
        return []
    
    # Find the index of the book in the dataframe
    book_index = df[df['Book_ID'] == book_id].index[0]
    
    # Get distances and indices of the top neighbors
    distances, indices = knn.kneighbors(tfidf_matrix[book_index], n_neighbors=len(df))  # Get all neighbors
    
    # Exclude the input book and filter for distinct recommendations
    recommended_indices = indices.flatten()[1:]  # Exclude the book itself
    recommendations = df.iloc[recommended_indices]
    recommendations = recommendations.drop_duplicates(subset='Book_ID').head(n)  # Ensure distinct books
    
    return recommendations[['Book_ID', 'Title', 'Author', 'Genres']]


book_id = 115030 # Replace with a valid Book_ID
recommendations = content_based_recommendations(book_id, n=5)

# print("Recommended Books:")
# print(recommendations)
