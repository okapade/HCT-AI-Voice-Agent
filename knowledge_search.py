#!/usr/bin/env python3
"""
HCT Knowledge Search Engine
Fast full-text search using Whoosh
"""
import os
import json
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.analysis import StemmingAnalyzer
import re

class KnowledgeSearch:
    def __init__(self, index_dir='whoosh_index'):
        self.index_dir = index_dir
        self.schema = Schema(
            filename=ID(stored=True),
            path=TEXT(stored=True),
            category=KEYWORD(stored=True, commas=True),
            product=KEYWORD(stored=True, commas=True),
            subcategory=KEYWORD(stored=True, commas=True),
            topic=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            content=TEXT(stored=True, analyzer=StemmingAnalyzer())
        )
        self.ix = None
        
    def create_index(self, documents):
        """
        Create Whoosh index from scanned documents
        documents: list of dicts from document_scanner
        """
        print(f"\n🔨 Building search index...")
        
        # Create index directory
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            self.ix = index.create_in(self.index_dir, self.schema)
            print(f"   ✅ Created new index: {self.index_dir}")
        else:
            # Open existing or create new
            try:
                self.ix = index.open_dir(self.index_dir)
                print(f"   ✅ Opened existing index")
            except:
                self.ix = index.create_in(self.index_dir, self.schema)
                print(f"   ✅ Created new index")
        
        # Index all documents
        writer = self.ix.writer()
        
        for i, doc in enumerate(documents):
            writer.add_document(
                filename=doc['filename'],
                path=doc.get('path', ''),
                category=doc['category'],
                product=doc['product'],
                subcategory=doc['subcategory'],
                topic=doc['topic'],
                content=doc['content']
            )
            
            if (i + 1) % 10 == 0:
                print(f"   📝 Indexed {i + 1}/{len(documents)} documents")
        
        writer.commit()
        print(f"   ✅ Index complete: {len(documents)} documents")
        
    def load_index(self):
        """Load existing index"""
        if os.path.exists(self.index_dir):
            try:
                self.ix = index.open_dir(self.index_dir)
                print(f"✅ Search index loaded")
                return True
            except Exception as e:
                print(f"⚠️  Index load error: {e}")
                return False
        else:
            print(f"⚠️  No index found at {self.index_dir}")
            return False
    
    def normalize_query(self, query):
        """
        Normalize common HCT product names
        'f 500' -> 'f-500', 'f500' -> 'f-500'
        """
        normalized = query.lower()
        
        # F-500 variations
        normalized = re.sub(r'\bf\s*500\b', 'f-500', normalized)
        normalized = re.sub(r'\bf500\b', 'f-500', normalized)
        
        # HydroLock variations
        normalized = re.sub(r'\bhydro\s*lock\b', 'hydrolock', normalized)
        
        # Pinnacle variations
        normalized = re.sub(r'\bpinnacle\s*foam\b', 'pinnacle', normalized)
        
        # Dust Wash variations
        normalized = re.sub(r'\bdust\s*wash\b', 'dust-wash', normalized)
        
        return normalized
    
    def search(self, query_text, max_results=5):
        """
        Search for documents matching query
        Returns list of results with relevance scores
        """
        if not self.ix:
            if not self.load_index():
                return []
        
        # Normalize query
        normalized_query = self.normalize_query(query_text)
        
        print(f"\n🔍 Searching: '{query_text}'")
        if normalized_query != query_text.lower():
            print(f"   📝 Normalized: '{normalized_query}'")
        
        results_list = []
        
        with self.ix.searcher() as searcher:
            # Search across multiple fields
            parser = MultifieldParser(
                ['product', 'topic', 'content', 'category', 'subcategory'],
                schema=self.ix.schema
            )
            
            query = parser.parse(normalized_query)
            results = searcher.search(query, limit=max_results)
            
            print(f"   ✅ Found {len(results)} results")
            
            for i, hit in enumerate(results):
                # Extract relevant snippet from content
                snippet = self.get_snippet(hit['content'], normalized_query)
                
                result = {
                    'rank': i + 1,
                    'score': hit.score,
                    'filename': hit['filename'],
                    'path': hit['path'],
                    'category': hit['category'],
                    'product': hit['product'],
                    'subcategory': hit.get('subcategory', ''),
                    'topic': hit['topic'],
                    'snippet': snippet,
                    'full_content': hit['content']
                }
                
                results_list.append(result)
                
                print(f"\n   [{i+1}] {hit['filename']}")
                print(f"       Score: {hit.score:.2f}")
                print(f"       Product: {hit['product']}")
                print(f"       Snippet: {snippet[:100]}...")
        
        return results_list
    
    def get_snippet(self, content, query, snippet_length=300):
        """
        Extract relevant snippet from content based on query
        """
        # Find first occurrence of any query term
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        earliest_pos = len(content)
        for term in query_terms:
            pos = content_lower.find(term)
            if pos != -1 and pos < earliest_pos:
                earliest_pos = pos
        
        if earliest_pos == len(content):
            # No match found, return beginning
            return content[:snippet_length].strip()
        
        # Extract snippet around match
        start = max(0, earliest_pos - 100)
        end = min(len(content), earliest_pos + snippet_length)
        
        snippet = content[start:end].strip()
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def get_by_product(self, product_name, max_results=10):
        """Get all documents for a specific product"""
        if not self.ix:
            if not self.load_index():
                return []
        
        results_list = []
        
        with self.ix.searcher() as searcher:
            parser = QueryParser('product', schema=self.ix.schema)
            query = parser.parse(product_name.lower())
            results = searcher.search(query, limit=max_results)
            
            for hit in results:
                results_list.append({
                    'filename': hit['filename'],
                    'path': hit['path'],
                    'category': hit['category'],
                    'topic': hit['topic'],
                    'content': hit['content']
                })
        
        return results_list


# Command-line testing
if __name__ == '__main__':
    import sys
    
    search_engine = KnowledgeSearch()
    
    # Load index
    if search_engine.load_index():
        # Test search
        test_queries = [
            "F-500 aviation applications",
            "lithium ion battery fire",
            "HydroLock vapor mitigation",
            "what is f 500"
        ]
        
        if len(sys.argv) > 1:
            # Search from command line
            query = ' '.join(sys.argv[1:])
            results = search_engine.search(query)
            
            if results:
                print(f"\n📄 Top result:")
                print(f"   {results[0]['filename']}")
                print(f"\n   Snippet:")
                print(f"   {results[0]['snippet'][:200]}...")
        else:
            # Run test queries
            print("\n🧪 Running test searches...")
            for query in test_queries:
                results = search_engine.search(query, max_results=3)
                print()
    else:
        print("\n⚠️  Run document_scanner.py first to create index!")
