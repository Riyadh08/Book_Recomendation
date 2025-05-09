# Step 1: Import Libraries
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import os
import re

# Step 2: Load and Clean the Dataset
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset_path = os.path.join(BASE_DIR, 'static', 'assets', 'dataset', 'Final_Dataset.csv')
df = pd.read_csv(dataset_path)

# Step 3: Clean and Combine Content Fields with better handling
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

# First remove exact duplicates from dataset
df = df.drop_duplicates(subset=['Title', 'Author'], keep='first')

df['Clean_Title'] = df['Title'].apply(clean_text)
df['Clean_Author'] = df['Author'].apply(clean_text)
df['Clean_Genres'] = df['Genres'].apply(lambda x: clean_text(x.replace('|', ' ')))

# More balanced weighted combination
df['Content'] = (
    df['Clean_Title'] * 3 + ' ' +  # Highest weight to title
    df['Clean_Author'] * 2 + ' ' +  # Medium weight to author
    df['Clean_Genres']  # Lower weight to genres
)

# Step 4: TF-IDF Vectorization with adjusted parameters
tfidf = TfidfVectorizer(
    stop_words='english',
    ngram_range=(1, 3),  # Wider ngram range to capture more context
    min_df=3,  # Higher min_df to filter out rare terms
    max_features=10000  # Limit features to most important ones
)
tfidf_matrix = tfidf.fit_transform(df['Content'])

# Step 5: Build Nearest Neighbors Model
knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=50)  # Larger neighborhood
knn.fit(tfidf_matrix)

def content_based_recommendations(book_id, n=5):
    try:
        # Convert book_id to string if needed
        book_id = str(book_id)
        
        # Validate book exists
        if book_id not in df['Book_ID'].values:
            print(f"Book ID {book_id} not found. Trying title search...")
            return get_fallback_recommendations(n)
        
        book_index = df[df['Book_ID'] == book_id].index[0]
        
        # Special character handling in title matching
        current_title = clean_text(df.iloc[book_index]['Title'])
        if not current_title or current_title.strip() == "":
            print("Invalid title format, using fallback")
            return get_fallback_recommendations(n)
        
        # Safe similarity calculation
        cosine_sim = cosine_similarity(tfidf_matrix[book_index:book_index+1], tfidf_matrix).flatten()
        
        # Get recommendations with similarity threshold
        recommendations = []
        seen_titles = {current_title}
        
        for idx in cosine_sim.argsort()[::-1]:
            if len(recommendations) >= n:
                break
            candidate_title = clean_text(df.iloc[idx]['Title'])
            similarity = cosine_sim[idx]
            
            if (idx != book_index and 
                candidate_title not in seen_titles and 
                similarity > 0.1):  # Minimum similarity threshold
                seen_titles.add(candidate_title)
                recommendations.append(idx)
        
        if not recommendations:
            print("No sufficiently similar books found, using fallback")
            return get_fallback_recommendations(n)
            
        result = df.iloc[recommendations][['Book_ID', 'Title', 'Author', 'Genres']].copy()
        result['Similarity_Score'] = cosine_sim[recommendations]
        return result.reset_index(drop=True)
        
    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        return get_fallback_recommendations(n)

def get_fallback_recommendations(n=5):
    """Return popular books when specific recommendations fail"""
    return df.sample(n=n)[['Book_ID', 'Title', 'Author', 'Genres']]

def clean_text(text):
    """More robust text cleaning"""
    try:
        text = str(text)
        # Keep only letters, numbers and basic punctuation
        text = re.sub(r'[^\w\s.,!?\-]', '', text, flags=re.UNICODE)
        return text.lower().strip()
    except:
        return ""