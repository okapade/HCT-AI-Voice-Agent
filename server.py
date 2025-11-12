from flask import Flask, request, jsonify, send_from_directory, Response, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
from bs4 import BeautifulSoup
from io import BytesIO

# Import Google Drive knowledge search
from knowledge_search import KnowledgeSearch

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Knowledge Search (works with both local and Drive-sourced indexes)
knowledge_search = KnowledgeSearch('whoosh_index')

# HCT Website URLs
HCT_URLS = {
    'f500': 'https://hct-world.com/f-500-encapsulator-agent',
    'f-500': 'https://hct-world.com/f-500-encapsulator-agent',
    'hydrolock': 'https://hct-world.com/hydrolock',
    'pinnacle': 'https://hct-world.com/pinnacle-foam',
    'dust wash': 'https://hct-world.com/dust-wash',
    'diamond doser': 'https://hct-world.com/diamond-doser',
}

# Fetch from website
def fetch_hct_page(url):
    """Fetch content from HCT website"""
    try:
        print(f"🌐 Fetching: {url}")
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(['script', 'style', 'nav', 'footer']):
                script.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            print(f"✅ Got {len(text)} chars from web")
            return text[:1000]
    except Exception as e:
        print(f"⚠️ Scrape error: {e}")
    return ""

# Basic knowledge (fallback)
KNOWLEDGE = """F-500: Multi-class fire suppression (A,B,C,D,lithium). Fluorine-free, biodegradable. NFPA 18A certified. Reduces smoke 97%, toxins 98%.
HydroLock: Vapor mitigation, tank degassing. Reduces LEL.
Pinnacle: PFAS-free Class A foam.
Dust Wash: Combustible dust control.
Diamond Doser: Proportioning system for HCT products."""

sessions = {}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/health')
def health():
    kb_status = {
        'indexed': knowledge_search.ix is not None,
        'source': 'google_drive' if os.getenv('GOOGLE_DRIVE_FOLDER_ID') else 'local',
    }
    
    if knowledge_search.ix:
        with knowledge_search.ix.searcher() as searcher:
            kb_status['document_count'] = searcher.doc_count_all()
    
    return jsonify({
        'ok': True,
        'knowledge_base': kb_status,
        'google_drive_enabled': bool(os.getenv('GOOGLE_DRIVE_CREDENTIALS'))
    })

# ============================================================================
# CHAT - with GOOGLE DRIVE KNOWLEDGE BASE + web scraping
# ============================================================================

@app.route('/chat/stream', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        print(f"\n💬 Q: {message}")
        
        if session_id not in sessions:
            sessions[session_id] = []
        
        # ==============================================================
        # Search Google Drive knowledge base FIRST (priority source)
        # ==============================================================
        local_context = ""
        
        try:
            search_results = knowledge_search.search(message, max_results=3)
            
            if search_results:
                print(f"📚 Found {len(search_results)} documents from Google Drive:")
                
                local_context = "\n\n=== FROM HCT KNOWLEDGE BASE (Google Drive) ===\n"
                
                for i, result in enumerate(search_results[:2], 1):
                    print(f"   [{i}] {result['filename']} (Score: {result['score']:.2f})")
                    local_context += f"\n[Document {i}: {result['filename']}]\n"
                    local_context += f"{result['snippet']}\n"
                
                local_context += "=== END KNOWLEDGE BASE ===\n"
            else:
                print("⚠️ No documents found in knowledge base")
        except Exception as e:
            print(f"⚠️ Knowledge search error: {e}")
            local_context = ""
        
        # ==============================================================
        # ALSO check website for latest info
        # ==============================================================
        web_context = ""
        message_lower = message.lower()
        
        for key, url in HCT_URLS.items():
            if key in message_lower:
                web_content = fetch_hct_page(url)
                if web_content:
                    web_context = f"\n\n=== FROM WEBSITE (Latest) ===\n{web_content}\n=== END WEBSITE ===\n"
                break
        
        # ==============================================================
        # Build messages with conversational AI prompt
        # ==============================================================
        
        system_prompt = f"""You are the HCT Voice Agent, a knowledgeable and conversational expert on Hazard Control Technologies products and fire suppression solutions.

RESPONSE STYLE:
- Provide comprehensive answers of 6-7 sentences that fully explain the topic
- Be conversational and professional, never say "I don't have that in my knowledge base"
- If you don't have specific information, provide related helpful information about HCT products and offer to help with related topics
- Occasionally (about 30% of the time) ask a relevant follow-up question to engage the user, especially when:
  * The user asks a broad question that could be narrowed down
  * There are multiple product options that might fit their needs
  * You want to understand their specific use case better
- Don't ask follow-up questions when the user asks a very specific factual question that you fully answered

KNOWLEDGE SOURCES (use these when available):
{KNOWLEDGE}
{local_context}
{web_context}

Remember: Be helpful, detailed, and conversational. Focus on providing value even if you don't have the exact information requested."""
        
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        messages.extend(sessions[session_id][-2:])
        messages.append({'role': 'user', 'content': message})
        
        def generate():
            try:
                stream = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=messages,
                    stream=True,
                    max_tokens=400,  # Increased for longer responses
                    temperature=0.7  # Increased for more conversational tone
                )
                
                full = ''
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full += content
                        yield f"data: {json.dumps({'content': content})}\n\n"
                
                print(f"✅ A: {full[:50]}...")
                
                sessions[session_id].append({'role': 'user', 'content': message})
                sessions[session_id].append({'role': 'assistant', 'content': full})
                sessions[session_id] = sessions[session_id][-4:]
                
                yield f"data: [DONE]\n\n"
                
            except Exception as e:
                print(f"❌ Error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TTS - HD Quality
# ============================================================================

@app.route('/speak', methods=['POST'])
def speak():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        voice = data.get('voice', 'nova')
        
        if not text:
            return jsonify({'error': 'No text'}), 400
        
        if len(text) > 500:
            text = text[:500]
        
        print(f"🔊 TTS ({voice}): {len(text)} chars")
        
        response = client.audio.speech.create(
            model='tts-1-hd',
            voice=voice,
            input=text,
            speed=1.0,
            response_format='mp3'
        )
        
        print("✅ TTS done")
        
        return send_file(
            BytesIO(response.content),
            mimetype='audio/mpeg',
            as_attachment=False
        )
    
    except Exception as e:
        print(f"❌ TTS error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Knowledge Base API Endpoints
# ============================================================================

@app.route('/knowledge/search', methods=['POST'])
def search_knowledge():
    """Direct search endpoint for testing"""
    try:
        data = request.json
        query = data.get('query', '')
        max_results = data.get('max_results', 5)
        
        results = knowledge_search.search(query, max_results)
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results),
            'source': 'google_drive' if os.getenv('GOOGLE_DRIVE_FOLDER_ID') else 'local'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/knowledge/stats', methods=['GET'])
def knowledge_stats():
    """Get stats about knowledge base"""
    try:
        if knowledge_search.ix:
            with knowledge_search.ix.searcher() as searcher:
                doc_count = searcher.doc_count_all()
                return jsonify({
                    'indexed': True,
                    'document_count': doc_count,
                    'index_path': knowledge_search.index_dir,
                    'source': 'google_drive' if os.getenv('GOOGLE_DRIVE_FOLDER_ID') else 'local',
                    'drive_folder': os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'N/A')
                })
        else:
            return jsonify({
                'indexed': False,
                'message': 'Run update_knowledge.py first',
                'google_drive_enabled': bool(os.getenv('GOOGLE_DRIVE_CREDENTIALS'))
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/knowledge/refresh', methods=['POST'])
def refresh_knowledge():
    """Trigger knowledge base refresh from Google Drive"""
    try:
        if not os.getenv('GOOGLE_DRIVE_CREDENTIALS'):
            return jsonify({
                'error': 'Google Drive not configured',
                'message': 'Set GOOGLE_DRIVE_CREDENTIALS in .env'
            }), 400
        
        # Import and run scanner
        from gdrive_document_scanner import GoogleDriveScanner
        
        scanner = GoogleDriveScanner()
        documents = scanner.scan_drive()
        
        if documents:
            scanner.save_index(documents)
            
            # Rebuild search index
            knowledge_search.create_index(documents)
            
            return jsonify({
                'success': True,
                'documents_scanned': len(documents),
                'total_words': sum(d['word_count'] for d in documents),
                'message': 'Knowledge base refreshed from Google Drive'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No documents found in Google Drive'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎤 HCT VOICE - GOOGLE DRIVE KNOWLEDGE BASE")
    print("="*60)
    
    # Check Google Drive configuration
    if os.getenv('GOOGLE_DRIVE_CREDENTIALS'):
        print("✅ Google Drive: Configured")
        print(f"📂 Folder ID: {os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1m6wF8p340oSbRvt0s0zAGFh1l8VgC8wI')}")
    else:
        print("⚠️  Google Drive: Not configured (using local files)")
        print("   Add GOOGLE_DRIVE_CREDENTIALS to .env to enable")
    
    # Check knowledge base
    if knowledge_search.load_index():
        print("✅ Knowledge base loaded")
    else:
        print("⚠️  No knowledge base found")
        if os.getenv('GOOGLE_DRIVE_CREDENTIALS'):
            print("   Run: python update_knowledge_gdrive.py")
        else:
            print("   Run: python update_knowledge.py")
    
    print("✅ Server: http://localhost:5002")
    print("✅ HD Audio (tts-1-hd)")
    print("✅ LangChain universal document parsing")
    print("✅ API endpoint: POST /knowledge/refresh (trigger Drive sync)")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)