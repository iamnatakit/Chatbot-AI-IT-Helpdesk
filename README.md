# Chatbot AI Intent IT Helpdesk Support

This project features a modern React (Vite) frontend with beautiful glassmorphism UI, connected to a FastAPI Python backend powered by LangChain and FAISS.

## 🚀 How to Run

You will need two separate terminal windows.

### 1. Start the Backend (API)
Open a terminal and run the following commands:
```powershell
cd D:\Antigravity\Chatbot-AI-IT-Helpdesk\backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
> Note: The backend uses your existing `OPENAI_API_KEY` loaded from `.env`.

### 2. Start the Frontend (Web UI)
Open a second terminal and run the following commands:
```powershell
cd D:\Antigravity\Chatbot-AI-IT-Helpdesk\frontend
npm install
npm run dev
```

Then, open your browser to `http://localhost:3000` (or whatever URL Vite gives you) to see your beautiful new IT Helpdesk Chatbot!
