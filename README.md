# 🎤 HCT AI Voice Agent

AI-powered voice and text assistant for Hazard Control Technologies, specializing in fire suppression solutions.

## 🌟 Features

- **Voice Mode** - Natural voice conversations with AI responses
- **Text Mode** - Traditional chat interface
- **Google Drive Integration** - Knowledge base synced from Google Drive
- **Universal Document Parsing** - Supports 15+ file types (PDF, DOCX, PPTX, XLSX, CSV, etc.)
- **Conversational AI** - 6-7 sentence detailed responses with intelligent follow-up questions
- **HD Audio** - High-quality text-to-speech using OpenAI's Nova voice

## 🚀 Live Demo

**URL:** [Coming soon - deploying to Render]

No login required - just visit and start talking!

## 📚 Knowledge Base

The agent has access to comprehensive information about:
- **F-500 Encapsulator Agent** - Multi-class fire suppression
- **HydroLock** - Vapor mitigation solutions
- **Pinnacle Foam** - PFAS-free Class A foam
- **Dust Wash** - Combustible dust control
- **Diamond Doser** - Proportioning systems

All product documentation is automatically synced from Google Drive.

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript
- **AI:** OpenAI GPT-4o-mini + Whisper + TTS
- **Document Processing:** LangChain + Google Drive API
- **Search:** Whoosh full-text search

## 📦 Supported File Types

- Office: PDF, DOCX, PPTX, XLSX
- Data: CSV, TSV
- Text: TXT, MD, HTML
- Images: JPG, PNG (with OCR)

## 🔧 Local Development

### Prerequisites
- Python 3.8+
- OpenAI API key
- Google Cloud service account (for Drive access)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/okapade/HCT-AI-Voice-Agent.git
cd HCT-AI-Voice-Agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file:
```bash
OPENAI_API_KEY=your-openai-api-key
GOOGLE_DRIVE_CREDENTIALS=/path/to/credentials.json
GOOGLE_DRIVE_FOLDER_ID=1m6wF8p340oSbRvt0s0zAGFh1l8VgC8wI
```

4. **Sync knowledge base**
```bash
python update_knowledge_gdrive.py
```

5. **Run the server**
```bash
python server.py
```

6. **Open in browser**
```
http://localhost:5002
```

## 📂 Project Structure
```
HCT-AI-Voice-Agent/
├── server.py                      # Flask server
├── gdrive_document_scanner.py     # Google Drive integration
├── update_knowledge_gdrive.py     # Knowledge base sync
├── knowledge_search.py            # Search engine
├── index.html                     # Main interface
├── script.js                      # Frontend logic
├── style.css                      # Styling
├── requirements.txt               # Python dependencies
├── assets/                        # Images and icons
└── README.md                      # This file
```

## 🔄 Updating Knowledge Base

When new documents are added to the Google Drive folder:
```bash
python update_knowledge_gdrive.py
```

Or trigger via API:
```bash
curl -X POST http://localhost:5002/knowledge/refresh
```

## 🌐 API Endpoints

- `GET /` - Main interface
- `GET /health` - System health check
- `POST /chat/stream` - Chat with AI (streaming)
- `POST /speak` - Text-to-speech
- `POST /knowledge/search` - Search knowledge base
- `POST /knowledge/refresh` - Sync from Google Drive
- `GET /knowledge/stats` - Knowledge base statistics

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | ✅ Yes |
| `GOOGLE_DRIVE_CREDENTIALS` | Path to service account JSON | ✅ Yes |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive folder ID | ✅ Yes |

## 📊 Performance

- **Response Time:** < 3 seconds
- **Supported Users:** Unlimited simultaneous users
- **Knowledge Base:** 31+ documents, 2.6M+ words
- **File Types:** 15+ formats supported

## 🎯 Use Cases

- **Sales Teams** - Quick product information during customer calls
- **Training** - Educational resource for fire suppression solutions
- **Customer Support** - Instant answers about HCT products
- **Trade Shows** - Interactive kiosk demonstrations

## 🤝 Contributing

This is a private project for Hazard Control Technologies.

## 📝 License

Proprietary - © 2025 Hazard Control Technologies

## 👥 Team

Developed by HCT Technology Department

## 📞 Support

For issues or questions, contact the HCT IT department.

---

**Made with ❤️ for Hazard Control Technologies**

*Empowering safer communities through innovative fire suppression technology*
