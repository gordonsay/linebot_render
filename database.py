import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load Environment Arguments
load_dotenv()

# 設定 Supabase 連線
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_chat_history(user_id, role, content):
    """將對話紀錄存入 Supabase"""
    data = {"user_id": user_id, "role": role, "content": content}
    response = supabase.table("chat_history").insert(data).execute()
    return response

def get_recent_chat_history(user_id, limit=5):
    """從 Supabase 讀取最近 5 條對話歷史，轉換成 `ask_groq` 可接受的 `user_message` 格式"""
    
    response = supabase.table("chat_history") \
        .select("role, content") \
        .eq("user_id", user_id) \
        .order("timestamp", desc=True) \
        .limit(limit) \
        .execute()
    
    history_data = response.data[::-1]  # 確保最新對話在最後

    # **整理對話內容，確保 `content` 是字串**
    conversation = []
    for chat in history_data:
        role = "你" if chat["role"] == "user" else "狗蛋"
        content = str(chat["content"]).strip() if chat["content"] else ""

        # 過濾空白訊息
        if content:
            conversation.append(f"{role}: {content}")

    # **將對話合併為單一字串**
    if conversation:
        return "\n".join(conversation)
    
    return "這是你與狗蛋的對話！"  # 當沒有歷史紀錄時


