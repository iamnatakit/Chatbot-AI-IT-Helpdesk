import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.orm import Session
from database import init_db, get_db, ChatRecord

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# FAQ Data
FAQ_DATA = [
    {"intent": "password_reset", "question": "ลืมรหัสผ่านเข้าระบบ ต้องทำยังไง", "answer": "คุณสามารถรีเซ็ตรหัสผ่านด้วยตัวเองได้ที่ลิ้งก์นี้ครับ: https://helpdesk.company.com/reset-password"},
    {"intent": "password_reset", "question": "จำรหัสผ่านไม่ได้ เข้าเครื่องไม่ได้", "answer": "คุณสามารถรีเซ็ตรหัสผ่านด้วยตัวเองได้ที่ลิ้งก์นี้ครับ: https://helpdesk.company.com/reset-password"},
    {"intent": "network_issue", "question": "เข้าเน็ตไม่ได้ WiFi หลุด", "answer": "รบกวนลองปิดและเปิดสวิตช์ WiFi ที่เครื่องดูก่อนครับ หากยังไม่ได้ให้ลอง Restart เครื่อง 1 ครั้งครับ"},
    {"intent": "network_issue", "question": "อินเทอร์เน็ตใช้งานไม่ได้ ไม่มีสัญญาณ", "answer": "รบกวนลองปิดและเปิดสวิตช์ WiFi ที่เครื่องดูก่อนครับ หากยังไม่ได้ให้ลอง Restart เครื่อง 1 ครั้งครับ"},
    {"intent": "printer_issue", "question": "ปริ้นเอกสารไม่ออก เครื่องปริ้นเสีย", "answer": "เบื้องต้นรบกวนเช็คว่ากระดาษติดหรือไม่ และไฟสถานะที่เครื่องปริ้นเป็นสีเขียวหรือเปล่าครับ"},
    {"intent": "printer_issue", "question": "กระดาษติดในเครื่องปริ้น", "answer": "เบื้องต้นรบกวนเช็คว่ากระดาษติดหรือไม่ และไฟสถานะที่เครื่องปริ้นเป็นสีเขียวหรือเปล่าครับ"},
    {"intent": "printer_issue", "question": "ปริ้นเตอร์เสีย", "answer": "เบื้องต้นรบกวนเช็คว่ากระดาษติดหรือไม่ และไฟสถานะที่เครื่องปริ้นเป็นสีเขียวหรือเปล่าครับ"},
    {"intent": "hardware_issue", "question": "คอมเสีย computer เสีย เปิดไม่ติด", "answer": "รบกวนตรวจสอบปลั๊กไฟและสายชาร์จดูก่อนครับ หากยังเปิดไม่ติดเลย รบกวนแจ้งแผนก IT เพื่อนำเครื่องมาตรวจสอบครับ"},
]

def initialize_intent_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    docs = [
        Document(page_content=item["question"], metadata={"answer": item["answer"], "intent": item["intent"]})
        for item in FAQ_DATA
    ]
    vectorstore = QdrantVectorStore.from_documents(
        docs, 
        embeddings, 
        location=":memory:", 
        collection_name="faq_intents"
    )
    return vectorstore, embeddings

class HelpdeskChatbot:
    def __init__(self):
        print("Loading local embeddings...")
        self.vectorstore, self.embeddings = initialize_intent_vectorstore()
        
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model="meta-llama/llama-3.3-70b-instruct", # เปลี่ยนเป็นชื่อโมเดลฟรีหรือที่คุณต้องการบน OpenRouter เช่น google/gemini-2.5-flash
            temperature=0.2,
            default_headers={
                "HTTP-Referer": "http://localhost:3000", # แนะนำให้ใส่สำหรับ OpenRouter
                "X-Title": "IT Helpdesk Chatbot", # แนะนำให้ใส่สำหรับ OpenRouter
            }
        )
        # 1. สร้าง Classifier Prompt (ทำหน้าที่แยกหมวดหมู่ปัญหา)
        self.classifier_prompt = ChatPromptTemplate.from_messages([
            ("system", "คุณคือระบบคัดกรองหมวดหมู่ปัญหา IT จงอ่านปัญหาของผู้ใช้และตอบกลับด้วยคีย์เวิร์ดหมวดหมู่เพียง 1 คำเท่านั้น โดยเลือกจากรายการต่อไปนี้: [network, hardware, software, account, general] ห้ามตอบคำอื่นนอกจากนี้"),
            ("user", "ปัญหาที่แจ้ง: {question}")
        ])
        # ใช้ StrOutputParser เพื่อให้คำตอบออกมาเป็น String ธรรมดา
        self.classifier_chain = self.classifier_prompt | self.llm | StrOutputParser()
        
        # 2. สร้าง Prompts แยกตาม Domain (ผู้เชี่ยวชาญแต่ละด้าน)
        self.domain_prompts = {
            "network": ChatPromptTemplate.from_messages([
                ("system", "คุณคือ 'Network Engineer' ผู้เชี่ยวชาญด้านระบบเครือข่าย ให้คำแนะนำเรื่องอินเทอร์เน็ต, LAN, WiFi, Router อย่างเป็นขั้นตอนและตรวจสอบทีละจุด"),
                ("user", "{question}")
            ]),
            "hardware": ChatPromptTemplate.from_messages([
                ("system", "คุณคือ 'Hardware Technician' ช่างซ่อมอุปกรณ์ IT ให้คำแนะนำเบื้องต้นเกี่ยวกับการเช็คสภาพคอมพิวเตอร์ เครื่องปริ้นเตอร์ หน้าจอ และสายไฟต่างๆ"),
                ("user", "{question}")
            ]),
            "software": ChatPromptTemplate.from_messages([
                ("system", "คุณคือ 'Software Specialist' ให้คำแนะนำการใช้งานโปรแกรม การติดตั้งแอปพลิเคชัน การอัปเดตระบบปฏิบัติการ และแก้บั๊กหรือ Error ของซอฟต์แวร์"),
                ("user", "{question}")
            ]),
            "account": ChatPromptTemplate.from_messages([
                ("system", "คุณคือ 'System Admin' ผู้ดูแลระบบ ให้คำแนะนำเกี่ยวกับการรีเซ็ตรหัสผ่าน, การปลดล็อคผู้ใช้, การขอสิทธิ์การเข้าถึงข้อมูล อย่างปลอดภัยและรัดกุม"),
                ("user", "{question}")
            ]),
            "general": ChatPromptTemplate.from_messages([
                ("system", "คุณคือ 'IT Support Helpdesk' ทั่วไป คอยช่วยเหลือพนักงานบริษัทอย่างสุภาพ เป็นมิตร และให้คำปรึกษาเบื้องต้นได้"),
                ("user", "{question}")
            ])
        }
        
    def process_message(self, user_message: str):
        results = self.vectorstore.similarity_search_with_score(user_message, k=1)
        
        if results:
            best_match_doc, score = results[0]
            print(f"[Local Match Debug] Intent: {best_match_doc.metadata['intent']} | Score (Cosine): {score:.4f}")
            
            # Qdrant ใช้ Cosine Similarity เป็นค่าเริ่มต้น (คะแนนยิ่งมากยิ่งเหมือนเป๊ะ สูงสุดคือ 1.0)
            threshold = 0.85
            
            if score >= threshold:
                return {
                    "answer": best_match_doc.metadata['answer'],
                    "source": "local_intent",
                    "intent": best_match_doc.metadata['intent'],
                    "confidence": float(score)
                }
                
        try:
            if not os.getenv("OPENROUTER_API_KEY"):
                return {
                    "answer": "⚠️ ระบบต้องการต่อกับ LLM แต่คุณยังไม่ได้ใส่ OPENROUTER_API_KEY ในไฟล์ .env ของ Backend ครับ",
                    "source": "error"
                }
                
            # 1. ใช้ LLM Classifier วิเคราะห์หมวดหมู่
            raw_domain = self.classifier_chain.invoke({"question": user_message}).strip().lower()
            
            # กรองคำตอบของ LLM ให้อยู่ในหมวดหมู่ที่เรามีเท่านั้น
            valid_domains = ["network", "hardware", "software", "account", "general"]
            matched_domain = "general" # ค่าเริ่มต้นถ้าหาไม่เจอ
            for d in valid_domains:
                if d in raw_domain:
                    matched_domain = d
                    break
                    
            print(f"[LLM Classifier] ข้อความนี้ถูกจัดให้อยู่ใน Domain: {matched_domain.upper()}")
            
            # 2. เลือก Prompt ตาม Domain ที่วิเคราะห์ได้
            selected_prompt = self.domain_prompts[matched_domain]
            domain_chain = selected_prompt | self.llm
            
            # 3. ให้ LLM สร้างคำตอบด้วย Prompt ของ Domain นั้น
            response = domain_chain.invoke({"question": user_message})
            
            return {
                "answer": response.content,
                "source": f"LLM ({matched_domain})",
                "intent": matched_domain
            }
        except Exception as e:
            print(f"[System Error] LLM Chain Failed: {str(e)}")
            return {
                "answer": "ขออภัยครับ ขณะนี้ระบบ AI ผู้เชี่ยวชาญไม่สามารถให้บริการได้ชั่วคราว (ระบบขัดข้อง) หากเป็นปัญหาเร่งด่วน รบกวนติดต่อแผนก IT โดยตรงที่เบอร์สายใน 1111 หรือสร้าง Ticket ในระบบได้เลยครับ",
                "source": "system_fallback"
            }

app = FastAPI(title="IT Helpdesk Chatbot API")

@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = HelpdeskChatbot()

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    response = chatbot.process_message(req.message)
    
    # บันทึกประวัติการแชทลง Database
    new_record = ChatRecord(
        user_message=req.message,
        bot_response=response.get("answer", ""),
        source=response.get("source", ""),
        intent=response.get("intent", ""),
        confidence=response.get("confidence", None)
    )
    db.add(new_record)
    db.commit()
    
    return response

@app.get("/")
def read_root():
    return {"message": "IT Helpdesk Chatbot API is running"}
