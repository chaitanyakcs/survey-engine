from typing import List, Optional, Any
from sentence_transformers import SentenceTransformer
from src.config import settings
import replicate
import asyncio
import uuid
import time
from ..utils.llm_audit_decorator import LLMAuditContext
from ..services.llm_audit_service import LLMAuditService


class EmbeddingService:
    # Class-level singleton to avoid multiple model loads
    _instance = None
    _model = None
    _initialized = False
    _model_loading = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_session: Optional[Any] = None) -> None:
        # Only initialize once
        if hasattr(self, '_initialized_instance'):
            return
            
        self.model_name = settings.embedding_model
        self.use_replicate = None
        self._initialized_instance = True
        self.db_session = db_session
        
        # Always initialize model attribute
        self.model = None
        self._initialized = False
        
        # Use class-level model if available
        if EmbeddingService._model is not None:
            self.model = EmbeddingService._model
            self._initialized = True
    
    def _ensure_initialized(self):
        """Lazy initialization of the embedding model"""
        if self._initialized or EmbeddingService._initialized:
            return
            
        # Initialize based on model type
        if self._should_use_replicate():
            # Replicate embedding model
            if not settings.replicate_api_token:
                raise ValueError("REPLICATE_API_TOKEN is required for Replicate models but not set")
            self.replicate_client = replicate.Client(api_token=settings.replicate_api_token)
            self.use_replicate = True
            self.model = None
        else:
            # Sentence Transformers model - load if not already loading
            self.use_replicate = False
            if (self.model is None and EmbeddingService._model is None and 
                not self._model_loading and not EmbeddingService._model_loading):
                self._load_sentence_transformer_model()
        
        self._initialized = True
        EmbeddingService._initialized = True
    
    def _load_sentence_transformer_model(self):
        """Load the Sentence Transformer model"""
        if (self.model is not None or self._model_loading or 
            EmbeddingService._model is not None or EmbeddingService._model_loading):
            return
            
        self._model_loading = True
        EmbeddingService._model_loading = True
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔄 [EmbeddingService] Loading SentenceTransformer model: {self.model_name}")
            logger.info(f"⏳ [EmbeddingService] This may take a few seconds on first run...")
            model = SentenceTransformer(self.model_name)
            
            # Store at class level for sharing
            EmbeddingService._model = model
            self.model = model
            
            logger.info(f"✅ [EmbeddingService] Model loaded successfully: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ [EmbeddingService] Failed to load model {self.model_name}: {str(e)}")
            # Fallback to a default model
            try:
                logger.info(f"🔄 [EmbeddingService] Trying fallback model: all-MiniLM-L6-v2")
                model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Store at class level for sharing
                EmbeddingService._model = model
                self.model = model
                
                print(f"✅ [EmbeddingService] Fallback model loaded successfully")
            except Exception as fallback_e:
                print(f"❌ [EmbeddingService] Fallback model also failed: {str(fallback_e)}")
                raise Exception(f"Failed to load any embedding model: {str(e)}")
        finally:
            self._model_loading = False
            EmbeddingService._model_loading = False
    
    async def preload_model(self):
        """Preload the model in background (non-blocking)"""
        if not self._should_use_replicate():
            if self.model is None and EmbeddingService._model is None:
                print(f"🔄 [EmbeddingService] Preloading model in background: {self.model_name}")
                # Run model loading in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._load_sentence_transformer_model)
            else:
                print(f"✅ [EmbeddingService] Model already loaded: {self.model_name}")
        else:
            print(f"🌐 [EmbeddingService] Using Replicate API, no local model to preload")
    
    @classmethod
    def is_ready(cls) -> bool:
        """Check if embedding models are ready"""
        return cls._initialized and (cls._model is not None or cls._should_use_replicate_static())
    
    @classmethod
    def wait_until_ready(cls, timeout: int = 300) -> bool:
        """Wait for models to be ready with timeout"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if cls.is_ready():
                return True
            time.sleep(0.1)  # Check every 100ms
        
        return False
    
    @classmethod
    def _should_use_replicate_static(cls) -> bool:
        """Static version of _should_use_replicate for class methods"""
        from src.config import settings
        replicate_indicators = [
            "text-embedding-ada",  # OpenAI-style models
            "text-embedding-3",
            "/",  # Custom Replicate model paths
            "replicate:",  # Explicit replicate prefix
            "nateraw/",  # Popular Replicate embedding models
            "sentence-transformers/"  # Sentence transformers on Replicate
        ]
        
        return any(indicator in settings.embedding_model for indicator in replicate_indicators)
    
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔄 [EmbeddingService] Generating embedding for text length: {len(text)}")
        logger.debug(f"🔄 [EmbeddingService] Text preview: '{text[:100]}...'")
        
        self._ensure_initialized()
        
        if self.use_replicate:
            logger.info("🌐 [EmbeddingService] Using Replicate API for embedding generation")
            return await self._get_replicate_embedding(text)
        else:
            logger.info("🤖 [EmbeddingService] Using SentenceTransformer for embedding generation")
            return await self._get_sentence_transformer_embedding(text)
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        """
        self._ensure_initialized()
        
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
            # Determine the model to use
            if "text-embedding-ada-002" in self.model_name:
                model_to_use = "replicate/all-mpnet-base-v2:b6b7585c9640cd7a9572c6e129c9549d79c9c31f0d3fdce7baac7c67ca38f305"
            elif "/" in self.model_name:
                model_to_use = self.model_name
            else:
                model_to_use = "nateraw/bge-large-en-v1.5:9cf9f015a9cb9c61d1a2610659cdac4a4ca222f2d3707a68517b18c198a9add1"
            
            # Create audit context for this LLM interaction
            interaction_id = f"embedding_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session) if self.db_session else None
            
            if audit_service:
                async with LLMAuditContext(
                    audit_service=audit_service,
                    interaction_id=interaction_id,
                    model_name=model_to_use,
                    model_provider="replicate",
                    purpose="embedding",
                    input_prompt=text,
                    sub_purpose="text_embedding",
                    context_type="text",
                    hyperparameters={},
                    metadata={
                        "text_length": len(text),
                        "model_name": model_to_use
                    },
                    tags=["embedding", "text_processing"]
                ) as audit_context:
                    start_time = time.time()
                    output = await self.replicate_client.async_run(
                        model_to_use,
                        input={"text": text}
                    )
                    
                    # Process the output and set audit context
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Capture raw response immediately (unprocessed)
                    if hasattr(output, '__iter__') and not isinstance(output, str):
                        raw_response = "".join(str(chunk) for chunk in output)
                    else:
                        raw_response = str(output)
                    
                    # Process the output for further use
                    processed_output = raw_response.strip()
                    
                    # Set raw response (unprocessed) and processed output
                    audit_context.set_raw_response(raw_response)
                    audit_context.set_output(
                        output_content=processed_output,
                        response_time_ms=response_time_ms
                    )
            else:
                # Fallback without auditing
                output = await self.replicate_client.async_run(
                    model_to_use,
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
        if self.model is None:
            # Load model if not already loaded
            self._load_sentence_transformer_model()
        
        if self.model is None:
            raise Exception("Failed to load SentenceTransformer model")
        
        try:
            # Run encoding in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, self.model.encode, text)
            # Handle both numpy arrays and lists
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            else:
                return list(embedding)
        except Exception as e:
            print(f"❌ [EmbeddingService] Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    async def _get_sentence_transformer_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts from Sentence Transformers
        """
        if self.model is None:
            # Load model if not already loaded
            self._load_sentence_transformer_model()
        
        if self.model is None:
            raise Exception("Failed to load SentenceTransformer model")
        
        try:
            # Run batch encoding in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self.model.encode, texts)
            # Handle both numpy arrays and lists
            result = []
            for embedding in embeddings:
                if hasattr(embedding, 'tolist'):
                    result.append(embedding.tolist())
                else:
                    result.append(list(embedding))
            return result
        except Exception as e:
            print(f"❌ [EmbeddingService] Error generating batch embeddings: {str(e)}")
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")