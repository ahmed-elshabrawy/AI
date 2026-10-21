from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import (
    search_documents,
    create_conversation,
    save_message,
    get_conversations,
    get_conversation_messages,
)


# =========================================================
# إعدادات API
# =========================================================

app = FastAPI(
    title="منصة دراستك API",
    version="1.0.0",
)


# =========================================================
# Models
# =========================================================

class QuestionRequest(BaseModel):
    question: str


class ConversationRequest(BaseModel):
    title: str


class MessageRequest(BaseModel):
    conversation_id: int
    content: str
    role: str = "user"


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.get("/")
def home():

    return {
        "message": "منصة دراستك API تعمل بنجاح",
        "docs": "/docs",
    }


# =========================================================
# فحص حالة API
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# =========================================================
# البحث عن إجابة
# =========================================================

@app.post("/ask")
def ask(data: QuestionRequest):

    q = data.question.strip()

    if not q:

        raise HTTPException(
            400,
            "السؤال فارغ",
        )

    rows = search_documents(
        q,
        1,
    )

    if not rows:

        return {
            "question": q,
            "answer": None,
            "found": False,
        }

    answer = str(
        rows[0][2] or ""
    ).strip()

    cid = create_conversation(q)

    save_message(
        cid,
        q,
        "user",
    )

    save_message(
        cid,
        answer,
        "assistant",
    )

    return {
        "question": q,
        "answer": answer,
        "found": True,
        "conversation_id": cid,
    }


# =========================================================
# إنشاء محادثة
# =========================================================

@app.post("/conversations")
def conversations(
    data: ConversationRequest,
):

    title = data.title.strip()

    if not title:

        raise HTTPException(
            400,
            "العنوان فارغ",
        )

    return {
        "id": create_conversation(title),
        "title": title,
    }


# =========================================================
# جلب المحادثات
# =========================================================

@app.get("/conversations")
def list_conversations(
    limit: int = 20,
):

    return [
        {
            "id": x[0],
            "title": x[1],
        }
        for x in get_conversations(limit)
    ]


# =========================================================
# جلب رسائل محادثة
# =========================================================

@app.get(
    "/conversations/{conversation_id}/messages"
)
def messages(
    conversation_id: int,
):

    return [
        {
            "id": x[0],
            "conversation_id": x[1],
            "content": x[2],
            "role": x[3],
            "created_at": (
                str(x[4])
                if x[4]
                else None
            ),
        }
        for x in get_conversation_messages(
            conversation_id
        )
    ]


# =========================================================
# إضافة رسالة
# =========================================================

@app.post("/messages")
def add_message(
    data: MessageRequest,
):

    save_message(
        data.conversation_id,
        data.content,
        data.role,
    )

    return {
        "message": "تم حفظ الرسالة بنجاح"
    }