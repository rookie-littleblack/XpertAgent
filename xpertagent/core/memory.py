"""
Memory management module for XpertAgent.
This module handles the storage and retrieval of agent memories using ChromaDB.
"""

import chromadb
from typing import List, Dict, Any
from datetime import datetime
from chromadb.config import Settings as ChromaSettings
from xpertagent.config.settings import settings

class Memory:
    """
    Memory management class using ChromaDB as vector database.
    Handles storage, retrieval, and management of agent memories.
    """
    
    def __init__(self):
        """
        Initialize the memory system with ChromaDB client.
        Sets up persistent storage and collection with cosine similarity.
        """
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(
                anonymized_telemetry=False  # Disable telemetry for privacy
            )
        )
        
        # Get or create collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name=settings.MEMORY_COLLECTION,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity for vector matching
        )
    
    def add(self, text: str, metadata: Dict[str, Any] | None = None) -> None:
        """
        Add a memory entry to the vector database.
        
        Args:
            text: The text content to store
            metadata: Associated metadata dictionary, defaults to None
            
        Note:
            - Creates a copy of metadata to avoid modifying the original
            - Automatically adds timestamp to metadata
            - Generates unique ID using timestamp
        """
        # Create metadata copy to avoid modifying default parameter
        current_metadata = {} if metadata is None else metadata.copy()
        
        # Add timestamp to metadata
        current_metadata["timestamp"] = str(datetime.now())
        
        # Generate unique document ID
        doc_id = str(datetime.now().timestamp())
        
        # Add entry to collection
        self.collection.add(
            documents=[text],
            metadatas=[current_metadata],
            ids=[doc_id]
        )
    
    def search(self, query: str, n_results: int = 5) -> List[str]:
        """
        Search for relevant memories using vector similarity.
        
        Args:
            query: The search query text
            n_results: Maximum number of results to return (default: 5)
            
        Returns:
            List[str]: List of unique relevant memory texts
            
        Note:
            Uses cosine similarity for matching and removes duplicates
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Get documents and remove duplicates while preserving order
        documents = results["documents"][0]
        seen = set()
        unique_documents = []
        
        for doc in documents:
            if doc not in seen:
                seen.add(doc)
                unique_documents.append(doc)
        
        return unique_documents
    
    def clear(self) -> None:
        """
        Clear all memories from the collection.
        
        Note:
            - Deletes the entire collection
            - Creates a new empty collection with the same name
            - Use with caution as this operation cannot be undone
        """
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}  # Maintain cosine similarity setting
        )