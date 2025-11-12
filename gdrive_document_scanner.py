#!/usr/bin/env python3
"""
HCT Knowledge Base - Google Drive Scanner with LangChain
Universal document parser supporting ALL file types
"""
import os
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Optional

# Google Drive API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# LangChain Universal Document Loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader,
    TextLoader,
)

class GoogleDriveScanner:
    """
    Universal document scanner for Google Drive using LangChain
    """
    
    MIME_TYPES = {
        'application/pdf': {'ext': '.pdf', 'loader': PyPDFLoader},
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
            'ext': '.docx', 'loader': UnstructuredWordDocumentLoader
        },
        'application/msword': {'ext': '.doc', 'loader': UnstructuredWordDocumentLoader},
        'text/csv': {'ext': '.csv', 'loader': CSVLoader},
        'text/plain': {'ext': '.txt', 'loader': TextLoader},
    }
    
    def __init__(self, credentials_path: str = None, folder_id: str = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.service = None
        
        if self.credentials_path:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                self.service = build('drive', 'v3', credentials=creds)
                print("✅ Authenticated with Google Drive")
            else:
                print("⚠️  Credentials file not found")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
    
    def parse_filename(self, filename: str) -> Dict:
        """Parse HCT naming convention"""
        from pathlib import Path
        name_without_ext = Path(filename).stem
        parts = name_without_ext.split('_')
        
        return {
            'category': parts[0] if len(parts) > 0 else 'Unknown',
            'product': parts[1] if len(parts) > 1 else 'Unknown',
            'subcategory': parts[2] if len(parts) > 2 else '',
            'topic': '_'.join(parts[3:]) if len(parts) > 3 else '',
            'original_filename': filename
        }
    
    def list_files(self, folder_id: str = None) -> List[Dict]:
        """List all files in Google Drive folder"""
        if not self.service:
            print("❌ Not authenticated")
            return []
        
        folder_id = folder_id or self.folder_id
        
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, modifiedTime)',
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            supported_files = [f for f in files if f['mimeType'] in self.MIME_TYPES]
            
            print(f"✅ Found {len(supported_files)} supported documents")
            return supported_files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def download_file(self, file_id: str, filename: str) -> Optional[str]:
        """Download file from Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, filename)
            
            with io.FileIO(temp_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            return temp_path
        except Exception as e:
            print(f"   ❌ Download error: {e}")
            return None
    
    def extract_text_with_langchain(self, file_path: str, mime_type: str) -> str:
        """Extract text using LangChain"""
        try:
            loader_class = self.MIME_TYPES[mime_type]['loader']
            
            if loader_class == CSVLoader:
                loader = loader_class(file_path, encoding='utf-8')
            else:
                loader = loader_class(file_path)
            
            documents = loader.load()
            text = "\n\n".join([doc.page_content for doc in documents])
            return text.strip()
        except Exception as e:
            print(f"   ⚠️  Extraction failed: {e}")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read().strip()
            except:
                return ""
    
    def scan_drive(self, folder_id: str = None) -> List[Dict]:
        """Scan Google Drive folder and extract all documents"""
        files = self.list_files(folder_id)
        
        if not files:
            return []
        
        documents = []
        
        for i, file_meta in enumerate(files, 1):
            file_id = file_meta['id']
            filename = file_meta['name']
            mime_type = file_meta['mimeType']
            
            print(f"\n📄 [{i}/{len(files)}] {filename}")
            
            file_path = self.download_file(file_id, filename)
            if not file_path:
                continue
            
            print(f"   📖 Extracting text...")
            text = self.extract_text_with_langchain(file_path, mime_type)
            
            if text:
                word_count = len(text.split())
                print(f"   ✅ Extracted {word_count:,} words")
                
                metadata = self.parse_filename(filename)
                
                documents.append({
                    'file_id': file_id,
                    'filename': filename,
                    'mime_type': mime_type,
                    'category': metadata['category'],
                    'product': metadata['product'],
                    'subcategory': metadata['subcategory'],
                    'topic': metadata['topic'],
                    'content': text,
                    'word_count': word_count,
                    'scanned_at': datetime.now().isoformat(),
                    'source': 'google_drive'
                })
            
            try:
                os.remove(file_path)
            except:
                pass
        
        print(f"\n✅ Scan complete! {len(documents)} documents extracted")
        return documents
    
    def save_index(self, documents: List[Dict], output_path: str = 'knowledge_index.json'):
        """Save extracted documents to JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False