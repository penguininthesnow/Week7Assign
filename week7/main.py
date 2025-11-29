from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from datetime import datetime
import mysql.connector

app = FastAPI()

# 利用前端fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session
app.add_middleware(SessionMiddleware, secret_key="week7-key")

# 靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")


# 資料庫設定
def get_db():
    conn = mysql.connector.connect(
        user="root",
        password="12345678",
        host="localhost",
        database="website"
    )
    # 回傳 cursor 會帶 column 名稱
    conn.cursor(dictionary=True)
    return conn

# pydantic Models
class UpdateName(BaseModel):
    name: str

# 取得使用者登入
def get_logged_member(request: Request):
    return request.session.get("user")
     #{id, name, email}

# 直接打開html
@app.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse("/static/index.html")

# 註冊頁面
@app.post("/api/signup")
def signup(name: str=Form(), email: str=Form(), password: str=Form()):
    conn= get_db()
    cur = conn.cursor(dictionary=True)

    # 檢查email有無重複
    cur.execute("SELECT * FROM member WHERE email=%s", (email, ))
    exist = cur.fetchone()

    if exist:
        return {"error":True, "message":"此Email已被註冊過" } 
    
    # 新增會員
    cur.execute("""
        INSERT INTO member (name, email, password) VALUES (%s, %s, %s)""", (name, email, password))
    conn.commit()
    cur.close()
    conn.close()

    return{"ok": True}



# log in
@app.post("/api/login")
def login(request: Request, email: str=Form(), password: str=Form()):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT id, name, email FROM member WHERE email=%s AND password=%s", (email, password))
    row = cur.fetchone()

    if not row:
        return {"error":True}
    
    # 設定 session
    request.session["user"] = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
    }

    cur.close()
    conn.close()

    return{"ok": True}

# log out
@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return{"ok": True}

# member query api
@app.get("/api/member/{member_id}")
def query_member(request: Request, member_id: int):
    user = get_logged_member(request)

    # 未登入則 data=null
    if not user:
        return{"data": None}
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT id, name, email FROM member WHERE id=%s", (member_id,))
    row= cur.fetchone()

    if not row:
        return{"data":None}
    
    # 紀錄查詢(tip: 不能記錄自己查自己)
    if user["id"] !=row["id"]:
        cur.execute(
            """
            INSERT INTO query_log (member_id_being_queried, searcher_member_id, searcher_name, searched_at) VALUES (%s, %s, %s, %s) 
            """,
            (row["id"], user["id"], user["name"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    
    cur.close()
    conn.close()

    return{"data": row}
    

# Update Name API
@app.patch("/api/member")
def update_name(request: Request, body: UpdateName):
    user = get_logged_member(request)
    if not user:
        return{"error": True}

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE member SET name=%s WHERE id=%s", (body.name, user["id"]),)
    conn.commit()

    # 更新 session
    request.session["user"]["name"] = body.name

    cur.close()
    conn.close()

    return {"ok": True}

# 誰查詢了我 區塊
@app.get("/api/member/{member_id}/query-log")
def get_query_log(request: Request, member_id: int):
    user = get_logged_member(request)

    if not user:
        return{"data":None}
    
    if user["id"] !=member_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT searcher_name, searched_at 
        FROM query_log WHERE member_id_being_queried=%s ORDER BY searched_at DESC Limit 10
    """, (member_id,))

    rows = cur.fetchall()

    #格式化: 把顯示出來的時間去除" T "
    for row in rows:
        row["searched_at"] = row["searched_at"].strftime("%Y-%m-%d %H:%M:%S")
    cur.close()
    conn.close()

    return{"data": rows}

# 取得當前登入者
@app.get("/api/me")
def get_me(request: Request):
    user = get_logged_member(request)
    return {"data": user or None}