import os
import re

import pymysql
from dotenv import load_dotenv


# =========================================================
# تحميل متغيرات البيئة
# =========================================================

load_dotenv()


# =========================================================
# إعدادات قاعدة البيانات
# =========================================================

DB_HOST = os.getenv(
    "DB_HOST",
    "127.0.0.1",
)

DB_PORT = int(
    os.getenv(
        "DB_PORT",
        "3306",
    )
)

DB_USER = os.getenv(
    "DB_USER",
    "root",
)

DB_PASSWORD = os.getenv(
    "DB_PASSWORD",
    "",
)

DB_NAME = os.getenv(
    "DB_NAME",
    "ai_model_db",
)


# =========================================================
# الاتصال بقاعدة البيانات
# =========================================================

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
    )


# =========================================================
# أدوات مساعدة للتعامل مع الجداول
# =========================================================

def _cols(cur, table):
    cur.execute(
        f"SHOW COLUMNS FROM `{table}`"
    )

    return [
        x[0]
        for x in cur.fetchall()
    ]


def _pick(cols, names):
    return next(
        (
            x
            for x in names
            if x in cols
        ),
        None,
    )


# =========================================================
# إعدادات الذكاء الاصطناعي
# =========================================================

def get_ai_settings():

    out = {}

    try:

        c = get_connection()
        cur = c.cursor()

        cur.execute(
            """
            SELECT `key`, `value`, `type`
            FROM ai_settings
            WHERE is_active = 1
            """
        )

        for k, v, t in cur.fetchall():

            if t == "integer":

                try:
                    v = int(v)

                except:
                    pass

            elif t == "float":

                try:
                    v = float(v)

                except:
                    pass

            elif t == "boolean":

                v = str(v).lower() in (
                    "1",
                    "true",
                    "yes",
                    "on",
                )

            out[str(k)] = v

        cur.close()
        c.close()

    except Exception:
        pass

    return out


# =========================================================
# البحث داخل قاعدة البيانات
# =========================================================

def search_documents(question, limit=1):

    q = str(
        question or ""
    ).strip()

    if not q:
        return []

    words = [
        w
        for w in re.findall(
            r"[A-Za-z0-9\u0600-\u06FF]+",
            q,
        )
        if len(w) >= 2
    ]

    c = get_connection()
    cur = c.cursor()

    try:

        cols = _cols(
            cur,
            "ai_faqs",
        )

        ic = _pick(
            cols,
            [
                "id",
                "faq_id",
            ],
        )

        qc = _pick(
            cols,
            [
                "question",
                "faq_question",
                "title",
            ],
        )

        ac = _pick(
            cols,
            [
                "answer",
                "faq_answer",
                "content",
            ],
        )

        cc = _pick(
            cols,
            [
                "category",
            ],
        )

        kc = _pick(
            cols,
            [
                "keywords",
            ],
        )

        if not ic or not qc or not ac:

            raise RuntimeError(
                "جدول ai_faqs يجب أن يحتوي على "
                "id وquestion وanswer"
            )

        select = (
            f"`{ic}`,"
            f"`{qc}`,"
            f"`{ac}`,"
            +
            (
                f"`{cc}`"
                if cc
                else "NULL"
            )
            +
            ","
            +
            (
                f"`{kc}`"
                if kc
                else "NULL"
            )
        )

        cond = [
            f"`{qc}` LIKE %s",
            f"`{ac}` LIKE %s",
        ]

        params = [
            f"%{q}%",
            f"%{q}%",
        ]

        for w in words[:8]:

            cond.append(
                f"`{qc}` LIKE %s"
            )

            params.append(
                f"%{w}%"
            )

            if kc:

                cond.append(
                    f"`{kc}` LIKE %s"
                )

                params.append(
                    f"%{w}%"
                )

        cur.execute(
            f"""
            SELECT {select}
            FROM `ai_faqs`
            WHERE {' OR '.join(cond)}
            LIMIT %s
            """,
            params + [int(limit)],
        )

        return cur.fetchall()

    finally:

        cur.close()
        c.close()


# =========================================================
# إنشاء محادثة جديدة
# =========================================================

def create_conversation(title):

    c = get_connection()
    cur = c.cursor()

    try:

        cols = _cols(
            cur,
            "ai_conversations",
        )

        tc = _pick(
            cols,
            [
                "title",
                "name",
            ],
        )

        if not tc:

            raise RuntimeError(
                "جدول ai_conversations يحتاج title"
            )

        cur.execute(
            f"""
            INSERT INTO `ai_conversations`
            (`{tc}`)
            VALUES (%s)
            """,
            (
                str(title)[:255],
            ),
        )

        cid = cur.lastrowid

        c.commit()

        return cid

    finally:

        cur.close()
        c.close()


# =========================================================
# حفظ رسالة
# =========================================================

def save_message(
    conversation_id,
    content,
    role="user",
):

    c = get_connection()
    cur = c.cursor()

    try:

        cols = _cols(
            cur,
            "ai_messages",
        )

        fc = _pick(
            cols,
            [
                "conversation_id",
                "chat_id",
            ],
        )

        cc = _pick(
            cols,
            [
                "content",
                "message",
                "text",
                "body",
            ],
        )

        rc = _pick(
            cols,
            [
                "role",
                "sender",
                "message_type",
            ],
        )

        if not fc or not cc:

            raise RuntimeError(
                "جدول ai_messages يحتاج "
                "conversation_id وcontent"
            )

        names = [
            fc,
            cc,
        ]

        vals = [
            conversation_id,
            content,
        ]

        if rc:

            names.append(rc)
            vals.append(role)

        cur.execute(
            f"""
            INSERT INTO `ai_messages`
            ({','.join(f'`{x}`' for x in names)})
            VALUES ({','.join(['%s'] * len(vals))})
            """,
            vals,
        )

        c.commit()

    finally:

        cur.close()
        c.close()


# =========================================================
# جلب المحادثات القديمة
# =========================================================


def get_conversations(limit=20):
    c = get_connection()
    cur = c.cursor()

    try:
        cur.execute(
            """
            SELECT
                c.id,
                c.title
            FROM ai_conversations AS c
            LEFT JOIN ai_messages AS m
                ON m.conversation_id = c.id
            GROUP BY c.id, c.title
            ORDER BY
                MAX(m.created_at) DESC,
                c.created_at DESC,
                c.id DESC
            LIMIT %s
            """,
            (int(limit),),
        )

        return cur.fetchall()

    finally:
        cur.close()
        c.close()


# =========================================================
# جلب رسائل محادثة معينة
# =========================================================

def get_conversation_messages(cid):

    c = get_connection()
    cur = c.cursor()

    try:

        cols = _cols(
            cur,
            "ai_messages",
        )

        ic = _pick(
            cols,
            [
                "id",
                "message_id",
            ],
        )

        fc = _pick(
            cols,
            [
                "conversation_id",
                "chat_id",
            ],
        )

        cc = _pick(
            cols,
            [
                "content",
                "message",
                "text",
                "body",
            ],
        )

        rc = _pick(
            cols,
            [
                "role",
                "sender",
                "message_type",
            ],
        )

        dc = _pick(
            cols,
            [
                "created_at",
                "updated_at",
            ],
        )

        if not fc or not cc:
            return []

        s = [
            f"`{ic}`"
            if ic
            else "NULL",

            f"`{fc}`",
            f"`{cc}`",

            f"`{rc}`"
            if rc
            else "NULL",

            f"`{dc}`"
            if dc
            else "NULL",
        ]

        order = (
            f" ORDER BY `{dc}` ASC"
            if dc
            else ""
        )

        cur.execute(
            f"""
            SELECT {','.join(s)}
            FROM ai_messages
            WHERE `{fc}` = %s
            {order}
            """,
            (
                cid,
            ),
        )

        return cur.fetchall()

    finally:

        cur.close()
        c.close()


# =========================================================
# جلب جميع المستندات / الأسئلة
# =========================================================

def get_all_documents():

    c = get_connection()
    cur = c.cursor()

    try:

        cur.execute(
            "SELECT * FROM ai_faqs"
        )

        return cur.fetchall()

    finally:

        cur.close()
        c.close()


# =========================================================
# جلب المحادثات القديمة مع أول سؤال وإجابة
# =========================================================

def get_old_chats(limit=20):

    out = []

    for cid, title in get_conversations(limit):

        msgs = get_conversation_messages(cid)

        q = ""
        a = ""

        for m in msgs:

            role = (
                str(m[3] or "").lower()
                if len(m) > 3
                else ""
            )

            if role == "user" and not q:
                q = str(m[2] or "")

            if role == "assistant" and not a:
                a = str(m[2] or "")

        out.append(
            (
                cid,
                q or title,
                a,
            )
        )

    return out


# =========================================================
# حفظ الشات بالكامل
# =========================================================

def save_chat(
    question,
    answer,
):

    cid = create_conversation(
        question
    )

    save_message(
        cid,
        question,
        "user",
    )

    save_message(
        cid,
        answer,
        "assistant",
    )

    return cid