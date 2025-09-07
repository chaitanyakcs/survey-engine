from typing import List
from sentence_transformers import SentenceTransformer
from src.config import settings
import replicate
import asyncio


class EmbeddingService:
    def __init__(self) -> None:
        self.model_name = settings.embedding_model
        
        # Initialize based on model type
        if self._should_use_replicate():
            # Replicate embedding model
            if not settings.replicate_api_token:
                raise ValueError("REPLICATE_API_TOKEN is required for Replicate models but not set")
            replicate.api_token = settings.replicate_api_token  # type: ignore
            self.use_replicate = True
            self.model = None
        else:
            # Sentence Transformers model
            try:
                self.model = SentenceTransformer(self.model_name)
                self.use_replicate = False
            except Exception as e:
                # If sentence transformer fails, try to fallback to a default model
                print(f"Warning: Failed to load {self.model_name}, falling back to all-MiniLM-L6-v2")
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.use_replicate = False
    
    def _should_use_replicate(self) -> bool:
        """
        Determine if we should use Replicate based on model name
        """
        replicate_indicators = [
            "text-embedding-ada",  # OpenAI-style models
            "text-embedding-3",
            "/",  # Custom Replicate model paths
            "replicate:",  # Explicit replicate prefix
            "nateraw/",  # Popular Replicate embedding models
            "sentence-transformers/"  # Sentence transformers on Replicate
        ]
        
        return any(indicator in self.model_name for indicator in replicate_indicators)
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for given text
        """
        if self.use_replicate:
            return await self._get_replicate_embedding(text)
        else:
            return await self._get_sentence_transformer_embedding(text)
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        """
        if self.use_replicate:
            # Process individually for Replicate
            embeddings = []
            for text in texts:
                embedding = await self._get_replicate_embedding(text)
                embeddings.append(embedding)
            return embeddings
        else:
            return await self._get_sentence_transformer_embeddings_batch(texts)
    
    async def _get_replicate_embedding(self, text: str) -> List[float]:
        """
        Get embedding from Replicate API
        """
        try:
            # Use a popular text embedding model on Replicate
            if "text-embedding-ada-002" in self.model_name:
                # For OpenAI-style models, use a compatible model
                output = await replicate.async_run(
                    "replicate/all-mpnet-base-v2:b6b7585c9640cd7a9572c6e129c9549d79c9c31f0d3fdce7baac7c67ca38f305",
                    input={"text": text}
                )
            elif "/" in self.model_name:
                # Custom Replicate model specified
                output = await replicate.async_run(
                    self.model_name,
                    input={"text": text}
                )
            else:
                # Default to a good general-purpose embedding model
                output = await replicate.async_run(
                    "nateraw/bge-large-en-v1.5:9cf9f015a9cb9c61d1a2610659cdac4a4ca222f2d3707a68517b18c198a9add1",
                    input={"text": text}
                )
            
            # Handle different output formats from Replicate
            if isinstance(output, list):
                return output
            elif isinstance(output, dict) and "embedding" in output:
                return output["embedding"]
            elif isinstance(output, dict) and "embeddings" in output:
                return output["embeddings"][0] if output["embeddings"] else []
            else:
                # Fallback to sentence transformers if output format is unexpected
                return await self._get_sentence_transformer_embedding(text)
            
        except Exception as e:
            # Fallback to sentence transformers on any error
            try:
                return await self._get_sentence_transformer_embedding(text)
            except:
                raise Exception(f"Both Replicate and sentence transformer embedding failed: {str(e)}")
    
    async def _get_sentence_transformer_embedding(self, text: str) -> List[float]:
        """
        Get embedding from Sentence Transformers model
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                lambda: self.model.encode([text])[0].tolist()
            )
            return embedding  # type: ignore
        except Exception as e:
            raise Exception(f"Sentence transformer embedding failed: {str(e)}")
    
    async def _get_sentence_transformer_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts from Sentence Transformers
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts).tolist()
            )
            return embeddings  # type: ignore
        except Exception as e:
            raise Exception(f"Batch sentence transformer embedding failed: {str(e)}")