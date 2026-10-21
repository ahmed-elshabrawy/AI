# منصة دراستك
واجهة Streamlit + MySQL + FastAPI.

تشغيل الواجهة:
`pip install -r requirements.txt`
`streamlit run main.py --server.port 8502`

تشغيل API:
`uvicorn api:app --reload --port 8000`

توثيق API:
`http://127.0.0.1:8000/docs`

ضع بيانات MySQL في ملف `.env` بناءً على `.env.example`.
