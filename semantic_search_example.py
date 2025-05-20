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
            ngram_range=(1, 2),  # Use both single words and pairs
            max_features=1000
        )
        self.documents = []
        self.embeddings = None

    def index_documents(self, documents):
        """
        Index a list of documents for searching.
        Args:
            documents: List of strings (documents to index)
        """
        self.documents = documents
        # Convert documents to TF-IDF vectors
        self.embeddings = self.vectorizer.fit_transform(documents)

    def search(self, query, top_k=2):
        """
        Search for similar documents.
        Args:
            query: String (search query)
            top_k: Number of results to return
        Returns:
            List of dictionaries with 'score' and 'text' keys
        """
        if self.embeddings is None:
            raise ValueError("No documents indexed. Call index_documents first.")

        # Convert query to TF-IDF vector
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, self.embeddings).flatten()
        
        # Get top k results
        top_indices = np.argsort(similarity_scores)[-top_k:][::-1]
        
        # Format results
        results = []
        for idx in top_indices:
            results.append({
                'score': similarity_scores[idx],
                'text': self.documents[idx]
            })
        
        return results

def main():
    # Create semantic search instance
    search = SemanticSearch()
    
    # Example documents about memory and context
    documents = [
        "The system maintains conversation history for context awareness",
        "Memory management includes both short-term and long-term storage",
        "Context window size affects how much history can be retained",
        "The AI can recall previous interactions and user preferences",
        "Memory compression techniques help manage large conversation histories",
        "Token limits determine maximum context length in conversations",
        "The system uses semantic memory for understanding concepts",
        "Memory pruning removes irrelevant information to save space",
        "Context switching allows handling multiple conversation threads",
        "Memory persistence ensures conversations survive system restarts"
    ]
    
    # Index the documents
    print("Indexing documents...\n")
    search.index_documents(documents)
    
    # Example queries
    queries = [
        "How does the system remember past conversations?",
        "What happens when memory gets too large?",
        "Can the AI recall previous interactions?",
        "How is context maintained in conversations?",
        "What are the memory limitations?"
    ]
    
    # Perform searches
    print("Performing semantic searches:\n")
    for query in queries:
        print(f"Query: {query}")
        results = search.search(query)
        for result in results:
            print(f"Score: {result['score']:.4f} - {result['text']}")
        print()

if __name__ == "__main__":
    main() 