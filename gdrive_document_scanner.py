#!/usr/bin/env python3
"""
HCT Knowledge Base - Google Drive Scanner (Production)
Lightweight version without LangChain - preserves ALL functionality
"""
import os
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Optional
import io

# Google Drive API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Document parsers (lightweight)
import fitz  # PyMuPDF
from docx import Document

class GoogleDriveScanner:
    """
    Lightweight document scanner for Google Drive
    Supports: PDF, DOCX, TXT (same as before, just without LangChain)
    """
    
    SUPPORTED_TYPES = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/msword': '.doc',
        'text/plain': '.txt',
    }
    
    def __init__(self, credentials_json: str = None, folder_id: str = None):
        """Initialize with credentials JSON string or path"""
        self.credentials_json = credentials_json or os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1m6wF8p340oSbRvt0s0zAGFh1l8VgC8wI')
        self.service = None
        
        if self.credentials_json:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Check if credentials_json is a file path or JSON string
            if os.path.exists(self.credentials_json):
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_json,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            else:
                # It's a JSON string (from environment variable)
                creds_dict = json.loads(self.credentials_json)
                creds = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ Authenticated with Google Drive")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def parse_filename(self, filename: str) -> Dict:
        """Parse HCT naming convention: B_F5_AM_Aviation.pdf"""
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
    
    def list_files(self) -> List[Dict]:
        """List all supported files in Google Drive folder"""
        if not self.service:
            print("❌ Not authenticated")
            return []
        
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, modifiedTime)',
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            supported_files = [f for f in files if f['mimeType'] in self.SUPPORTED_TYPES]
            
            print(f"✅ Found {len(supported_files)} supported documents")
            return supported_files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def download_file(self, file_id: str, filename: str) -> Optional[str]:
        """Download file from Google Drive to temp directory"""
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
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text() + "\n"
            
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"   ⚠️ PDF error: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"   ⚠️ DOCX error: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip()
        except Exception as e:
            print(f"   ⚠️ TXT error: {e}")
            return ""
    
    def extract_text(self, file_path: str, mime_type: str) -> str:
        """Extract text based on file type"""
        if mime_type == 'application/pdf':
            return self.extract_text_from_pdf(file_path)
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return self.extract_text_from_docx(file_path)
        elif mime_type == 'text/plain':
            return self.extract_text_from_txt(file_path)
        else:
            return ""
    
    def scan_drive(self) -> List[Dict]:
        """Scan Google Drive folder and extract all documents"""
        print(f"\n📂 Scanning Google Drive folder: {self.folder_id}")
        
        files = self.list_files()
        
        if not files:
            print("⚠️ No files found")
            return []
        
        documents = []
        
        for i, file_meta in enumerate(files, 1):
            file_id = file_meta['id']
            filename = file_meta['name']
            mime_type = file_meta['mimeType']
            
            print(f"\n📄 [{i}/{len(files)}] {filename}")
            
            # Download file
            file_path = self.download_file(file_id, filename)
            if not file_path:
                continue
            
            # Extract text
            print(f"   📖 Extracting text...")
            text = self.extract_text(file_path, mime_type)
            
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
            else:
                print(f"   ⚠️ No text extracted")
            
            # Clean up temp file
            try:
                os.remove(file_path)
            except:
                pass
        
        print(f"\n✅ Scan complete! {len(documents)} documents extracted")
        total_words = sum(d['word_count'] for d in documents)
        print(f"📊 Total words: {total_words:,}")
        
        return documents
    
    def save_index(self, documents: List[Dict], output_path: str = 'knowledge_index.json'):
        """Save extracted documents to JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(output_path) / 1024
            print(f"\n💾 Saved: {output_path} ({file_size:.1f} KB)")
            return True
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False


# Command-line testing
if __name__ == '__main__':
    print("=" * 70)
    print("🔍 HCT GOOGLE DRIVE SCANNER - PRODUCTION VERSION")
    print("=" * 70)
    
    scanner = GoogleDriveScanner()
    
    if scanner.service:
        documents = scanner.scan_drive()
        
        if documents:
            scanner.save_index(documents)
            print("\n✅ Ready to use!")
        else:
            print("\n⚠️ No documents found or extracted")
    else:
        print("\n❌ Failed to authenticate with Google Drive")
        print("   Set GOOGLE_DRIVE_CREDENTIALS in environment")
    
    print("=" * 70)
