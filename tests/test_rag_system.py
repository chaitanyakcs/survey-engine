#!/usr/bin/env python3
"""
Test script for the RAG system
"""
import asyncio
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.services.embedding_service import EmbeddingService
from src.services.retrieval_service import RetrievalService


async def test_rag_system():
    """Test the complete RAG retrieval system"""
    print("Testing RAG system...")
    
    # Initialize services
    embedding_service = EmbeddingService()
    session = SessionLocal()
    retrieval_service = RetrievalService(session)
    
    try:
        # Test query - similar to our seeded data
        test_query = "We need to determine the optimal price for a new smartphone targeting tech users"
        
        print(f"\nTest query: {test_query}")
        print("=" * 60)
        
        # 1. Generate embedding
        print("1. Generating embedding...")
        query_embedding = await embedding_service.get_embedding(test_query)
        print(f"   Embedding dimension: {len(query_embedding)}")
        
        # 2. Retrieve golden pairs
        print("\n2. Retrieving golden pairs...")
        golden_pairs = await retrieval_service.retrieve_golden_pairs(
            embedding=query_embedding,
            limit=3
        )
        
        print(f"   Found {len(golden_pairs)} golden pairs")
        for i, pair in enumerate(golden_pairs):
            print(f"   {i+1}. {pair['industry_category']} (similarity: {pair['similarity']:.3f})")
            print(f"      Methodologies: {pair['methodology_tags']}")
            print(f"      Quality: {pair['quality_score']}")
        
        # 3. Retrieve methodology blocks
        print("\n3. Retrieving methodology blocks...")
        methodology_blocks = await retrieval_service.retrieve_methodology_blocks(
            research_goal="pricing",
            limit=3
        )
        
        print(f"   Found {len(methodology_blocks)} methodology blocks")
        for i, block in enumerate(methodology_blocks):
            print(f"   {i+1}. {block['methodology']}")
            print(f"      Structure: {list(block['example_structure'].keys())}")
            print(f"      Best for: {block['usage_pattern'].get('best_for', [])}")
        
        # 4. Retrieve template questions
        print("\n4. Retrieving template questions...")
        template_questions = await retrieval_service.retrieve_template_questions(
            category="pricing",
            limit=5
        )
        
        print(f"   Found {len(template_questions)} template questions")
        for i, question in enumerate(template_questions):
            print(f"   {i+1}. [{question['category']}] {question['question_text'][:60]}...")
            print(f"      Type: {question['question_type']}, Reusability: {question['reusability_score']:.2f}")
        
        print("\n" + "=" * 60)
        print("RAG system test completed successfully! ✅")
        
    except Exception as e:
        print(f"Error testing RAG system: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(test_rag_system())