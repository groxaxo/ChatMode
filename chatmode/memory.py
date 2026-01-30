import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

import chromadb

from .providers import EmbeddingProvider

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Long-term memory storage backed by ChromaDB embeddings.
    
    Stores conversation snippets with metadata for retrieval.
    """
    
    def __init__(self, collection_name: str, persist_dir: str, embedding_provider: EmbeddingProvider):
        os.makedirs(persist_dir, exist_ok=True)
        self.embedding_provider = embedding_provider
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.collection_name = collection_name
        logger.debug(f"Initialized MemoryStore: {collection_name}")

    def add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Add a text snippet to memory with enriched metadata.
        
        Args:
            text: The text content to store
            metadata: Additional metadata (sender, etc.)
            session_id: Current session identifier
            agent_id: Agent that produced this content
            topic: Current debate topic
            tags: Optional tags for filtering
        """
        if not text:
            return
        
        # Build enriched metadata
        enriched_metadata = metadata.copy() if metadata else {}
        enriched_metadata["timestamp"] = datetime.utcnow().isoformat()
        if session_id:
            enriched_metadata["session_id"] = session_id
        if agent_id:
            enriched_metadata["agent_id"] = agent_id
        if topic:
            enriched_metadata["topic"] = topic
        if tags:
            enriched_metadata["tags"] = ",".join(tags)
        
        try:
            embeddings = self.embedding_provider.embed([text])
            self.collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=embeddings,
                documents=[text],
                metadatas=[enriched_metadata],
            )
            logger.debug(f"Added memory: {text[:50]}... with metadata: {enriched_metadata}")
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    def query(
        self,
        text: str,
        k: int,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query memory for relevant snippets.
        
        Args:
            text: Query text for semantic search
            k: Maximum results to return
            session_id: Filter to specific session (optional)
            agent_id: Filter to specific agent (optional)
            where_filter: Custom ChromaDB where filter
            
        Returns:
            List of matching memory entries
        """
        if not text:
            return []
        
        try:
            embeddings = self.embedding_provider.embed([text])
            
            # Build where filter if session/agent filtering requested
            query_where = where_filter
            if not query_where:
                query_where = {}
                if session_id:
                    query_where["session_id"] = session_id
                if agent_id:
                    query_where["agent_id"] = agent_id
                # Only use the filter if it has content
                if not query_where:
                    query_where = None
            
            result = self.collection.query(
                query_embeddings=embeddings,
                n_results=k,
                include=["documents", "metadatas"],
                where=query_where,
            )
            
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            
            items = []
            for doc, meta in zip(docs, metas):
                entry = {"text": doc}
                if isinstance(meta, dict):
                    entry.update(meta)
                items.append(entry)
            
            logger.debug(f"Memory query returned {len(items)} results")
            return items
            
        except Exception as e:
            logger.error(f"Memory query failed: {e}")
            return []

    def clear(self, session_id: Optional[str] = None, agent_id: Optional[str] = None) -> None:
        """
        Clear memory entries.
        
        Args:
            session_id: If provided, only clear entries for this session
            agent_id: If provided, only clear entries for this agent
            
        If neither is provided, clears all entries.
        """
        try:
            if session_id or agent_id:
                # Build where filter for selective deletion
                where_filter = {}
                if session_id:
                    where_filter["session_id"] = session_id
                if agent_id:
                    where_filter["agent_id"] = agent_id
                
                # ChromaDB doesn't support filtered delete easily, so we need to query first
                # then delete by IDs
                result = self.collection.get(where=where_filter, include=["metadatas"])
                if result and result.get("ids"):
                    self.collection.delete(ids=result["ids"])
                    logger.info(f"Cleared {len(result['ids'])} memory entries with filter: {where_filter}")
            else:
                # Clear entire collection
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.get_or_create_collection(name=self.collection_name)
                logger.info(f"Cleared all memory in collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")

    def count(self) -> int:
        """Return the number of entries in memory."""
        return self.collection.count()
