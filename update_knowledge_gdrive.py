#!/usr/bin/env python3
"""
Update HCT Knowledge Base from Google Drive
"""
import sys
import os
from gdrive_document_scanner import GoogleDriveScanner
from knowledge_search import KnowledgeSearch

def update_knowledge_base():
    print("\n" + "="*70)
    print("🔄 UPDATING HCT KNOWLEDGE BASE FROM GOOGLE DRIVE")
    print("="*70)
    
    # Check credentials
    if not os.getenv('GOOGLE_DRIVE_CREDENTIALS'):
        print("\n❌ GOOGLE_DRIVE_CREDENTIALS not set in .env")
        return False
    
    # Step 1: Scan Google Drive
    print("\n📂 Step 1: Scanning Google Drive...")
    scanner = GoogleDriveScanner()
    documents = scanner.scan_drive()
    
    if not documents:
        print("\n❌ No documents found in Google Drive!")
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
    success = update_knowledge_base()
    sys.exit(0 if success else 1)