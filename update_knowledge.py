#!/usr/bin/env python3
"""
Update HCT Knowledge Base
Quick script to refresh index when documents change
"""
import sys
import os
from document_scanner import DocumentScanner
from knowledge_search import KnowledgeSearch

# Default KB path
KB_PATH = '/Users/omkarkapade/Desktop/HCT AI Agent-KB'

def update_knowledge_base(kb_path=KB_PATH):
    """
    Full update: Scan documents + rebuild search index
    """
    print("\n" + "="*70)
    print("🔄 UPDATING HCT KNOWLEDGE BASE")
    print("="*70)
    
    # Step 1: Scan documents
    print("\n📁 Step 1: Scanning documents...")
    scanner = DocumentScanner(kb_path)
    documents = scanner.scan_folder()
    
    if not documents:
        print("\n❌ No documents found!")
        return False
    
    # Step 2: Save JSON index
    print("\n💾 Step 2: Saving document index...")
    scanner.save_index(documents, 'knowledge_index.json')
    
    # Step 3: Build search index
    print("\n🔨 Step 3: Building search index...")
    search = KnowledgeSearch('whoosh_index')
    search.create_index(documents)
    
    print("\n" + "="*70)
    print("✅ KNOWLEDGE BASE UPDATED!")
    print("="*70)
    print(f"📊 Total documents: {len(documents)}")
    print(f"📊 Total words: {sum(d['word_count'] for d in documents):,}")
    print("\n💡 Ready to use in voice agent!")
    print("="*70 + "\n")
    
    return True

if __name__ == '__main__':
    # Allow custom path from command line
    kb_path = sys.argv[1] if len(sys.argv) > 1 else KB_PATH
    
    # Check if path exists
    if not os.path.exists(kb_path):
        print(f"\n❌ Folder not found: {kb_path}")
        print(f"\n💡 Usage: python update_knowledge.py [path-to-kb-folder]")
        print(f"   Default: {KB_PATH}\n")
        sys.exit(1)
    
    # Run update
    success = update_knowledge_base(kb_path)
    sys.exit(0 if success else 1)
