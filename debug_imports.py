#!/usr/bin/env python3
"""Debug script to test imports step by step"""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a module and report the result"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_name} - {e}")
        traceback.print_exc()
        return False

def main():
    print("🔍 Testing imports step by step...")
    
    # Test basic imports
    test_import("pgvector", "pgvector package")
    test_import("pgvector.asyncpg", "pgvector.asyncpg module")
    test_import("pgvector.sqlalchemy", "pgvector.sqlalchemy module")
    
    # Test langchain imports
    test_import("langchain", "langchain package")
    test_import("langgraph", "langgraph package")
    test_import("langgraph.graph", "langgraph.graph module")
    
    # Test our modules
    test_import("src.config", "src.config module")
    test_import("src.database.connection", "src.database.connection module")
    test_import("src.database.models", "src.database.models module")
    test_import("src.services.websocket_client", "src.services.websocket_client module")
    test_import("src.workflows.state", "src.workflows.state module")
    test_import("src.workflows.workflow", "src.workflows.workflow module")

if __name__ == "__main__":
    main()


