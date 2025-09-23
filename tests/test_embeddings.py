#!/usr/bin/env python3
"""
Test vector embeddings functionality
"""
import asyncio
from sentence_transformers import SentenceTransformer

async def test_embeddings():
    """
    Test sentence transformer embeddings
    """
    print("🧪 Testing vector embeddings functionality...")
    
    try:
        # Initialize sentence transformer
        print("📥 Loading sentence transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded successfully!")
        
        # Test texts
        test_texts = [
            "We need market research for premium coffee machines in the $500-2000 range",
            "Consumer electronics survey for smartphone purchasing behavior",
            "Restaurant dining experience and customer satisfaction survey"
        ]
        
        print("🔢 Generating embeddings for test texts...")
        
        # Generate embeddings
        embeddings = model.encode(test_texts)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"📊 Embedding dimensions: {embeddings[0].shape}")
        
        # Test similarity
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Coffee vs smartphone (should be lower similarity)
        sim1 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        # Coffee vs coffee (should be higher similarity with itself)
        coffee_text2 = "Premium coffee machine market research for price sensitivity"
        coffee_embedding2 = model.encode([coffee_text2])
        sim2 = cosine_similarity([embeddings[0]], coffee_embedding2)[0][0]
        
        print(f"📏 Similarity coffee vs smartphone: {sim1:.3f}")
        print(f"📏 Similarity coffee vs coffee: {sim2:.3f}")
        
        if sim2 > sim1:
            print("✅ Semantic similarity working correctly!")
        else:
            print("⚠️  Similarity results unexpected")
            
        print("🎉 Vector embeddings test completed successfully!")
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_embeddings())