from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticSearch:
    def __init__(self):
        """
        Initialize the semantic search with TF-IDF vectorizer.
        This is a simpler approach that doesn't require external models.
        """
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),  # Use both unigrams and bigrams
            max_features=10000
        )
        self.corpus_vectors = None
        self.corpus = None

    def index_documents(self, documents):
        """
        Index a list of documents for searching.
        Args:
            documents: List of strings (documents to index)
        """
        self.corpus = documents
        # Convert documents to TF-IDF vectors
        self.corpus_vectors = self.vectorizer.fit_transform(documents)

    def search(self, query, top_k=5):
        """
        Search for similar documents.
        Args:
            query: String (search query)
            top_k: Number of results to return
        Returns:
            List of tuples (document, similarity_score)
        """
        if self.corpus_vectors is None:
            raise ValueError("No documents indexed. Call index_documents first.")

        # Convert query to TF-IDF vector
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.corpus_vectors).flatten()
        
        # Get top-k results
        top_indices = np.argsort(similarity_scores)[-top_k:][::-1]
        
        # Format results
        results = []
        for idx in top_indices:
            results.append((self.corpus[idx], similarity_scores[idx]))
            
        return results

def main():
    # Example usage
    search_engine = SemanticSearch()
    
    # Example documents
    documents = [
        "The quick brown fox jumps over the lazy dog",
        "A fast orange fox leaps over a sleepy canine",
        "The weather is beautiful today",
        "It's raining cats and dogs outside",
        "The stock market is performing well",
        "Investors are seeing good returns on their investments",
        "Python is a popular programming language",
        "Many developers use Python for machine learning",
        "The restaurant serves delicious Italian food",
        "You can get authentic pasta and pizza here"
    ]
    
    # Index the documents
    print("Indexing documents...")
    search_engine.index_documents(documents)
    
    # Example searches
    queries = [
        "Tell me about foxes",
        "What's the weather like?",
        "How are investments doing?",
        "What programming language is good for ML?",
        "Where can I get good food?"
    ]
    
    print("\nPerforming semantic searches:")
    for query in queries:
        print(f"\nQuery: {query}")
        results = search_engine.search(query, top_k=2)
        for doc, score in results:
            print(f"Score: {score:.4f} - {doc}")

if __name__ == "__main__":
    main() 