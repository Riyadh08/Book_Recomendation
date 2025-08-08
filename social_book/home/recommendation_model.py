import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import re
import os

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
df['Clean_Genres'] = df['Genres'].apply(lambda x: clean_text(str(x).replace('|', ' ')))

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

# Build collaborative filtering model precompution using matrix factorization
user_item = df.pivot_table(index='User_ID', columns='Book_ID', values='Rating', fill_value=0)
user_ids = user_item.index.tolist()
book_ids = user_item.columns.tolist()
user_item_matrix = user_item.values
svd = TruncatedSVD(n_components=20, random_state=42)
user_factors = svd.fit_transform(user_item_matrix)
item_factors = svd.components_.T

#Step 5: Content based Similarity
def content_based_recommendations(book_id, n=5):
    """Original function interface - maintains compatibility with your existing views.py"""
    try:
        # Convert book_id to string if needed
        book_id = str(book_id)
        
        # Validate book exists
        if book_id not in df['Book_ID'].astype(str).values:
            print(f"Book ID {book_id} not found. Trying title search...")
            return get_fallback_recommendations(n)
        
        book_index = df[df['Book_ID'].astype(str) == book_id].index[0]
        
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

#Step 6: Collaborative filtering
def collaborative_recommendations(user_id, n=5):
    """Collaborative filtering recommendations"""
    try:
        if user_id not in user_ids:
            return get_fallback_recommendations(n)
        
        uidx = user_ids.index(user_id)
        preds = np.dot(user_factors[uidx], item_factors.T)
        unrated = user_item_matrix[uidx] == 0
        rec_idx = np.argsort(preds * unrated)[::-1][:n]
        
        recommendations = []
        for i in rec_idx:
            bookid = book_ids[i]
            book_matches = df[df['Book_ID'] == bookid]
            if not book_matches.empty:
                recommendations.append(book_matches.index[0])
        
        if recommendations:
            result = df.iloc[recommendations][['Book_ID', 'Title', 'Author', 'Genres']].copy()
            result['Predicted_Rating'] = preds[rec_idx[:len(recommendations)]]
            return result.reset_index(drop=True)
        else:
            return get_fallback_recommendations(n)
    except:
        return get_fallback_recommendations(n)

# Step 7:Combine both filtering technique
class HybridBookBot:
    """Enhanced class for chatbot functionality"""
    def __init__(self):
        # Use the global variables already initialized
        self.df = df
        self.tfidf_matrix = tfidf_matrix
        self.content_sim = cosine_similarity(tfidf_matrix)
        
        # Initialize QA pipeline with error handling
        try:
            from transformers import pipeline
            self.qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
        except Exception as e:
            print(f"Warning: Could not load QA pipeline: {e}")
            self.qa_pipeline = None

    def recommend(self, user_id=None, book_id=None, n=5):
        """Hybrid recommendations with comprehensive fallbacks"""
        try:
            results = []
            
            # Content-based recommendations (if book_id provided)
            if book_id is not None:
                try:
                    content_recs = content_based_recommendations(book_id, n)
                    if not content_recs.empty:
                        for _, row in content_recs.iterrows():
                            results.append({
                                'Book_ID': row['Book_ID'],
                                'Title': row['Title'],
                                'Author': row['Author'],
                                'Genres': row['Genres'],
                                'Type': 'content',
                                'Score': row.get('Similarity_Score', 0)
                            })
                except Exception as e:
                    print(f"Content-based failed: {e}")
            
            # Collaborative filtering (if user_id provided)
            if user_id is not None:
                try:
                    collab_recs = collaborative_recommendations(user_id, n)
                    if not collab_recs.empty:
                        for _, row in collab_recs.iterrows():
                            results.append({
                                'Book_ID': row['Book_ID'],
                                'Title': row['Title'],
                                'Author': row['Author'],
                                'Genres': row['Genres'],
                                'Type': 'collaborative',
                                'Score': row.get('Predicted_Rating', 0)
                            })
                except Exception as e:
                    print(f"Collaborative failed: {e}")
            
            # If we have results, remove duplicates
            if results:
                results_df = pd.DataFrame(results)
                results_df = results_df.drop_duplicates(subset=['Book_ID'])
            else:
                results_df = pd.DataFrame()
            
            # Fallback if not enough results
            if len(results_df) < n:
                needed = n - len(results_df)
                try:
                    fallback = get_fallback_recommendations(needed)
                    for _, row in fallback.iterrows():
                        results_df = pd.concat([
                            results_df,
                            pd.DataFrame([{
                                'Book_ID': row['Book_ID'],
                                'Title': row['Title'],
                                'Author': row['Author'],
                                'Genres': row['Genres'],
                                'Type': 'fallback',
                                'Score': 0
                            }])
                        ], ignore_index=True)
                except Exception as e:
                    print(f"Fallback failed: {e}")
                    # Ultimate fallback - random sample
                    if len(results_df) < n:
                        sample = self.df.sample(n=min(5, len(self.df)))[['Book_ID', 'Title', 'Author', 'Genres']]
                        for _, row in sample.iterrows():
                            results_df = pd.concat([
                                results_df,
                                pd.DataFrame([{
                                    'Book_ID': row['Book_ID'],
                                    'Title': row['Title'],
                                    'Author': row['Author'],
                                    'Genres': row['Genres'],
                                    'Type': 'emergency_fallback',
                                    'Score': 0
                                }])
                            ], ignore_index=True)
            
            # Sort by type priority and score
            type_order = {'content': 0, 'collaborative': 1, 'fallback': 2, 'emergency_fallback': 3}
            results_df['type_rank'] = results_df['Type'].map(type_order)
            results_df = results_df.sort_values(['type_rank', 'Score'], ascending=[True, False])
            
            return results_df.head(n).drop(columns=['type_rank'])

        except Exception as e:
            print(f"Critical error in recommend(): {e}")
            # Final safety net
            return get_fallback_recommendations(n)
    
    def answer_general(self, question):
        q = question.lower()
        
        if "genre" in q:
            all_genres = []
            for genre_str in self.df['Genres'].dropna():
                genres = re.split(r'[,|]', str(genre_str))
                all_genres.extend([g.strip() for g in genres if g.strip()])
            
            genre_counts = pd.Series(all_genres).value_counts().head(5)
            return "Top genres: " + ", ".join(genre_counts.index)
            
        elif "author" in q:
            return "Top authors: " + ", ".join(self.df['Author'].value_counts().head(5).index)
            
        elif "rating" in q or "best" in q:
            top = self.df.groupby('Title')['Rating'].mean().sort_values(ascending=False).head(5)
            return "Top rated books: " + ", ".join(top.index)
            
        else:
            return "I can answer about genres, authors, ratings, or recommend books! Try asking for recommendations or info."

    def chat(self, message):
        msg = message.lower()
        
        if "recommend" in msg or "similar" in msg:
            user_match = re.search(r'user[\s_]?id[\s:]*(\d+)', msg)
            book_match = re.search(r'book[\s_]?id[\s:]*(\d+)', msg)
            user_id = int(user_match.group(1)) if user_match else None
            book_id = int(book_match.group(1)) if book_match else None
            return self.recommend(user_id=user_id, book_id=book_id)
            
        elif "search" in msg or "find" in msg:
            query = re.sub(r'\b(search|find)\b', '', msg).strip()
            if not query:
                return "Please specify what you want to search for."
                
            mask = (
                self.df['Title'].str.lower().str.contains(query, na=False) |
                self.df['Author'].str.lower().str.contains(query, na=False) |
                self.df['Genres'].str.lower().str.contains(query, na=False)
            )
            found = self.df[mask].head(5)
            
            if found.empty:
                return f"No books found matching '{query}'."
            
            return "\n".join(f"{row['Title']} by {row['Author']} (Genres: {row['Genres']})" 
                           for _, row in found.iterrows())
        else:
            return self.answer_general(message)

# Global bot instance for chatbot functionality
bot = HybridBookBot()

# Function for chatbot API
def process_chat_message(message):
    """Process chat message and return response"""
    return bot.chat(message)
