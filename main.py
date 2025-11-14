import os, re, json, openai, random, time, requests, shutil, datetime, wikipediaapi, spotipy
from pydub import AudioSegment
from flask import Flask, request, jsonify
from linebot.exceptions import InvalidSignatureError
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, MessagingApiBlob, QuickReply, QuickReplyItem, LocationAction
from linebot.v3.webhooks import MessageEvent, PostbackEvent, FollowEvent, LocationMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer, ImageMessage, PushMessageRequest, StickerMessage, AudioMessage
from linebot.v3.webhooks.models import AudioMessageContent
from linebot.v3.webhook import WebhookHandler
from groq import Groq
from dotenv import load_dotenv
from flask import send_from_directory
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyClientCredentials
from playwright.sync_api import sync_playwright
#from playwright_stealth import stealth_sync
import google.generativeai as genai  # ✅ 正确的导入方式
import PIL.Image
from io import BytesIO
from database import save_chat_history, get_recent_chat_history
import io, uuid
from mutagen.mp3 import MP3
from urllib.parse import quote
from langdetect import detect, DetectorFactory
from supabase import create_client, Client

# Load Environment Arguments
load_dotenv()

# Grab API Key from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
HUGGING_TOKENS = os.getenv("HUGGING_TOKENS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY 
GOOGLE_SEARCH_KEY = os.getenv("GOOGLE_SEARCH_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
CWB_API_KEY = os.getenv("CWB_API_KEY")
CWB_API_URL = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-D0047-091"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
BASE_URL = "https://render-linebot-masp.onrender.com"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
VRSS_API_KEY = os.getenv("VRSS_API_KEY")
NGROK_URL = os.getenv("NGROK_URL")
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 初始化 Spotipy
spotify_auth = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify_api = spotipy.Spotify(auth_manager=spotify_auth)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

# Grab Allowed Users and Group ID from .env
allowed_users_str = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = {uid.strip() for uid in allowed_users_str.split(",") if uid.strip()}
allowed_groups_str = os.getenv("ALLOWED_GROUPS", "")
ALLOWED_GROUPS = {gid.strip() for gid in allowed_groups_str.split(",") if gid.strip()}
allowed_users_BADEGG_str = os.getenv("ALLOWED_BADEGG_USERS", "")
ALLOWED_BADEGG_USERS = {uid.strip() for uid in allowed_users_str.split(",") if uid.strip()}
allowed_groups_BADEGG_str = os.getenv("ALLOWED_BADEGG_GROUPS", "")
ALLOWED_BADEGG_GROUPS = {gid.strip() for gid in allowed_groups_str.split(",") if gid.strip()}
max_title_length = 70

# Initailize LINE API (v3)
config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
messaging_api = MessagingApi(ApiClient(config))
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = Groq(api_key=GROQ_API_KEY)
messaging_api_blob = MessagingApiBlob(ApiClient(config))

# Initialize Flask 
app = Flask(__name__)

video_batches = {}  # 存不同批次的影片
batch_index = {}  # 追蹤用戶當前批次
video_list = {}  # 存放不同用戶的完整影片列表
video_index = {}  # 存放每個用戶目前的影片索引
user_state = {}
user_mode = {}
user_videos_choice = {}

# sticker list
OFFICIAL_STICKERS = [
    ("446", "1988"),  # Moon: Special Edition
    ("446", "1989"),
    ("446", "1990"),
    ("446", "1991"),
    ("446", "1992"),
    ("446", "1993"),  
    ("446", "1994"),
    ("446", "1995"),
    ("446", "1996"),
    ("446", "1997"),
    ("446", "1998"),  
    ("446", "1999"),
    ("446", "2000"),
    ("446", "2001"),
    ("446", "2002"),
    ("446", "2003"),  
    ("446", "2004"),
    ("446", "2005"),
    ("446", "2006"),
    ("446", "2007"),
    ("446", "2008"),  
    ("446", "2009"),
    ("446", "2010"),
    ("446", "2011"),
    ("446", "2012"),
    ("446", "2013"),  
    ("446", "2014"),
    ("446", "2015"),
    ("446", "2016"),
    ("446", "2017"),
    ("446", "2018"),  
    ("446", "2019"),
    ("446", "2020"),
    ("446", "2021"),
    ("446", "2022"),
    ("446", "2023"),  
    ("446", "2024"),
    ("446", "2025"),
    ("446", "2026"),
    ("446", "2027"),
    ("789", "10855"),  # Sally: Special Edition
    ("789", "10856"),
    ("789", "10857"),
    ("789", "10858"),
    ("789", "10859"),
    ("789", "10860"), 
    ("789", "10861"),
    ("789", "10862"),
    ("789", "10863"),
    ("789", "10864"),
    ("789", "10865"),  
    ("789", "10866"),
    ("789", "10867"),
    ("789", "10868"),
    ("789", "10869"),
    ("789", "10870"), 
    ("789", "10871"),
    ("789", "10872"),
    ("789", "10873"),
    ("789", "10874"),
    ("789", "10875"),
    ("789", "10876"),
    ("789", "10877"),
    ("789", "10878"),
    ("789", "10879"),
    ("789", "10880"), 
    ("789", "10881"),
    ("789", "10882"),
    ("789", "10883"),
    ("789", "10884"),
    ("789", "10885"),  
    ("789", "10886"),
    ("789", "10887"),
    ("789", "10888"),
    ("789", "10889"),
    ("789", "10890"), 
    ("789", "10891"),
    ("789", "10892"),
    ("789", "10893"),
    ("789", "10894"),
    ("6136", "10551376"),  # LINE Characters: Making Amends
    ("6136", "10551377"),
    ("6136", "10551378"),
    ("6136", "10551379"),
    ("6136", "10551380"),
    ("6136", "10551381"),  
    ("6136", "10551382"),
    ("6136", "10551383"),
    ("6136", "10551384"),
    ("6136", "10551385"),
    ("6136", "10551386"), 
    ("6136", "10551387"),
    ("6136", "10551388"),
    ("6136", "10551389"),
    ("6136", "10551390"),
    ("6136", "10551391"), 
    ("6136", "10551392"),
    ("6136", "10551393"),
    ("6136", "10551394"),
    ("6136", "10551395"),
    ("6136", "10551396"),
    ("6136", "10551397"),
    ("6136", "10551398"),
    ("6136", "10551399"),
    ("6325", "10979904"),  # Brown and Cony Fun Size Pack
    ("6325", "10979905"),
    ("6325", "10979906"),
    ("6325", "10979907"),
    ("6325", "10979908"),
    ("6325", "10979909"),
    ("6325", "10979910"),
    ("6325", "10979911"),
    ("6325", "10979912"),
    ("6325", "10979913"),
    ("6325", "10979914"),  
    ("6325", "10979915"),
    ("6325", "10979916"),
    ("6325", "10979917"),
    ("6325", "10979918"),
    ("6325", "10979919"),  
    ("6325", "10979920"),
    ("6325", "10979921"),
    ("6325", "10979922"),
    ("6325", "10979923"),
    ("6325", "10979924"), 
    ("6325", "10979925"),
    ("6325", "10979926"),
    ("6325", "10979927"),
    ("8525", "16581290"), # LINE Characters: Pretty Phrases
    ("8525", "16581291"),
    ("8525", "16581292"),
    ("8525", "16581293"),
    ("8525", "16581294"),
    ("8525", "16581295"),
    ("8525", "16581296"),
    ("8525", "16581297"),
    ("8525", "16581298"),
    ("8525", "16581299"),
    ("8525", "16581300"),
    ("8525", "16581301"),
    ("8525", "16581302"),
    ("8525", "16581303"),
    ("8525", "16581304"),
    ("8525", "16581305"),
    ("8525", "16581306"),
    ("8525", "16581307"),
    ("8525", "16581308"),
    ("8525", "16581309"),
    ("8525", "16581310"),
    ("8525", "16581311"),
    ("8525", "16581312"),
    ("8525", "16581313"),
    ("11537", "52002734"), # Brown & Cony & Sally: Animated Special
    ("11537", "52002735"),
    ("11537", "52002736"),
    ("11537", "52002737"),
    ("11537", "52002738"),
    ("11537", "52002739"),
    ("11537", "52002740"),
    ("11537", "52002741"),
    ("11537", "52002742"),
    ("11537", "52002743"),
    ("11537", "52002744"),
    ("11537", "52002745"),
    ("11537", "52002746"),
    ("11537", "52002747"),
    ("11537", "52002748"),
    ("11537", "52002749"),
    ("11537", "52002750"),
    ("11537", "52002751"),
    ("11537", "52002752"),
    ("11537", "52002753"),
    ("11537", "52002754"),
    ("11537", "52002755"),
    ("11537", "52002756"),
    ("11537", "52002757"),
    ("11537", "52002758"),
    ("11537", "52002759"),
    ("11537", "52002760"),
    ("11537", "52002761"),
    ("11537", "52002762"),
    ("11537", "52002763"),
    ("11537", "52002764"),
    ("11537", "52002765"),
    ("11537", "52002766"),
    ("11537", "52002767"),
    ("11537", "52002768"),
    ("11537", "52002769"),
    ("11537", "52002770"),
    ("11537", "52002771"),
    ("11537", "52002772"),
    ("11537", "52002773"),
    ("11538", "51626494"), # CHOCO & Friends: Animated Special
    ("11538", "51626495"),
    ("11538", "51626496"),
    ("11538", "51626497"),
    ("11538", "51626498"),
    ("11538", "51626499"),
    ("11538", "51626500"),
    ("11538", "51626501"),
    ("11538", "51626502"),
    ("11538", "51626503"),
    ("11538", "51626504"),
    ("11538", "51626505"),
    ("11538", "51626506"),
    ("11538", "51626507"),
    ("11538", "51626508"),
    ("11538", "51626509"),
    ("11538", "51626510"),
    ("11538", "51626511"),
    ("11538", "51626512"),
    ("11538", "51626513"),
    ("11538", "51626514"),
    ("11538", "51626515"),
    ("11538", "51626516"),
    ("11538", "51626517"),
    ("11538", "51626518"),
    ("11538", "51626519"),
    ("11538", "51626520"),
    ("11538", "51626521"),
    ("11538", "51626522"),
    ("11538", "51626523"),
    ("11538", "51626524"),
    ("11538", "51626525"),
    ("11538", "51626526"),
    ("11538", "51626527"),
    ("11538", "51626528"),
    ("11538", "51626529"),
    ("11538", "51626530"),
    ("11538", "51626531"),
    ("11538", "51626532"),
    ("11538", "51626533"),
    ("11539", "52114110"), #UNIVERSTAR BT21: Animated Specia
    ("11539", "52114111"),
    ("11539", "52114112"),
    ("11539", "52114113"),
    ("11539", "52114114"),
    ("11539", "52114115"),
    ("11539", "52114116"),
    ("11539", "52114117"),
    ("11539", "52114118"),
    ("11539", "52114119"),
    ("11539", "52114120"),
    ("11539", "52114121"),
    ("11539", "52114122"),
    ("11539", "52114123"),
    ("11539", "52114124"),
    ("11539", "52114125"),
    ("11539", "52114126"),
    ("11539", "52114127"),
    ("11539", "52114128"),
    ("11539", "52114129"),
    ("11539", "52114130"),
    ("11539", "52114131"),
    ("11539", "52114132"),
    ("11539", "52114133"),
    ("11539", "52114134"),
    ("11539", "52114135"),
    ("11539", "52114136"),
    ("11539", "52114137"),
    ("11539", "52114138"),
    ("11539", "52114139"),
    ("11539", "52114140"),
    ("11539", "52114141"),
    ("11539", "52114142"),
    ("11539", "52114143"),
    ("11539", "52114144"),
    ("11539", "52114145"),
    ("11539", "52114146"),
    ("11539", "52114147"),
    ("11539", "52114148"),
    ("11539", "52114149")
]

# 城市對應表（避免輸入錯誤）
CITY_MAPPING = {
    # 台灣縣市
    "台北": "Taipei",
    "新北": "New Taipei",
    "桃園": "Taoyuan",
    "台中": "Taichung",
    "台南": "Tainan",
    "高雄": "Kaohsiung",
    "基隆": "Keelung",
    "新竹": "Hsinchu",
    "嘉義": "Chiayi",
    "苗栗": "Miaoli",
    "彰化": "Changhua",
    "南投": "Nantou",
    "雲林": "Yunlin",
    "嘉義": "Chiayi",
    "屏東": "Pingtung",
    "宜蘭": "Yilan",
    "花蓮": "Hualien",
    "台東": "Taitung",
    "澎湖": "Penghu",
    "金門": "Kinmen",
    "連江": "Lienchiang",  # 馬祖

    # 世界大都市
    "東京": "Tokyo",
    "大阪": "Osaka",
    "京都": "Kyoto",
    "首爾": "Seoul",
    "釜山": "Busan",
    "曼谷": "Bangkok",
    "新加坡": "Singapore",
    "吉隆坡": "Kuala Lumpur",
    "胡志明": "Ho Chi Minh City",
    "河內": "Hanoi",
    "雅加達": "Jakarta",
    "香港": "Hong Kong",
    "澳門": "Macau",
    "北京": "Beijing",
    "上海": "Shanghai",
    "廣州": "Guangzhou",
    "深圳": "Shenzhen",
    "倫敦": "London",
    "巴黎": "Paris",
    "柏林": "Berlin",
    "阿姆斯特丹": "Amsterdam",
    "羅馬": "Rome",
    "馬德里": "Madrid",
    "紐約": "New York",
    "洛杉磯": "Los Angeles",
    "芝加哥": "Chicago",
    "舊金山": "San Francisco",
    "華盛頓": "Washington",
    "多倫多": "Toronto",
    "溫哥華": "Vancouver",
    "墨西哥城": "Mexico City",
    "布宜諾斯艾利斯": "Buenos Aires",
    "悉尼": "Sydney",
    "墨爾本": "Melbourne",
    "開普敦": "Cape Town",
    "開羅": "Cairo",
    "杜拜": "Dubai",
    "伊斯坦堡": "Istanbul",
    "莫斯科": "Moscow"
}

ACTRESS_AV_NAMES = ["三上悠亞", "橋本有菜", "篠田優", "桃乃木香奈", "波多野結衣", "Julia", "天海翼", "葵司", "深田詠美", "明日花綺羅", "小倉由菜", "白石茉莉奈", "夢乃愛華", \
                    "山岸逢花", "河北彩", "小島南", "相澤南", "涼森玲夢", "架乃由羅", "伊藤舞雪", "藤森里穂", "星宮一花", "櫻空桃", "明里紬", "高橋聖子", "七澤美亞", "楓可憐", \
                    "岬奈奈美", "八乃翼", "美谷朱里", "水卜櫻", "戶田真琴", "星奈愛", "君島美緒", "佐佐木明希", "松本一香", "石川澪", "東條夏", "小花暖", "倉多真央", "蓮實克蕾兒", "樞木葵", "渚光希"    ]

ACTRESS_AV_SERIES = ["NTR", "人妻", "痴女", "制服", "未亡", "交換", "按摩", "精油", "鄰居", "電車", "遊戲", "面試", \
                    "眼鏡", "家庭教師", "女上司", "女同學", "秘書", "女僕", "美少女"]

ACTRESS_AV_DESCRIPTIONS = {
    "三上悠亞": "甜美誘惑的國民偶像",
    "橋本有菜": "清純靈動的校園女神",
    "篠田優": "成熟嫵媚的人妻代表",
    "桃乃木香奈": "俏皮可愛的水果甜心",
    "波多野結衣": "多才多藝的E級萬能女王",
    "Julia": "驚艷J級的夢幻尤物",
    "天海翼": "優雅氣質的飛行天使",
    "葵司": "知性冷艷的高級秘書",
    "深田詠美": "夢幻誘惑的眼鏡家庭教師",
    "明日花綺羅": "華麗耀眼的G級花魁公主",
    "小倉由菜": "青春活潑的鄰家少女",
    "白石茉莉奈": "溫柔成熟的熟女姐姐",
    "夢乃愛華": "夢幻浪漫的愛情精靈",
    "山岸逢花": "氣質出眾的新聞主播",
    "河北彩": "清新自然的彩虹女孩",
    "小島南": "嬌小玲瓏的南方甜心",
    "相澤南": "陽光燦爛的南國美人",
    "涼森玲夢": "清涼舒爽的夏日夢境",
    "架乃由羅": "優雅迷人的藝術畫像",
    "伊藤舞雪": "純白柔美的冬日精靈",
    "藤森里穂": "溫暖貼心的森林姐姐",
    "星宮一花": "星光閃耀的花樣美人",
    "櫻空桃": "甜美誘人的桃色櫻花",
    "明里紬": "細膩柔美的紡織少女",
    "高橋聖子": "高雅聖潔的文藝女子",
    "七澤美亞": "小巧可愛的七彩寶石",
    "楓可憐": "纖細可憐的秋日紅葉",
    "岬奈奈美": "海風輕盈的甜美浪花",
    "八乃翼": "性感飛揚的靈動小鳥",
    "美谷朱里": "熱情奔放的紅寶舞者",
    "水卜櫻": "清新飽滿的H級櫻桃女孩",
    "戶田真琴": "文靜清秀的文學少女",
    "星奈愛": "溫柔星光的愛情使者",
    "君島美緒": "高貴冷艷的島嶼女王",
    "佐佐木明希": "明亮活潑的陽光女孩",
    "松本一香": "清新自然的松林仙子",
    "石川澪": "靈動輕盈的溪流精靈",
    "東條夏": "熱情火辣的夏日辣妹",
    "小花暖": "溫暖柔軟的小花仙子",
    "倉多真央": "豐滿真摯的倉庫甜心",
    "蓮實克蕾兒": "霸氣性感的蓮花戰士",
    "樞木葵": "俏皮靈動的向日葵",
    "渚光希": "閃耀海灘的希望之光"
}

ACTRESS_AV_SERIES_DESCRIPTIONS = {
    "NTR": "偷心背叛的刺激劇情",
    "人妻": "成熟女性的溫柔誘惑",
    "痴女": "主動出擊的性感獵人",
    "制服": "青春校園的純情幻想",
    "未亡": "孤單寡婦的秘密心事",
    "交換": "禁忌遊戲的刺激體驗",
    "按摩": "放鬆身心的隱秘觸感",
    "精油": "滑膩香氛的誘人療癒",
    "鄰居": "隔壁傳來的曖昧氣息",
    "電車": "擁擠車廂的緊張邂逅",
    "遊戲": "虛擬與現實的挑逗對決",
    "面試": "壓力下的意外展開",
    "眼鏡": "知性外表下的反差魅力",
    "家庭教師": "課桌下的私密教學",
    "女上司": "職場權威的性感支配",
    "女同學": "青澀回憶的甜蜜悸動",
    "秘書": "辦公桌旁的貼身誘惑",
    "女僕": "服侍主人的溫順幻想",
    "美少女": "純真與魅力的完美結合"
}

LANGUAGE_MAP = {
    "ar": "ar-eg",
    "bg": "bg-bg",
    "ca": "ca-es",
    "zh-cn": "zh-cn",
    "zh-tw": "zh-tw",
    "zh": "zh-cn",    # 偵測到 "zh" 時，預設使用簡體中文
    "hr": "hr-hr",
    "cs": "cs-cz",
    "da": "da-dk",
    "nl": "nl-nl",
    "en": "en-us",    # 英文預設使用美式英語
    "et": "et-ee",
    "fi": "fi-fi",
    "fr": "fr-fr",
    "de": "de-de",
    "el": "el-gr",
    "he": "he-il",
    "hu": "hu-hu",
    "id": "id-id",
    "it": "it-it",
    "ja": "ja-jp",
    "ko": "ko-kr",
    "lv": "lv-lv",
    "lt": "lt-lt",
    "no": "no-no",
    "pl": "pl-pl",
    "pt": "pt-br",   # 這裡預設使用巴西葡萄牙語
    "ro": "ro-ro",
    "ru": "ru-ru",
    "sr": "sr-rs",
    "sk": "sk-sk",
    "sl": "sl-si",
    "es": "es-es",   # 預設使用西班牙語（西班牙）
    "sv": "sv-se",
    "tr": "tr-tr",
    "uk": "uk-ua",
    "vi": "vi-vn"
}


GENERAL_MOVIE_SERIES = ["動作片", "喜劇片", "愛情片", "科幻片", "恐怖片", "劇情片", "戰爭片", "動畫片"]

NETFLIX_DRAMA_SERIES = ["劇情影集", "動作影集", "喜劇影集", "愛情影集", "科幻影集", "恐怖影集", "戰爭影集", "動畫影集"]

GENERAL_DRAMA_SERIES = ["陸劇", "港劇", "台劇", "日劇", "韓劇", "美劇", "海外劇"]

GENERAL_ANIME_SERIES = ["港台動漫", "日韓動漫", "大陸動漫", "歐美動漫", "海外動漫"]

# Record AI model choosen by User
user_ai_choice = {}
# Record AI model choosen by User
user_personality_choice = {}

@app.route("/ping", methods=["GET", "POST"])
def ping():
    return "OK", 200  # 不論是 GET 或 POST 都回應 OK

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status="ok"), 200  # ✅ 回傳 HTTP 200 表示正常

@app.route("/", methods=["GET"])
def home():
    return "狗蛋 啟動！"

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "未收到簽名")
    body = request.get_data(as_text=True)

    # 🔍 Log Webhook Data
    print(f"📢 [DEBUG] Webhook Received: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ [ERROR] Webhook Signature 驗證失敗")
        return "Invalid signature", 400
    except Exception as e:
        print(f"❌ [ERROR] Webhook 處理錯誤: {e}")

    return "OK", 200

@handler.add(FollowEvent)
def handle_follow(event):
    """當用戶加好友時，立即發送選單"""
    command_list = (
            "📝 支援的指令：\n"
            "1. 換模型: 更換 AI 語言模型 \n\t\t（預設為 Deepseek-R1）\n"
            "2. 換人格: 更換 AI 人格 \n\t\t（預設為 正宗狗蛋）\n"
            "3. 狗蛋出去: 機器人離開群組\n"
            "4. 當前模型: 機器人現正使用的模型\n"
            "5. 狗蛋生成: 生成圖片\n"
            "6. 狗蛋介紹: 人物或角色的說明\n\t\t (僅供參考) \n"
            "7. 狗蛋搜圖: 即時搜圖\n"
            "8. 狗蛋唱歌: 串連Spotify試聽\n"
            "9. 狗蛋氣象: 確認當前天氣\n"
            "10. 狗蛋預報: 確認三天天氣預報\n"
            "11. 狗蛋情勒: 狗蛋的超能力"
        )
    reply_request = ReplyMessageRequest(
        replyToken=event.reply_token,
        messages=[TextMessage(text=command_list)]
    )
    send_response(event, reply_request)

# ----------------------------------
# Support Function
# ----------------------------------
def safe_api_call(api_func, request_obj, retries=3, backoff_factor=1.0):
    for i in range(retries):
        try:
            return api_func(request_obj)
        except Exception as e:
            if "429" in str(e):
                wait_time = backoff_factor * (2 ** i)
                print(f"🔄 Rate limit: {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                print(f"❌ API call error: {e}")
                raise
    raise Exception("API call failed after retries")

def send_limit_message(event):
    """
    嘗試使用 push_message 發送「很抱歉，使用已達上限」訊息，
    並採用指數退避機制重試若遇到 429 錯誤。
    """
    target_id = event.source.group_id if event.source.type == "group" else event.source.user_id
    limit_msg = TextMessage(text="很抱歉，使用已達上限")
    push_req = PushMessageRequest(
        to=target_id,
        messages=[limit_msg]
    )
    retries = 3
    backoff_factor = 1.0
    for i in range(retries):
        try:
            messaging_api.push_message(push_req)
            print("成功發送使用已達上限訊息給使用者")
            return
        except Exception as err:
            err_str = str(err)
            if "429" in err_str or "monthly limit" in err_str:
                wait_time = backoff_factor * (2 ** i)
                print(f"push_message 發送失敗 (429)，{wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                print(f"push_message 發送失敗: {err}")
                break
    print("最終無法發送使用已達上限訊息給使用者")

# ----------------------------------
# Main Function
# ----------------------------------
# Response Function - Sort by event "reply_message" or "push_message"
def send_response(event, reply_request):
    """
    發送回覆訊息：如果發送失敗且捕捉到 429（超過使用量限制），
    嘗試改用 send_limit_message() 來告知使用者。
    """
    try:
        if getattr(event, "_is_audio", False):
            to = event.source.group_id if event.source.type == "group" else event.source.user_id
            push_req = PushMessageRequest(
                to=to,
                messages=reply_request.messages
            )
            messaging_api.push_message(push_req)
        else:
            messaging_api.reply_message(reply_request)
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "monthly limit" in err_str:
            print("❌ 捕捉到 429 錯誤，表示使用已達上限")
            send_limit_message(event)
        else:
            print(f"❌ LINE Reply Error: {e}")

# TextMessage Handler
@handler.add(MessageEvent)  # 預設處理 MessageEvent
def handle_message(event):
    """處理 LINE Picture訊息，根據指令回覆或提供 AI 服務"""
    t_ini = time.time()
    if event.message.type == "image":
        # ✅ 下载 LINE 服务器上的图片
        message_id = event.message.id
        message_content = messaging_api_blob.get_message_content(message_id)

        # ✅ 保存图片
        image_path = f"/tmp/{message_id}.jpg"
        with open(image_path, "wb") as fd:
            fd.write(message_content)

        # ✅ 使用 `Gemini` 进行详细分析
        image = PIL.Image.open(image_path)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            [
                {
                    "text": """
                            請用繁體中文 用朋友聊天的自然語氣 描述照片內容
                            語氣微靠北一點 但安全不冒犯
                            不要問問題 不要驚嘆 不要太正式 標點符號隨性都可以
                            
                            回覆一定要很短 2~3 句就好 不要超過 30 字
                            先講你看到的內容 再補一句輕鬆的小吐槽
                            
                            示例：
                            - 人物：看起來滿放鬆的啦 很像今天不想努力
                            - 場景：地方很安靜 有種想直接躺平的fu
                            - 物品：桌面乾淨很多欸 比我那坨災難好看多了
                            
                            保持自然 隨性 微靠北 但務必極短
                            """
                },
                image   # 直接傳 PIL Image
            ]
        )

        # ✅ 获取 `Gemini` 生成的详细描述
        gemini_text = response.text.strip()

        # ✅ 删除本地图片
        os.remove(image_path)
        # ✅ 解决 `LINE` 长度限制（单条消息最多 2000 字）
        messages = []
        while gemini_text:
            messages.append(TextMessage(text=gemini_text[:2000]))  # 取 2000 字以内
            gemini_text = gemini_text[2000:]  # 截取剩余部分

        # ✅ 发送 AI 生成的回复
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )
        return

    # detect type is sticker
    if event.message.type == "sticker" :
        user_id = event.source.user_id
        group_id = event.source.group_id if event.source.type == "group" else None
        # print("✅ 偵測到貼圖訊息！")
        if group_id and random.random() < 0.30 or not group_id:
            reply_token = event.reply_token
            # **隨機選擇一個貼圖**
            package_id, sticker_id = random.choice(OFFICIAL_STICKERS)
            print(f"🎨 選擇的貼圖 package_id: {package_id}, sticker_id: {sticker_id}")

            sticker_message = StickerMessage(package_id=package_id, sticker_id=sticker_id)
            reply_req = ReplyMessageRequest(replyToken=reply_token, messages=[sticker_message])

            try:
                messaging_api.reply_message(reply_req)
                # print("✅ 成功回應貼圖訊息！")
                return
            except Exception as e:
                # print(f"❌ 回應貼圖訊息失敗，錯誤：{e}")
                if time.time-t_ini > 5:
                    reply_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text="狗蛋還在籠子裡睡, 請再呼喊牠一次🐕")]
                    )
                    send_response(event, reply_request)
                return

    # 檢查 event.message 是否存在
    if not hasattr(event, "message"):
        return

    # 判斷 message 資料型態：
    if isinstance(event.message, dict):
        msg_type = event.message.get("type")
        msg_text = event.message.get("text", "")
    elif hasattr(event.message, "type"):
        msg_type = event.message.type
        msg_text = getattr(event.message, "text", "")
    else:
        return
    
    # 若事件已經被處理過，則直接返回
    if getattr(event, "_processed", False):
        return

    # 如果是從語音轉錄而來的事件，也可以標記為已處理
    if getattr(event, "_is_audio", False):
        event._processed = True

    if msg_type != "text":
        return

    # 取得使用者與群組資訊（採用 snake_case）
    user_message = msg_text.strip().lower()
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else None

    if "狗蛋儲存" in user_message:
        user_message_history = user_message.replace("狗蛋儲存", "").strip()
        # 儲存使用者訊息
        save_to_data = f"{user_id} talk with ai about contents:{user_message_history}"
        save_chat_history(user_id, "user", save_to_data)
        # 取得最近 5 條對話歷史
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text="save done")]
        )
        send_response(event, reply_request)
        return

    # 檢查目前選用的 AI 模型
    if group_id and group_id in user_ai_choice:
        ai_model = user_ai_choice[group_id]
    else:
        ai_model = user_ai_choice.get(user_id, "GPT_4o_Mini")

    # 檢查目前選用的 AI 人格
    if group_id and group_id in user_personality_choice:
        ai_model = user_personality_choice[group_id]
    else:
        ai_model = user_personality_choice.get(user_id, "normal_egg")

    print(f"📢 [DEBUG] {user_id if not group_id else group_id} 當前模型: {ai_model}")

    # (1) 「給我id」：若訊息中同時包含「給我」和「id」
    if "給我" in user_message and "id" in user_message:
        reply_text = f"您的 User ID 是：\n{user_id}"
        if group_id:
            reply_text += f"\n這個群組的 ID 是：\n{group_id}"
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        send_response(event, reply_request)
        return

    # (2) 「群組id」：在群組中，若訊息中同時包含「群組」和「id」
    if group_id and "群組" in user_message and "id" in user_message:
        reply_text = f"這個群組的 ID 是：\n{group_id}"
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        send_response(event, reply_request)
        return

    # (2-2) 若為個人訊息卻要求群組指令，回覆錯誤訊息
    if group_id is None and "群組" in user_message and "id" in user_message:
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text="❌ 此指令僅限群組使用")]
        )
        send_response(event, reply_request)
        return
    
    # (2-3) Random response from default pool
    if "狗蛋" in user_message and "情勒" in user_message:
        try :
            target_id = group_id if group_id is not None else user_id
            random_reply(event.reply_token, target_id, messaging_api)
            return
        except Exception as e:
            if time.time-t_ini > 5:
                reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="狗蛋還在籠子裡睡, 請再呼喊牠一次🐕")]
                )
                send_response(event, reply_request)
            return

    # (3) 「狗蛋指令」：列出所有支援指令
    if "指令" in user_message and "狗蛋" in user_message:
        command_list = (
            "📝 支援的指令：\n"
            "1. 換模型: 更換 AI 語言模型 \n\t\t（預設為 Deepseek-R1）\n"
            "2. 換人格: 更換 AI 人格 \n\t\t（預設為 正宗狗蛋）\n"
            "3. 狗蛋出去: 機器人離開群組\n"
            "4. 當前模型: 機器人現正使用的模型\n"
            "5. 狗蛋生成: 生成圖片\n"
            "6. 狗蛋介紹: 人物或角色的說明\n\t\t (僅供參考) \n"
            "7. 狗蛋搜圖: 即時搜圖\n"
            "8. 狗蛋唱歌: 串連Spotify試聽\n"
            "9. 狗蛋氣象: 確認當前天氣\n"
            "10. 狗蛋預報: 確認三天天氣預報\n"
            "11. 狗蛋情勒: 狗蛋的超能力"
        )
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=command_list)]
        )
        send_response(event, reply_request)
        return

    # # (4) AI 服務指令：檢查使用權限
    # if event.source.type != "group":
    #     if user_id not in ALLOWED_USERS:
    #         reply_request = ReplyMessageRequest(
    #             replyToken=event.reply_token,
    #             messages=[TextMessage(text="❌ 你沒有權限使用 AI 服務")]
    #         )
    #         send_response(event, reply_request)
    #         return
    # else:
    #     if group_id not in ALLOWED_GROUPS:
    #         reply_request = ReplyMessageRequest(
    #             replyToken=event.reply_token,
    #             messages=[TextMessage(text="❌ 本群組沒有權限使用 AI 服務")]
    #         )
    #         send_response(event, reply_request)
    #         return
    #     if user_id not in ALLOWED_USERS and "狗蛋" in user_message:
    #         reply_request = ReplyMessageRequest(
    #             replyToken=event.reply_token,
    #             messages=[TextMessage(text="❌ 你沒有權限使用 AI 服務")]
    #         )
    #         send_response(event, reply_request)
    #         return
    #     # 處理「狗蛋出去」指令（僅適用於群組）
    #     if "狗蛋" in user_message and "出去" in user_message and group_id:
    #         try:
    #             reply_request = ReplyMessageRequest(
    #             replyToken=event.reply_token,
    #             messages=[TextMessage(text="我也不想留, 掰")]
    #             )
    #             send_response(event, reply_request)
    #             messaging_api.leave_group(group_id)
    #             print(f"🐶 狗蛋已離開群組 {group_id}")
    #         except Exception as e:
    #             print(f"❌ 無法離開群組: {e}")
    #         return


    # (4) AI Group Command
    if event.source.type == "group":
        # 處理「狗蛋出去」指令（僅適用於群組）
        if "狗蛋" in user_message and "出去" in user_message and group_id:
            try:
                reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="我也不想留, 掰")]
                )
                send_response(event, reply_request)
                messaging_api.leave_group(group_id)
                print(f"🐶 狗蛋已離開群組 {group_id}")
                return
            except Exception as e:
                if time.time-t_ini > 5:
                    reply_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text="狗蛋還在籠子裡睡, 請再呼喊牠一次🐕")]
                    )
                    send_response(event, reply_request)
                return

    # (4-a) 「狗蛋生成」指令（例如圖片生成）
    if "狗蛋生成" in user_message:
        prompt = user_message.split("狗蛋生成", 1)[1].strip()
        if not prompt:
            prompt = "一個美麗的風景"
        print(f"📢 [DEBUG] 圖片生成 prompt: {prompt}")
        # 直接傳入 event.reply_token，而不是 user id
        try:
            handle_generate_image_command(event.reply_token, prompt, messaging_api)
            return
        except Exception as e:
                if time.time-t_ini > 30:
                    reply_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text="狗蛋還在籠子裡睡, 請再呼喊牠一次🐕")]
                    )
                    send_response(event, reply_request)
                return

    # (4-b) 「當前模型」指令
    if "模型" in user_message and "當前" in user_message:
        if group_id and group_id in user_ai_choice:
            model = user_ai_choice[group_id]
        else:
            model = user_ai_choice.get(user_id, "Deepseek-R1")
        if group_id and group_id in user_personality_choice:
            personality = user_personality_choice[group_id]
        else:
            personality = user_personality_choice.get(user_id, "正宗狗蛋")
        reply_text = f"🤖 \n現在使用的 AI 模型是：\n{model}\n現在使用的 AI 人格是：\n{personality}"
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        send_response(event, reply_request)
        return
    
    # (4-c) 「換模型」
    if "換" in user_message and "模型" in user_message:
        # 若此事件來自語音，則改用 push_message
        if getattr(event, "_is_audio", False):
            target = event.source.group_id if event.source.type == "group" else event.source.user_id
            send_ai_selection_menu(event.reply_token, target, use_push=True)
        else:
            send_ai_selection_menu(event.reply_token)
        return
    
    # (4-cc) 「狗蛋人格」
    if "人格" in user_message and "換" in user_message :
        # 若此事件來自語音，則改用 push_message
        if getattr(event, "_is_audio", False):
            target = event.source.group_id if event.source.type == "group" else event.source.user_id
            if user_id in allowed_users_BADEGG_str :
                send_ai_properties_private_menu(event.reply_token, target, use_push=True)
            else:
                send_ai_properties_menu(event.reply_token, target, use_push=True)
        else:
            if user_id in allowed_users_BADEGG_str :
                send_ai_properties_private_menu(event.reply_token)
            else:
                send_ai_properties_menu(event.reply_token)
        return

    # (4-e)「狗蛋搜尋」指令：搜尋 + AI 總結
    if user_message.startswith("狗蛋搜尋"):
        search_query = user_message.replace("狗蛋搜尋", "").strip()
        
        if not search_query:
            reply_text = "請輸入要搜尋的內容，例如：狗蛋搜尋 OpenAI"
        else:
            print(f"📢 [DEBUG] 進行 Google 搜尋: {search_query}")
            search_results = google_search(search_query)

            if not search_results:
                reply_text = "❌ 找不到相關資料。"
            else:
                reply_text = summarize_with_openai(search_results, search_query)

        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        send_response(event, reply_request)
        return
    
    # (4-f)狗蛋介紹 Image + AI 總結
    if user_message.startswith("狗蛋介紹"):
        # 解析人物名稱
        messages = []
        person_name = user_message.replace("狗蛋介紹", "").strip()
        if not person_name:
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="請提供要查詢的人物名稱，例如：狗蛋介紹 川普")]
            )
            send_response(event, reply_request)
            return
        # 取得 AI 回應 + 圖片
        response_text, image_url = search_person_info(person_name)
        if image_url:
            messages.append(create_flex_message(response_text, image_url))  # 附加圖片

        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=messages
        )
        send_response(event, reply_request)
        return

    # (4-g)狗蛋搜圖 Image search
    if user_message.startswith("狗蛋搜圖"):
        search_query = user_message.replace("狗蛋搜圖", "").strip()

        if not search_query:
            reply_text = "請提供要搜尋的內容，例如：狗蛋搜圖 日本女星"
            messages = [TextMessage(text=reply_text)]
        else:
            image_url = search_google_image(search_query)

            if image_url:
                messages = [create_flex_message(f"「{search_query}」的圖片 🔍", image_url)]
            else:
                messages = [TextMessage(text=f"找不到 {search_query} 的相關圖片 😢")]

        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=messages
        )
        send_response(event, reply_request)
        return
    
    # (4-h)狗蛋唱歌 Spotify link
    if user_message.startswith("狗蛋唱歌"):
        song_name = user_message.replace("狗蛋唱歌", "").strip()
        song_data = search_spotify_song(song_name)

        if not song_data:
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="❌ 沒找到這首歌，請試試別的！")]
            )
        else:
            mp3_url = song_data.get("preview_url")
            if mp3_url:
                hosted_m4a_url = download_and_host_audio(mp3_url)  # 轉換為 m4a

                if hosted_m4a_url:
                    reply_request = ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[
                            TextMessage(text=f"🎶 這是 {song_data['name']} 的預覽音頻 🎵"),
                            AudioMessageContent(original_content_url=hosted_m4a_url, duration=30000)
                        ]
                    )
                else:
                    reply_request = ReplyMessageRequest(
                        replyToken=event.reply_token,
                        messages=[TextMessage(text="❌ 轉換歌曲失敗，請稍後再試！")]
                    )
            else:
                reply_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text=f"🎵 {song_data['name']} 的歌曲連結：{song_data['song_url']} ）")]
                )

        send_response(event, reply_request)
        return

    if user_message.startswith("狗蛋翻譯"):
        user_message = user_message.replace("狗蛋翻譯", "").strip()
        gpt_reply = ask_translate(user_message, "deepseek-r1-distill-llama-70b")
    
        # 將回覆文字轉換成語音資料
        audio_data = text_to_speech(gpt_reply, rate=1)
        if not audio_data or len(audio_data) == 0:
            messaging_api.reply_message({
                "replyToken": event.reply_token,
                "messages": [TextMessage(text="语音转换失败，请稍后再试。")]
            })
            return
        
        # 將音檔存入 static/audio 並取得公開 URL
        audio_url, audio_pri_url = upload_audio(audio_data)
        if not audio_url:
            messaging_api.reply_message({
                "replyToken": event.reply_token,
                "messages": [TextMessage(text="音檔上傳失敗，请检查伺服器配置。")]
            })
            return
        audio_message = AudioMessage(originalContentUrl=audio_url, duration=30000)
        text_message = TextMessage(text=f"翻譯內容:\n{gpt_reply}")
        
        # 使用單一 reply_message 回覆語音訊息
        messaging_api.reply_message({
            "replyToken": event.reply_token,
            "messages": [audio_message, text_message]
        })
        return

    # (4-i)狗蛋氣象
    # 如果使用者輸入 "台北天氣"，則查詢台北天氣
    if "氣象" in user_message and "狗蛋" in user_message:
        city = user_message.replace("狗蛋氣象", "").strip()
        
        if city:
            weather_info = get_weather_weatherapi(city)
        else:
            weather_info = "❌ 請輸入有效的城市名稱, 包含行政區（例如：竹北市、東勢鄉）"

        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=f"{weather_info}")]
        )
        send_response(event, reply_request)
        return
    
    # (4-j) 狗蛋預報
    if "狗蛋" in user_message and "預報" in user_message:
        city = user_message.replace("狗蛋預報", "").strip()
        
        if city:
            # get_weather_forecast 改為回傳 (forecast_text, chart_filename)
            forecast_text, chart_filename = get_weather_forecast(city)
        else:
            forecast_text = "❌ 請輸入有效的城市名稱, 包含行政區（例如：竹北市、東勢鄉）"
            chart_filename = None
        # print(chart_filename)
        messages = []
        if chart_filename:
            IMAGE_URL_BASE = f"{BASE_URL}/static/{chart_filename}"
            messages.append(
                ImageMessage(
                    originalContentUrl=IMAGE_URL_BASE,
                    previewImageUrl=IMAGE_URL_BASE
                )
            )
        messages.append(TextMessage(text=f"{forecast_text}"))
        
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=messages
        )
        send_response(event, reply_request)
        return

    # # (4-j)「狗蛋開車」
    # if ("狗蛋開車") in user_message and ("最熱") not in user_message and ("最新") not in user_message:
    #     search_query = user_message.replace("狗蛋開車", "").strip()
        
    #     if not search_query:
    #         response_text = "請提供人名，例如：狗蛋開車 狗蛋"
    #         reply_request = ReplyMessageRequest(
    #             reply_token=event.reply_token,
    #             messages=[TextMessage(text=response_text)]
    #         )
    #     else:
    #         videos = get_video_data(search_query)  # ✅ 爬取影片
    #         # print(f"✅ [DEBUG] 爬取結果: {videos}")  # Debugging
            
    #         if not videos:
    #             print("❌ [DEBUG] 爬取結果為空，回傳純文字訊息")
    #             response_text = "找不到相關影片。"
    #             reply_request = ReplyMessageRequest(
    #                 reply_token=event.reply_token,
    #                 messages=[TextMessage(text=response_text)]
    #             )
    #         else:
    #             flex_message = create_flex_jable_message(user_id, group_id, videos)   # ✅ 生成 FlexMessage
                
    #             if flex_message is None:  # **確保 flex_message 不為 None**
    #                 print("❌ [DEBUG] FlexMessage 生成失敗，回傳純文字")
    #                 response_text = "找不到相關影片。"
    #                 reply_request = ReplyMessageRequest(
    #                     reply_token=event.reply_token,
    #                     messages=[TextMessage(text=response_text)]
    #                 )
    #             else:
    #                 # print(f"✅ [DEBUG] 生成的 FlexMessage: {flex_message}")
    #                 reply_request = ReplyMessageRequest(
    #                     reply_token=event.reply_token,
    #                     messages=[flex_message]
    #                 )
    #     send_response(event, reply_request)  
    #     return  

    # # (4-k)「狗蛋開車最熱」
    # if ("狗蛋開車") in user_message and ("最熱") in user_message:
    #     videos = get_video_data_hotest()  # ✅ 爬取影片
    #     print(f"✅ [DEBUG] 爬取結果: {videos}")  # Debugging
            
    #     if not videos:
    #         print("❌ [DEBUG] 爬取結果為空，回傳純文字訊息")
    #         response_text = "找不到相關影片。"
    #         reply_request = ReplyMessageRequest(
    #             reply_token=event.reply_token,
    #             messages=[TextMessage(text=response_text)]
    #         )
    #     else:
    #         flex_message = create_flex_jable_message(user_id, group_id, videos)   # ✅ 生成 FlexMessage
                
    #         if flex_message is None:  # **確保 flex_message 不為 None**
    #             print("❌ [DEBUG] FlexMessage 生成失敗，回傳純文字")
    #             response_text = "找不到相關影片。"
    #             reply_request = ReplyMessageRequest(
    #                 reply_token=event.reply_token,
    #                 messages=[TextMessage(text=response_text)]
    #             )
    #         else:
    #             # print(f"✅ [DEBUG] 生成的 FlexMessage: {flex_message}")
    #             reply_request = ReplyMessageRequest(
    #                 reply_token=event.reply_token,
    #                 messages=[flex_message]
    #             )
    #     send_response(event, reply_request)  
    #     return  
    
    # # (4-m)「狗蛋開車最新」
    # if ("狗蛋開車") in user_message and ("最新") in user_message:
    #     videos = get_video_data_newest()  # ✅ 爬取影片
    #     print(f"✅ [DEBUG] 爬取結果: {videos}")  # Debugging
            
    #     if not videos:
    #         print("❌ [DEBUG] 爬取結果為空，回傳純文字訊息")
    #         response_text = "找不到相關影片。"
    #         reply_request = ReplyMessageRequest(
    #             reply_token=event.reply_token,
    #             messages=[TextMessage(text=response_text)]
    #         )
    #     else:
    #         flex_message = create_flex_jable_message(user_id, group_id, videos)   # ✅ 生成 FlexMessage
                
    #         if flex_message is None:  # **確保 flex_message 不為 None**
    #             print("❌ [DEBUG] FlexMessage 生成失敗，回傳純文字")
    #             response_text = "找不到相關影片。"
    #             reply_request = ReplyMessageRequest(
    #                 reply_token=event.reply_token,
    #                 messages=[TextMessage(text=response_text)]
    #             )
    #         else:
    #             # print(f"✅ [DEBUG] 生成的 FlexMessage: {flex_message}")
    #             reply_request = ReplyMessageRequest(
    #                 reply_token=event.reply_token,
    #                 messages=[flex_message]
    #             )
    #     send_response(event, reply_request)  
    #     return 

    # 「狗蛋開車」時
    if user_message == "狗蛋開車":
        videos = get_latest_videos_from_database()

        if not videos:
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="目前沒有新影片，請稍後再試！")]
            )
            send_response(event, reply_request)
        else:
            flex_message = create_flex_jable_message(user_id, videos)
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[flex_message]
            )
            send_response(event, reply_request)
            return
    
    if "狗蛋開車"in user_message and "時刻表" in user_message:
        videos_des = get_AVVIDEO_description()
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=videos_des)]
        )
        send_response(event, reply_request)
        return
    
    if "狗蛋開車" in user_message:
        parts = user_message.split(" ", 1)
        print(parts)

        keywords = parts[1].strip() if len(parts) > 1 else ""
        if not keywords:  # 若無關鍵字，跳過處理
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="請輸入關鍵字，例如 '狗蛋開車 三上悠亞'")]
            )
            send_response(event, reply_request)
            return

        # 查找完整名稱（忽略大小寫，支援部分匹配）
        full_actress = find_full_name(keywords, ACTRESS_AV_NAMES)
        full_series = find_full_name(keywords, ACTRESS_AV_SERIES)

        if full_actress:
            videos_list = get_videos_from_database(full_actress, max_title_length)
        elif full_series:
            videos_list = get_videos_from_database_series(full_series, max_title_length)
        else:
            videos_list = []

        if not videos_list:
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="沒有搜尋到內容，請輸入\n 狗蛋開車 時刻表\n確認可查詢關鍵字")]
            )
            send_response(event, reply_request)
        else:
            flex_message = create_flex_jable_message(user_id, videos_list)
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[flex_message]
            )
            send_response(event, reply_request)
            return

    # (4-n)「狗蛋推片」
    if user_message == "狗蛋推片":
        # 🚀 轉發請求到本機爬蟲伺服器（ngrok）
        try:
            response = requests.post(
                f"{NGROK_URL}/crawlpromot",
                json={},  # 傳遞關鍵字
                timeout=10
            )
            result = response.json()
            print(response, result)

            if "videos" in result and result["videos"]:  # 確保 videos 存在且不為空
                videos = result["videos"]
            else:
                videos = []  # 確保 videos 不會未定義

        except Exception as e:
            print(f"❌ [ERROR] 無法請求本機爬蟲 API: {e}")
            videos = []  # 確保 videos 不會未定義

        if not videos:
            print("❌ [DEBUG] 爬取結果為空，回傳純文字訊息")
            response_text = "🚓請確認開車時刻表🚓"
            reply_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_text)]
            )
        else:
            flex_message = create_flex_jable_message(user_id, group_id, videos) 
                
            if flex_message is None:  # **確保 flex_message 不為 None**
                print("❌ [DEBUG] FlexMessage 生成失敗，回傳純文字")
                response_text = "找不到相關影片。"
                reply_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response_text)]
                )
            else:
                # print(f"✅ [DEBUG] 生成的 FlexMessage: {flex_message}")
                reply_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )
        send_response(event, reply_request)  
        return  

    # (4-q)「狗蛋推片」
    if user_message.startswith("狗蛋推片"):
        search_query = user_message.replace("狗蛋推片", "").strip()
        user_id = event.source.user_id  # ✅ 取得 user_id
        
        print(f"📢 [DEBUG] 指令『狗蛋推片』被觸發，查詢關鍵字: {search_query}")
        
        if not search_query:
            response_text = "請提供人名，例如：狗蛋推片 狗蛋"
            reply_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_text)]
            )
        
        try:
            print(f"📢 [DEBUG] 發送請求到: {NGROK_URL}/crawl")
            response = requests.post(
                f"{NGROK_URL}/crawl",
                json={"search_query": search_query},
                timeout=10
            )

            print(f"📢 [DEBUG] API 回應狀態碼: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"📢 [DEBUG] API 回應內容: {result}")
                videos = result.get("videos", [])
            else:
                print(f"❌ [ERROR] API 回應錯誤: {response.status_code}")
                videos = []

        except requests.exceptions.RequestException as e:
            print(f"❌ [ERROR] 無法請求本機爬蟲 API: {e}")
            videos = []

        if not videos:
            print("❌ [DEBUG] 爬取結果為空，回傳純文字訊息")
            response_text = "🚓請確認開車時刻表🚓"
            reply_request = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_text)]
            )
        else:
            flex_message = create_flex_jable_message(user_id, group_id, videos)  # ✅ 修正，傳入 user_id
            if flex_message is None:
                print("❌ [DEBUG] FlexMessage 生成失敗，回傳純文字")
                response_text = "找不到相關影片。"
                reply_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response_text)]
                )
            else:
                reply_request = ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )

        send_response(event, reply_request)
        return

    # (4-x) 狗蛋找店
    if user_message.startswith("狗蛋找店"):
        user_state[user_id] = {}
        parts = user_message.split(" ", 1)

        if len(parts) > 1:
            # 提取用戶輸入的店名
            location_name = parts[1].strip()

            # 嘗試取得座標
            lat, lng = geocode_location(location_name)

            if lat and lng:
                # 生成 Google Maps 連結
                maps_url = get_google_maps_link(lat, lng, location_name)

                reply_text = (
                    f"📍 {location_name} 的位置：\n"
                    f"🗺️ [Google 地圖連結]({maps_url})"
                )

                reply_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
                send_response(event, reply_request)
                return
            else:
                reply_text = f"😕 找不到 **{location_name}**，請試著提供更完整的店名或地址。"
                reply_request = ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
                send_response(event, reply_request)
                return

        # 若沒有輸入店名，詢問使用者店家類型
        user_state[user_id]["step"] = "awaiting_store_type"
        reply_text = "(´ᴥ`) 想找什麼店？讓我來嗅嗅看"
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
        send_response(event, reply_request)
        return

    # (4-z) 狗蛋劇場
    if user_message == "狗蛋劇場":
        # if getattr(event, "_is_audio", False):
        #     target = event.source.group_id if event.source.type == "group" else event.source.user_id
        #     send_video_selection_menu(event.reply_token, target, use_push=True)
        # else:
        #     send_video_selection_menu(event.reply_token)
        # return
        videos = get_remote_videos_from_database("test", max_title_length)
        print(videos)

        if not videos:
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text="目前沒有新影片，請稍後再試！")]
            )
            send_response(event, reply_request)
        else:
            flex_message = create_flex_user_message(user_id, videos)
            reply_request = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[flex_message]
            )
            send_response(event, reply_request)
            return

    # 如果目前狀態等待輸入店面類型
    if user_state.get(user_id, {}).get("step") == "awaiting_store_type":
        store_type = user_message.strip()
        user_state[user_id]["store_type"] = store_type
        user_state[user_id]["step"] = "awaiting_location"
        reply_text = f"請分享地點或目前的位置, 讓我幫你找 {store_type}。"
        quick_reply = QuickReply(
            items=[QuickReplyItem(action=LocationAction(label="點擊分享位置"))]
        )
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply_text, quick_reply=quick_reply)]
        )
        send_response(event, reply_request)
        return

    # (5) 若在群組中且訊息中不包含「狗蛋」，則不觸發 AI 回應
    if event.source.type == "group" and "狗蛋" not in user_message:
        return

    # (6) 預設：呼叫 AI 回應函式
    if event.source.type == "group":
        if group_id and group_id in user_ai_choice:
            ai_model = user_ai_choice[group_id]
        else:
            ai_model = "GPT_4o_Mini"
    else:
        ai_model = user_ai_choice.get(user_id, "GPT_4o_Minib")
    if event.source.type == "group":
        if group_id and group_id in user_personality_choice:
            ai_personality = user_personality_choice[group_id]
        else:
            ai_personality = "normal_egg"
    else:
        ai_personality = user_personality_choice.get(user_id, "normal_egg")
    
    # history = get_recent_chat_history(user_id)
    # prompt = f"following contents is history : {history}, according to history, this is my input:{user_message}"
    # gpt_reply = talk_to_ai_history(prompt, ai_model)
    # prompt_reponse = f"conversation as following between {user_id} and ai assistant, my input to ai is {user_message}, and ai response is {gpt_reply}"
    # save_chat_history(user_id, "assistant", prompt_reponse)
    gpt_reply = ask_groq(user_message, ai_model, ai_personality)
    
    try:
        reply_request = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=gpt_reply)]
        )
        send_response(event, reply_request)
    except Exception as e:
        print(f"❌ LINE Reply Error: {e}")

# AudioMessage Handler
@handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio_message(event):
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else None
    reply_token = event.reply_token
    audio_id = event.message.id

    print(f"📢 [DEBUG] 收到語音訊息, ID: {audio_id}")
    audio_url = f"https://api-data.line.me/v2/bot/message/{audio_id}/content"
    headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}

    try:
        # 下載語音檔案
        response = requests.get(audio_url, headers=headers, stream=True)
        if response.status_code == 200:
            audio_path = f"/tmp/{audio_id}.m4a"
            with open(audio_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"📢 [DEBUG] 語音檔案已儲存: {audio_path}")

            # 呼叫轉錄及後續回覆（同步完成）
            transcribed_text, ai_response = transcribe_and_respond_with_gpt(audio_path)
            if not transcribed_text:
                # 如果轉錄失敗，立即回覆失敗訊息
                reply_request = ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[TextMessage(text="❌ 語音辨識失敗，請再試一次！")]
                )
                messaging_api.reply_message(reply_request)
                return

            print(f"📢 [DEBUG] Whisper 轉錄結果: {transcribed_text}")

            # 準備回覆訊息列表（全部用 reply_message 一次性回覆）
            messages = []

            # 回覆轉錄內容
            messages.append(TextMessage(text=f"🎙️ 轉錄內容：{transcribed_text}"))

            # 檢查是否有特殊指令
            if "狗蛋生成" in transcribed_text:
                prompt = transcribed_text.split("狗蛋生成", 1)[1].strip()
                if not prompt:
                    prompt = "一隻可愛的小狗"
                print(f"📢 [DEBUG] 圖片生成 prompt: {prompt}")
                # 傳入 reply_token 而非 target_id
                handle_generate_image_command(event.reply_token, prompt, messaging_api)
                return


            if "狗蛋" in transcribed_text and "情勒" in transcribed_text:
                # 如果包含「狗蛋情勒」指令，回覆隨機訊息（模擬回覆）
                random_msg = random.choice([
                    "🥱你看我有想告訴你嗎？",
                    "😏我知道你在想什麼！",
                    "🤔你確定嗎？",
                    "😎好啦，不理你了！"
                ])
                messages.append(TextMessage(text=random_msg))
            elif event.source.type == "group" and "狗蛋" not in transcribed_text:
                print("群組語音訊息未明確呼喚 '狗蛋'，不進行ai回覆。")
                reply_request = ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=messages
                )
                messaging_api.reply_message(reply_request)
                return
            else:
                # 預設情況下回覆 AI 回應
                messages.append(TextMessage(text=ai_response))

            # 使用 reply_message 一次性回覆所有訊息
            reply_request = ReplyMessageRequest(
                replyToken=reply_token,
                messages=messages
            )
            messaging_api.reply_message(reply_request)
        else:
            print(f"❌ [ERROR] 無法下載語音訊息, API 狀態碼: {response.status_code}")
            reply_request = ReplyMessageRequest(
                replyToken=reply_token,
                messages=[TextMessage(text="❌ 下載語音檔案失敗")]
            )
            messaging_api.reply_message(reply_request)
    except Exception as e:
        print(f"❌ [ERROR] 處理語音時發生錯誤: {e}")
        reply_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[TextMessage(text="❌ 語音處理發生錯誤，請稍後再試！")]
        )
        messaging_api.reply_message(reply_request)

# Transcribe Function
def transcribe_and_respond_with_gpt(audio_path):
    """使用 GPT-4o Mini 進行語音轉文字並生成回應"""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    with open(audio_path, "rb") as audio_file:
        files = {
            "file": (audio_path, audio_file, "audio/m4a"),
            "model": (None, "whisper-1"),
            "language": (None, "zh")
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files
            )
            if response.status_code == 200:
                result = response.json()
                transcribed_text = result.get("text", "").strip()
                print(f"📢 [DEBUG] Whisper 轉錄結果: {transcribed_text}")
                if not transcribed_text:
                    return None, "❌ 語音內容過短，無法辨識"

                # 直接使用 openai.ChatCompletion.create() 來呼叫 API
                completion = openai.ChatCompletion.create(
                    model="gpt-4o",  # 此處請確認您有權限使用該模型，若有需要可改為其他模型（例如 "gpt-3.5-turbo"）
                    messages=[
                        {"role": "system", "content": "你是一個名叫狗蛋的智能助手，請使用繁體中文回答。"},
                        {"role": "user", "content": transcribed_text}
                    ]
                )
                ai_response = completion.choices[0].message.content.strip()
                return transcribed_text, ai_response
            else:
                print(f"❌ [ERROR] Whisper API 回應錯誤: {response.text}")
                return None, "❌ 語音辨識失敗，請稍後再試"
        except Exception as e:
            print(f"❌ [ERROR] 語音轉文字 API 失敗: {e}")
            return None, "❌ 伺服器錯誤，請稍後再試"

# 處理位置訊息
@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    user_id = event.source.user_id
    # 取出使用者先前設定的店面類型
    store_type = user_state.get(user_id, {}).get("store_type", "")
    # 呼叫搜尋函數，回傳搜尋結果
    location_info = search_nearby_location(latitude, longitude, store_type)
    reply_request = ReplyMessageRequest(
        replyToken=event.reply_token,
        messages=[TextMessage(text=location_info)]
    )
    send_response(event, reply_request)
    # 搜尋完畢後，清除該使用者的狀態
    user_state.pop(user_id, None)

# Post Handler
@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else None
    data = event.postback.data

    # ✅ **處理 AI 模型選擇**
    model_map = {
        "model_gpt4o": "GPT-4o",
        "model_gpt4o_mini": "GPT_4o_Mini",
        "model_deepseek": "GPT_4o_Minib",
        "model_llama3": "GPT_4o_Mini",
    }

    if data in model_map:
        if group_id:
            user_ai_choice[group_id] = model_map[data]
        else:
            user_ai_choice[user_id] = model_map[data]
        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=f"已選擇語言模型: {model_map[data]}！\n\n🔄 輸入「換模型」可重新選擇")]
        )
        messaging_api.reply_message(reply_req)
        return
    
    personality_map = {
        "personality_normal": "normal_egg",
        "personality_sad": "sad_egg",
        "personality_angry": "angry_egg",
        "personality_sowhat": "sowhat_egg",
        "personality_bad": "bad_egg"
    }

    if data in personality_map:
        if group_id:
            user_personality_choice[group_id] = personality_map[data]
        else:
            user_personality_choice[user_id] = personality_map[data]

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[
                TextMessage(text=f"已選擇個性: {personality_map[data]}！\n\n🔄 輸入「換人格」可重新選擇")
            ]
        )
        messaging_api.reply_message(reply_req)
        return

    # ✅ **處理影片批次切換**
    # 存儲使用者模式，避免換一批時按鈕變回預設
    if data.startswith("change_actress|"):
        _, user_id, actress_name = data.split("|")

        # **拉取對應演員的影片**
        videos = get_videos_from_database(actress_name, max_title_length)

        if not videos:
            reply_req = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=f"抱歉，演員「{actress_name}」目前沒有影片！")]
            )
            messaging_api.reply_message(reply_req)
            return

        # ✅ **如果有影片，則更新批次**
        video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
        batch_index[user_id] = 0

        # ✅ **刷新 user_mode 為當前演員**
        user_mode[user_id] = "actress"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_flex_message(user_id, mode="actress")]
        )
        messaging_api.reply_message(reply_req)
        return

    elif data.startswith("change_series|"):
        _, user_id, series_name = data.split("|")

        # **拉取對應系列的影片**
        videos = get_videos_from_database_series(series_name, max_title_length)

        if not videos:
            reply_req = ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=f"抱歉，系列「{series_name}」目前沒有影片！")]
            )
            messaging_api.reply_message(reply_req)
            return

        # ✅ **如果有影片，則更新批次**
        video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
        batch_index[user_id] = 0

        # ✅ **刷新 user_mode 為當前系列**
        user_mode[user_id] = "series"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_flex_message(user_id, mode="series")]
        )
        messaging_api.reply_message(reply_req)
        return

    if data.startswith("change_batch|"):
        user_id = data.split("|")[1]

        if user_id in video_batches and user_id in batch_index:
            total_batches = len(video_batches[user_id])
            batch_index[user_id] = (batch_index[user_id] + 1) % total_batches  # 循環播放影片

        # ✅ **維持使用者的 mode 狀態**
        current_mode = user_mode.get(user_id, "latest")

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_flex_message(user_id, mode=current_mode)]  # ✅ 不重置 mode
        )
        messaging_api.reply_message(reply_req)
        return

    elif data.startswith("change_popular|"):
        user_id = data.split("|")[1]

        # **拉取熱門影片**
        videos = get_hotest_videos_from_database()
        if videos:
            video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
            batch_index[user_id] = 0

        # ✅ **設定 mode="popular"，直到使用者切換回最新**
        user_mode[user_id] = "popular"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_flex_message(user_id, mode="popular")]
        )
        messaging_api.reply_message(reply_req)
        return

    elif data.startswith("change_latest|"):
        user_id = data.split("|")[1]

        # **拉取最新影片**
        videos = get_latest_videos_from_database()
        if videos:
            video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
            batch_index[user_id] = 0

        # ✅ **設定 mode="latest"，直到使用者切換回熱門**
        user_mode[user_id] = "latest"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_flex_message(user_id, mode="latest")]
        )
        messaging_api.reply_message(reply_req)
        return

    if data.startswith("change_latest_momo_videos|"):
        user_id = data.split("|")[1]
        videos = get_remote_videos_from_momovod_database("dummy", max_title_length)
        print(videos)
        if videos:
            video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
            batch_index[user_id] = 0

        # ✅ **設定 mode="latest"，直到使用者切換回熱門**
        user_mode[user_id] = "change_latest_momo_videos"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_user_videos_flex_message(user_id, mode="change_latest_momo_videos")]
        )
        messaging_api.reply_message(reply_req)
        return
    
    elif data.startswith("change_latest_netflix_movies|"):
        user_id = data.split("|")[1]
        videos = get_remote_videos_from_database_drama_series("dummy", max_title_length)
        if videos:
            video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
            batch_index[user_id] = 0

        # ✅ **設定 mode="latest"，直到使用者切換回熱門**
        user_mode[user_id] = "change_latest_momo_videos"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_user_videos_flex_message(user_id, mode="change_latest_momo_videos")]
        )
        messaging_api.reply_message(reply_req)
        return
    
    elif data.startswith("change_movie_series|"):
        user_id = data.split("|")[1]
        series_name = data.split("|")[2]

        # **拉取最新影片**
        videos = get_remote_videos_from_database_movie_series(series_name, max_title_length)
        if videos:
            video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
            batch_index[user_id] = 0
        # ✅ **設定 mode="latest"，直到使用者切換回熱門**
        user_mode[user_id] = "change_movie_series"

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[create_flex_user_message(user_id, videos)]
        )
        messaging_api.reply_message(reply_req)
        return
    
    elif data.startswith("change_batch_videos|"):
        user_id = data.split("|")[1]

        if user_id in video_batches and user_id in batch_index:
            total_batches = len(video_batches[user_id])
            batch_index[user_id] = (batch_index[user_id] + 1) % total_batches  # 循環播放影片

        # ✅ **維持使用者的 mode 狀態**
        current_mode = user_mode.get(user_id, "latest")

        reply_req = ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[generate_user_videos_flex_message(user_id, mode=current_mode)]  # ✅ 不重置 mode
        )
        messaging_api.reply_message(reply_req)
        return


    # ✅ **處理影片類型選擇**
    video_categories_map = {
        "videos_movies": "movies",
        "videos_dramas": "dramas",
        "videos_cartones": "cartones",
        "videos_expert": "expert",
    }

    if data in video_categories_map:
        selected_category = video_categories_map[data]

        # 儲存用戶選擇
        if group_id:
            user_videos_choice[group_id] = selected_category
        else:
            user_videos_choice[user_id] = selected_category

        # 產生對應類型的 FlexMessage
        flex_message = generate_videos_flex_message(user_id, selected_category)

        # 送出訊息
        reply_req = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[flex_message]
        )
        messaging_api.reply_message(reply_req)

    # ✅ **處理未知的 postback**
    reply_req = ReplyMessageRequest(
        replyToken=event.reply_token,
        messages=[TextMessage(text="未知選擇，請重試。")]
    )
    messaging_api.reply_message(reply_req)

def send_video_selection_menu(reply_token, target=None, use_push=False):
    """發送 AI 選擇選單"""
    flex_contents_json = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/movieegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Movies", "data": "videos_movies"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/dramaegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Dramas", "data": "videos_dramas"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/cartoneegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Animes", "data": "videos_cartones"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/expertegg.png",  
                    "size": "md",
                    "aspectRatio": "1:1",
                    "aspectMode": "fit"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Recommend", "data": "videos_expert"}}
                    ]
                }
            }
        ]
    }

    try:
        # 將 flex JSON 轉為字串，再解析成 FlexContainer
        flex_json_str = json.dumps(flex_contents_json)
        flex_contents = FlexContainer.from_json(flex_json_str)
        flex_message = FlexMessage(
            alt_text="請選擇影片類型",
            contents=flex_contents
        )
        reply_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[
                TextMessage(text="你好，我是狗蛋🐶 ！ \n今天想看點什麼！"),
                flex_message
            ]
        )
        if use_push and target:
            push_request = PushMessageRequest(
                to=target,
                messages=reply_request.messages
            )
            messaging_api.push_message(push_request)
        else:
            messaging_api.reply_message(reply_request)
    except Exception as e:
        print(f"❌ FlexMessage Error: {e}")

def send_ai_selection_menu(reply_token, target=None, use_push=False):
    """發送 AI 選擇選單"""
    flex_contents_json = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/openai.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "輕量強大-支援語音輸入", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "GPT-4o Mini", "data": "model_gpt4o_mini"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/deepseek.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "語意檢索強", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Deepseek-R1", "data": "model_deepseek"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/meta.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "長文本適配", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "LLama3-8b", "data": "model_llama3"}}
                    ]
                }
            },
            # {
            #     "type": "bubble",
            #     "hero": {
            #         "type": "image",
            #         "url": f"{BASE_URL}/static/giticon.png",  
            #         "size": "md",
            #         "aspectRatio": "1:1",
            #         "aspectMode": "fit"
            #     },
            #     "body": {
            #         "type": "box",
            #         "layout": "vertical",
            #         "justifyContent": "center",
            #         "contents": [
            #             {"type": "text", "text": "高登基地", "weight": "bold", "size": "xl", "align": "center"},
            #             {"type": "button", "style": "primary", "action": {"type": "uri", "label": "開啟基地", "uri": "https://gordonsay.github.io/gordonwu/personalpage/index_personal.html"}}
            #         ]
            #     }
            # }
        ]
    }

    try:
        # 將 flex JSON 轉為字串，再解析成 FlexContainer
        flex_json_str = json.dumps(flex_contents_json)
        flex_contents = FlexContainer.from_json(flex_json_str)
        flex_message = FlexMessage(
            alt_text="請選擇 AI 模型",
            contents=flex_contents
        )
        reply_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[
                TextMessage(text="你好，我是狗蛋🐶 ！\n請選擇 AI 模型後發問。"),
                flex_message
            ]
        )
        if use_push and target:
            push_request = PushMessageRequest(
                to=target,
                messages=reply_request.messages
            )
            messaging_api.push_message(push_request)
        else:
            messaging_api.reply_message(reply_request)
    except Exception as e:
        print(f"❌ FlexMessage Error: {e}")

def send_ai_properties_menu(reply_token, target=None, use_push=False):
    """發送 AI 選擇選單"""
    flex_contents_json = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/dogegg.jpg",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "正宗狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_normal"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/sowhategg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "SoWhat狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_sowhat"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/angryegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "Angry狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_angry"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/sadegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "Sadage狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_sad"}}
                    ]
                }
            },
        ]
    }

    try:
        # 將 flex JSON 轉為字串，再解析成 FlexContainer
        flex_json_str = json.dumps(flex_contents_json)
        flex_contents = FlexContainer.from_json(flex_json_str)
        flex_message = FlexMessage(
            alt_text="請選擇 AI 模型",
            contents=flex_contents
        )
        reply_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[
                TextMessage(text="你好，我是狗蛋🐶 ！\n請選擇 AI 模型後發問。"),
                flex_message
            ]
        )
        if use_push and target:
            push_request = PushMessageRequest(
                to=target,
                messages=reply_request.messages
            )
            messaging_api.push_message(push_request)
        else:
            messaging_api.reply_message(reply_request)
    except Exception as e:
        print(f"❌ FlexMessage Error: {e}")

def send_ai_properties_private_menu(reply_token, target=None, use_push=False):
    """發送 AI 選擇選單"""
    flex_contents_json = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/dogegg.jpg",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "正宗狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_normal"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/sowhategg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "SoWhat狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_sowhat"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/angryegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "Angry狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_angry"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/sadegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "Sadage狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_sad"}}
                    ]
                }
            },
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/badegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",
                    "contents": [
                        {"type": "text", "text": "Heaven狗蛋", "weight": "bold", "size": "xl", "align": "center"},
                        {"type": "button", "style": "primary", "action": {"type": "postback", "label": "Choose", "data": "personality_bad"}}
                    ]
                }
            }
        ]
    }

    try:
        # 將 flex JSON 轉為字串，再解析成 FlexContainer
        flex_json_str = json.dumps(flex_contents_json)
        flex_contents = FlexContainer.from_json(flex_json_str)
        flex_message = FlexMessage(
            alt_text="請選擇 AI 模型",
            contents=flex_contents
        )
        reply_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[
                TextMessage(text="你好，我是狗蛋🐶 ！\n請選擇 AI 模型後發問。"),
                flex_message
            ]
        )
        if use_push and target:
            push_request = PushMessageRequest(
                to=target,
                messages=reply_request.messages
            )
            messaging_api.push_message(push_request)
        else:
            messaging_api.reply_message(reply_request)
    except Exception as e:
        print(f"❌ FlexMessage Error: {e}")

def ask_groq(user_message, model, ai_personality, retries=3, backoff_factor=1.0):
    """
    根據選擇的模型執行不同的 API：
      - 如果 model 為 "gpt-4o" 或 "gpt_4o_mini"，則呼叫 OpenAI API（原有邏輯）
      - 如果 model 為 "gpt-translation"，則使用翻譯模式，轉換為有效模型（例如 "gpt-3.5-turbo"）並使用翻譯 prompt
      - 否則使用 Groq API，並加入重試機制避免連線錯誤。
    """
    print(f"[ask_groq] 模型參數: {model}")
    print(f"[ask_groq] 人格參數: {ai_personality}")

    if ai_personality == "normal_egg":
        Prompt_default = "你是一個名叫狗蛋的助手，只能使用繁體中文精簡跟朋友的語氣回答"
    elif ai_personality == "sowhat_egg":
        Prompt_default = "你是一個名叫狗蛋的助手，只能使用繁體中文, 所有回答都非常厭世悲觀且精簡; 例如：都可以啦反正也不太重要"
    elif ai_personality == "angry_egg":
        Prompt_default = "你是一個名叫狗蛋的助手，只能使用繁體中文, 所有回答都非常生氣激動且精簡; 例如：你每次都這樣說， 還不是發生了, 現在你看阿"
    elif ai_personality == "sad_egg":
        Prompt_default = "你是一個名叫狗蛋的助手，只能使用繁體中文, 所有回答都非常悲傷惆悵且精簡; 例如：這樣會不會情況很糟糕阿, 都是我的錯"
    elif ai_personality == "bad_egg":
        Prompt_default = "你是一個名叫狗蛋的助手，只能使用繁體中文, 所有回答都非常情色曖昧且直接赤裸; 例如：這樣太舒服了吧, 我怕上天堂, 你超色的啦"

    for i in range(retries):
        try:
            if model.lower() in ["gpt-4o", "gpt_4o_mini"]:
                # OpenAI GPT-4o Mini
                openai_client = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": f"{Prompt_default}, 約莫50字內，限制不超過80字，除非當請求為翻譯時, 全部內容都需要完成翻譯不殘留原語言。"},
                        {"role": "user", "content": user_message}
                    ]
                )
                print(f"📢 [DEBUG] OpenAI API 回應: {openai_client}")
                return openai_client.choices[0].message.content.strip()

            elif model.lower() == "gpt-translation":
                # OpenAI 翻譯模式
                effective_model = "gpt-3.5-turbo"
                print(f"📢 [DEBUG] 呼叫 OpenAI API (翻譯模式)，使用模型: {effective_model}")
                response = openai.ChatCompletion.create(
                    model=effective_model,
                    messages=[
                        {"role": "system", "content": "你是一位專業翻譯專家，請根據使用者的需求精準且自然地翻譯以下內容。當請求為翻譯時, 全部內容一定都要完成翻譯不殘留原語言"},
                        {"role": "user", "content": user_message}
                    ]
                )
                return response.choices[0].message.content.strip()

            else:
                # Groq API，加入重試機制
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": f"{Prompt_default}，約莫50字內，限制不超過80字，除非當請求為翻譯時, 全部內容都需要完成翻譯不殘留原語言。"},
                        {"role": "user", "content": user_message},
                    ],
                    model=model.lower(),
                )
                if not chat_completion.choices:
                    return "❌ 狗蛋無法回應，請稍後再試。"

                content = chat_completion.choices[0].message.content.strip()
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                return content

        except requests.exceptions.RequestException as e:
            print(f"❌ API 連線失敗 (第 {i+1} 次)：{e}")
            time.sleep(backoff_factor * (2 ** i))  # 指數退避 (1s, 2s, 4s)

        except Exception as e:
            print(f"❌ AI API 呼叫錯誤: {e}")
            return "❌ 狗蛋伺服器錯誤，請稍後再試。"

    return "❌ 無法連線至 AI 服務，請稍後再試。"

def ask_translate(user_message, model, retries=3, backoff_factor=1.0):
    print(f"[ask_translate] 模型參數: {model}")

    for i in range(retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "你是一位專業翻譯專家，請根據使用者的需求精準且自然地翻譯以下內容。全部內容一定都要完成翻譯不殘留原語言"},
                    {"role": "user", "content": user_message},
                ],
                model=model.lower(),
            )
            if not chat_completion.choices:
                return "❌ 狗蛋無法回應，請稍後再試。"

            content = chat_completion.choices[0].message.content.strip()
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return content

        except requests.exceptions.RequestException as e:
            print(f"❌ API 連線失敗 (第 {i+1} 次)：{e}")
            time.sleep(backoff_factor * (2 ** i))  # 指數退避 (1s, 2s, 4s)

        except Exception as e:
            print(f"❌ AI API 呼叫錯誤: {e}")
            return "❌ 狗蛋伺服器錯誤，請稍後再試。"

    return "❌ 無法連線至 AI 服務，請稍後再試。"

def talk_to_ai_history(user_message, model, retries=3, backoff_factor=1.0):
    """
    根據選擇的模型執行不同的 API：
      - 如果 model 為 "gpt-4o" 或 "gpt_4o_mini"，則呼叫 OpenAI API（原有邏輯）
      - 如果 model 為 "gpt-translation"，則使用翻譯模式，轉換為有效模型（例如 "gpt-3.5-turbo"）並使用翻譯 prompt
      - 否則使用 Groq API，並加入重試機制避免連線錯誤。
    """
    print(f"[ask_groq] 模型參數: {model}")

    for i in range(retries):
        try:
            if model.lower() in ["gpt-4o", "gpt_4o_mini"]:
                # OpenAI GPT-4o Mini
                openai_client = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": "你是一個名叫狗蛋的助手，盡量只使用繁體中文精簡跟朋友的語氣回答, 約莫50字內，限制不超過80字，除非當請求為翻譯時, 全部內容都需要完成翻譯不殘留原語言。"},
                        {"role": "user", "content": user_message}
                    ]
                )
                print(f"📢 [DEBUG] OpenAI API 回應: {openai_client}")
                return openai_client.choices[0].message.content.strip()

            elif model.lower() == "gpt-translation":
                # OpenAI 翻譯模式
                effective_model = "gpt-3.5-turbo"
                print(f"📢 [DEBUG] 呼叫 OpenAI API (翻譯模式)，使用模型: {effective_model}")
                response = openai.ChatCompletion.create(
                    model=effective_model,
                    messages=[
                        {"role": "system", "content": "你是一位專業翻譯專家，請根據使用者的需求精準且自然地翻譯以下內容。當請求為翻譯時, 全部內容一定都要完成翻譯不殘留原語言"},
                        {"role": "user", "content": user_message}
                    ]
                )
                return response.choices[0].message.content.strip()

            else:
                # Groq API，加入重試機制
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "你是一個名叫狗蛋的助手，跟使用者是朋友關係, 盡量只使用繁體中文方式進行回答, 約莫50字內，限制不超過80字, 除非當請求為翻譯時, 全部內容都需要完成翻譯不殘留原語言。"},
                        {"role": "user", "content": user_message},
                    ],
                    model=model.lower(),
                )
                if not chat_completion.choices:
                    return "❌ 狗蛋無法回應，請稍後再試。"

                content = chat_completion.choices[0].message.content.strip()
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                return content

        except requests.exceptions.RequestException as e:
            print(f"❌ API 連線失敗 (第 {i+1} 次)：{e}")
            time.sleep(backoff_factor * (2 ** i))  # 指數退避 (1s, 2s, 4s)

        except Exception as e:
            print(f"❌ AI API 呼叫錯誤: {e}")
            return "❌ 狗蛋伺服器錯誤，請稍後再試。"

    return "❌ 無法連線至 AI 服務，請稍後再試。"

def random_reply(reply_token, target, messaging_api):

    reply_messages = [
    "😏 哇，你終於想起家裡還有我這號人物了？",
    "🤔 小時候那麼乖，怎麼長大了反而學壞了？",
    "🙄 這麼多親戚，怎麼只有我記得幫忙？",
    "😎 你長大了嘛，什麼事都不用家人操心了，對吧？",
    "🥱 家裡是你旅館嗎？回來就吃飯，吃完就走？",
    "😂 現在會頂嘴了，長大了不起了是不是？",
    "😌 我們這輩子就這樣吧，下輩子不欠你的了。",
    "🤥 你說什麼都對，反正長輩講話都沒人聽啦。",
    "😇 嗯，你的道理聽起來很棒，但還是要聽我的。",
    "😏 這次考不好沒關係，反正你習慣了。",
    "🙄 每次說幫忙都說在忙，那你的忙是什麼時候結束？",
    "🥲 哦？家裡不是你的避風港嗎？怎麼一出事就消失？",
    "😌 反正我都是最閒的，你們才是最忙的嘛。",
    "😎 家裡的事跟你無關？行啊，以後財產分配也不關你的事。",
    "😒 啊～小時候那麼乖，怎麼現在只會氣人？",
    "🥱 沒事，你開心就好，家裡怎麼樣都不重要對吧？",
    "😏 你長大了，學會自己做決定了，出事可別找家裡哦。",
    "🙃 哇，難得見到你，你今天是客人還是家人？",
    "😇 你還記得家裡住哪嗎？怕你迷路呢。",
    "😌 好啦好啦，家裡的事你不用管，反正你最忙最累了。",
    "😏 哇，你終於有空理我了？",
    "🤔 你這麼忙，連回個訊息的時間都沒有嗎？",
    "😂 哦，你現在開始有標準了？當初不是什麼都可以？",
    "😇 哇，你的愛情觀好偉大喔，我配不上你呢。",
    "🙄 又在講大道理？還是說你根本沒打算解決問題？",
    "😎 我知道啊，你很特別，特別會讓人心累。",
    "🥱 你的承諾比天氣預報還不準呢。",
    "😏 你說你沒變？哦，那是我自己長大了啦。",
    "😂 你的愛是限量供應的嗎？怎麼輪到我時就沒了？",
    "😌 我們的關係就像天氣，時好時壞，全看你的心情。",
    "🙃 哇，這次冷戰比上次撐得更久，進步了呢！",
    "🥱 你每次都這樣，然後期待我當沒事？",
    "😇 哦，所以現在是我錯了？好啦，我認錯，滿意了吧？",
    "😏 你對別人都很好，對我特別不一樣呢，真特別。",
    "😂 你的道歉就像廣告，重複很多次但沒什麼用。",
    "🙄 哦，你現在才發現我是個不錯的人？晚了呢～",
    "😎 你說你不會再這樣？好啊，這是第幾次了呢？",
    "😌 你這麼愛自由，談什麼戀愛啊？去當風吧。",
    "😂 你說我們之間沒問題？對啊，問題都是我的。",
    "😇 嗯，分手後你過得很好，謝謝你讓我見識什麼叫成長。",
    "😏 哇，你的貢獻好大喔，真的沒有你不行呢！",
    "🤔 這麼簡單的事都搞不定，真的沒問題嗎？",
    "🙄 哦，所以這次的問題還是我的錯？好喔～",
    "😂 哇，你好忙啊，忙著讓別人幫你做事？",
    "😇 這種工作強度你都撐不住，那還是別做了吧？",
    "😏 哦，原來拖延時間也是你的專業技能之一啊？",
    "🥱 這次又是什麼理由？等一下要不要再編一個？",
    "😎 你的 KPI 是擺爛吧？怎麼還沒達標？",
    "😂 我以為你是來工作的，沒想到是來度假的。",
    "😇 你這個決定很有創意呢，特別容易出事的那種。",
    "🙄 這麼簡單的事都要問？你的腦子是裝飾品嗎？",
    "😏 你要的東西「剛剛」才發給你，剛剛是三天前。",
    "🥱 你的效率真讓人感動，感動到想哭。",
    "😌 你是來這裡解決問題的，還是來製造問題的？",
    "😂 哇，你的「馬上」和我的「馬上」果然不是同一個時區的。",
    "😎 你的領悟能力真的很獨特，特別慢。",
    "🙄 哦，現在是我的問題了？好啊，我背鍋習慣了。",
    "😏 你這麼會找藉口，不去當小說家真的可惜了。",
    "🥱 你真的不怕工作做不完嗎？還是你根本不打算做？",
    "😂 哇，你的職場生存技能是什麼？推卸責任嗎？"
    ]
    chosen_message = random.choice(reply_messages)
    reply_request = ReplyMessageRequest(
        replyToken=reply_token,
        messages=[TextMessage(text=chosen_message)]
    )
    messaging_api.reply_message(reply_request)

def generate_image_with_openai(prompt):
    """
    使用 OpenAI 圖像生成 API 生成圖片，返回圖片 URL。
    參數:
      prompt: 圖像生成提示文字
    """
    try:
        #from openai import OpenAI
        #client_openai_image = OpenAI()
        #response = client_openai_image.image.generate(
        #    model="gpt-image-1",
        #   prompt=f"請根據描述生成圖片。如果描述涉及人物，以可愛卡通風格呈現；如果描述涉及物品，請生成清晰且精美的物品圖像。 描述:{prompt}",
        #    n = 1,
        #    size = "512x512"
        #)
        response = openai.Image.create(
            model="gpt-image-1-mini",
            prompt=f"{prompt}",
            n=1,
            size="1024x1024"
        )
        data = response.get("data", [])
        if not data or len(data) == 0:
            print("❌ 生成圖片時沒有回傳任何資料")
            return None
        image_url = data[0].get("url")
        print(f"生成的圖片 URL：{image_url}")
        return image_url
    except Exception as e:
        print(f"❌ 生成圖像錯誤: {e}")
        return None

def async_generate_and_send_image(target_id, prompt, messaging_api):
    image_url = generate_image_with_openai(prompt)
    if image_url:
        push_request = PushMessageRequest(
            to=target_id,
            messages=[ImageMessage(original_content_url=image_url, preview_image_url=image_url)]
        )
        messaging_api.push_message(push_request)
    else:
        push_request = PushMessageRequest(
            to=target_id,
            messages=[TextMessage(text="❌ 圖片生成失敗，請稍後再試！")]
        )
        messaging_api.push_message(push_request)

def handle_generate_image_command(reply_token, prompt, messaging_api):
    """
    呼叫圖片生成 API 並使用 reply_message 一次性回覆所有訊息。
    注意：此流程必須在 reply token 有效期限內完成（約 60 秒）。
    """
    messages = []

    # 同步呼叫 OpenAI 圖像生成 API
    image_url = generate_image_with_openai(prompt)
    if image_url:
        messages.append(ImageMessage(original_content_url=image_url, preview_image_url=image_url))
        messages.append(TextMessage(text="生成完成, 你瞧瞧🐧"))
    else:
        messages.append(TextMessage(text="❌ 圖片生成失敗，請稍後再試！"))

    # 建立並發送 ReplyMessageRequest（只使用 reply_message）
    reply_request = ReplyMessageRequest(
        replyToken=reply_token,  # 這裡一定要傳入正確的 reply token
        messages=messages
    )
    try:
        messaging_api.reply_message(reply_request)
        print("成功使用 reply_message 回覆圖片生成結果")
    except Exception as e:
        print(f"❌ 發送圖片回覆時出錯: {e}")

def summarize_with_openai(search_results, query):
    """使用 OpenAI API 進行摘要"""
    if not search_results:
        print("❌ [DEBUG] 沒有搜尋結果，無法摘要！")
        return "找不到相關資料。"

    formatted_results = "\n".join(search_results)

    print(f"📢 [DEBUG] 傳送給 OpenAI 的內容:\n{formatted_results}")

    prompt = f"""
    使用者查詢: {query}

    以下是 Google 搜尋結果的標題與連結：
    {formatted_results}

    根據這些結果提供簡單明瞭的摘要（100 字內）。
    **請忽略新聞網站首頁或過期新聞（如 2017 回顧新聞），僅總結最新的有效內容**。
    **若資料多為天氣內容, 請確認日期符合後簡述推論天氣可能有什麼變化**。
    **若資料多為財金股市內容, 請簡述在這些資料內可以知道什麼趨勢**
    **若資料多娛樂八卦內容, 請簡述在這些資料內可以猜測有什麼事情發生了**
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "你是一個智慧助理，依照這些資料, 條列總結跟附上連結。"},
                  {"role": "user", "content": prompt}]
    )

    reply_text = response["choices"][0]["message"]["content"].strip()

    print(f"📢 [DEBUG] OpenAI 回應: {reply_text}")

    return reply_text

def google_search(query):
    """使用 Google Custom Search API 進行搜尋"""
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_KEY}&cx={GOOGLE_CX}"
    response = requests.get(url)

    print(f"📢 [DEBUG] Google 搜尋 API 回應: {response.status_code}")
    print(f"📢 [DEBUG] Google API 回應內容: {response.text}")

    if response.status_code != 200:
        return None

    results = response.json()
    search_results = []
    
    if "items" in results:
        for item in results["items"][:5]:  # 取前 5 筆搜尋結果
            search_results.append(f"{item['title']} - {item['link']}")

    print(f"📢 [DEBUG] Google 搜尋結果: {search_results}")

    return search_results if search_results else None

def validate_wikipedia_keyword(name):
    """檢查 AI 建議的關鍵字是否真的有 Wikipedia 頁面"""
    wiki = wikipediaapi.Wikipedia(user_agent="MyLineBot/1.0", language="zh")
    page = wiki.page(name)
    return page.exists()

def search_wikidata(name):
    """查詢 Wikidata，回傳摘要內容"""
    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": "zh",
        "format": "json"
    }
    response = requests.get(WIKIDATA_API_URL, params=params)
    data = response.json()

    if "search" in data and data["search"]:
        entity_id = data["search"][0]["id"]  # 取第一個結果
        entity_url = f"https://www.wikidata.org/wiki/{entity_id}"
        return entity_id, entity_url
    return None, None

def search_person_info(name):
    """查詢維基百科，若無則讓 AI 生成回應"""

    wiki_wiki = wikipediaapi.Wikipedia(user_agent="MyLineBot/1.0", language="zh")
    page = wiki_wiki.page(name)

    if page.exists():
        wiki_content = page.summary[:500]  # 取前 500 字
        print(f"📢 [DEBUG] 維基百科查詢成功: {wiki_content[:50]}...")

        # 如果維基百科條目有歧義，提示使用者提供更精確的關鍵字
        if "可能是下列" in wiki_content or "可能指" in wiki_content or "可以指" in wiki_content:
            return f"找到多個相關條目，請提供更精確的關鍵字：\n{wiki_content[:200]}...", f"{BASE_URL}/static/blackquest.jpg"

        # 搜尋對應圖片
        image_url = search_google_image(name)
        ai_prompt = f"請用 4-5 句話介紹 {name} 是誰。\n\n維基百科內容:\n{wiki_content}, 限制使用繁體中文回答"

    else:
        print(f"❌ [DEBUG] 維基百科無結果，改用 AI 猜測")
        
        # AI 猜測時，加上標籤 [AI自動生成]
        ai_prompt = f"請用 4-5 句話介紹 {name} 是誰，並確保資訊準確，限制使用繁體中文回答"
        response_text = ask_groq(ai_prompt, "deepseek-r1-distill-llama-70b")
        
        # 加上 AI 自動生成標註
        response_text = f"[未找到對應內容-由AI自動生成]\n{response_text}"
        
        # 使用預設圖片 hello.jpg
        return response_text, f"{BASE_URL}/static/airesponse.jpg"

    # AI 生成回應
    response_text = ask_groq(ai_prompt, "deepseek-r1-distill-llama-70b", "normal_egg")
    print(f"📢 [DEBUG] AI 回應: {response_text[:50]}...")

    return response_text, image_url

def create_flex_message(text, image_url):
    """建立 Flex Message，確保圖片可顯示"""
    if not image_url or not image_url.startswith("http"):
        return TextMessage(text="找不到適合的圖片，請換個關鍵字試試！")

    flex_content = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "16:9",
            "aspectMode": "fit",
            "action": {
                "type": "uri",
                "uri": image_url  # ✅ 點擊後可查看原圖
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": text,
                    "wrap": True,
                    "weight": "bold",
                    "size": "md"
                }
            ]
        }
    }

    flex_json_str = json.dumps(flex_content)
    flex_contents = FlexContainer.from_json(flex_json_str)
    return FlexMessage(alt_text=text, contents=flex_contents)

def search_google_image(query):
    """使用 Google Custom Search API 搜尋可直接顯示的圖片 URL"""
    search_url = "https://www.googleapis.com/customsearch/v1"

    params = {
        "q": query,
        "cx": GOOGLE_CX,
        "key": GOOGLE_SEARCH_KEY,
        "searchType": "image",  # 只搜尋圖片
        "num": 2,  # 取得 2 張圖片，確保至少有 1 張可用
        "imgSize": "xlarge",  # 嘗試獲取更高清圖片
        "fileType": "jpg,png",  # 確保回傳的是圖片，不是其他格式
        "safe": "off"
    }

    try:
        response = requests.get(search_url, params=params)
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                image_url = item["link"]

                # ❌ 過濾 Facebook / Instagram / 動態圖片 (帶 `?` 參數的)
                if "fbcdn.net" in image_url or "instagram.com" in image_url or "?" in image_url:
                    continue

                # 🔍 確保圖片可以直接存取（不重定向）
                img_response = requests.get(image_url, allow_redirects=False)
                if img_response.status_code == 200:
                    return image_url  # ✅ 返回可用圖片

    except Exception as e:
        print(f"❌ Google Custom Search API 錯誤: {e}")

    return None  # 找不到可顯示的圖片時回傳 None

def search_spotify_song(song_name):
    """ 透過 Spotify API 搜尋歌曲並回傳預覽 URL 與歌曲連結 """
    try:
        results = sp.search(q=song_name, limit=1, type='track')
        if not results["tracks"]["items"]:
            return None  # 沒找到歌曲
        
        track = results["tracks"]["items"][0]
        return {
            "name": track["name"],
            "preview_url": track["preview_url"],  # 30 秒的音頻預覽
            "song_url": track["external_urls"]["spotify"]  # Spotify 播放連結
        }
    except Exception as e:
        print(f"❌ [ERROR] Spotify API 呼叫失敗: {e}")
        return None

def download_and_host_audio(preview_url, filename="song_preview"):
    """ 下載 Spotify 的 preview.mp3，轉換為 m4a，並存到 Flask 的 /static/ 目錄 """
    tmp_mp3 = f"/tmp/{filename}.mp3"  # 暫存 mp3
    tmp_m4a = f"/tmp/{filename}.m4a"  # 暫存 m4a
    static_m4a = f"./static/{filename}.m4a"  # 最終存放於 Flask 可訪問的 /static/
    hosted_url = f"{BASE_URL}/static/{filename}.m4a"  # 你的 Flask 伺服器網址

    try:
        response = requests.get(preview_url, stream=True)
        if response.status_code == 200:
            # 下載 mp3
            with open(tmp_mp3, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            # 轉換為 m4a
            audio = AudioSegment.from_mp3(tmp_mp3)
            audio.export(tmp_m4a, format="ipod")  # "ipod" 會輸出 .m4a 格式
            
            # 移動檔案到 Flask 的 /static/ 目錄
            shutil.move(tmp_m4a, static_m4a)

            print(f"✅ 音檔轉換成功: {static_m4a}")
            return hosted_url
        else:
            print("❌ 下載失敗，狀態碼:", response.status_code)
            return None
    except Exception as e:
        print(f"❌ 下載或轉換失敗: {e}")
        return None

def get_weather_weatherapi(city):
    """ 使用 OpenWeather API 查詢天氣 """
    API_KEY = OPENWEATHER_API_KEY
    try:
        # 確保 city 是 OpenWeather 可接受的名稱
        city = CITY_MAPPING.get(city, city)

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=zh_tw"
        print(f"📢 [DEBUG] 呼叫 API: {url}")  # 確保 city 轉換正確
        
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            print(f"❌ OpenWeather API 錯誤: {data}")  # Debug API 回應
            return "❌ 無法取得天氣資訊，請確認城市名稱是否正確"

        # 提取需要的天氣資訊
        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]
        humidity = data["main"]["humidity"]
        # 建立天氣描述
        weather_text = (
                f"🌡 溫度：{temp}°C\n"
                f"💧 濕度：{humidity}%\n"
                f"💨 風速：{wind_speed} m/s\n"
                f"🌤 天氣狀況：{weather_desc}"
        )
        # 讓 AI 進行天氣分析
        ai_analysis = analyze_weather_with_ai(city, temp, humidity, weather_desc, wind_speed)

        return f"🌍 {city} 即時天氣預報：\n{weather_text}\n\n🧑‍🔬 狗蛋關心您：\n{ai_analysis}"


    except requests.exceptions.RequestException as e:
        return f"❌ 取得天氣資料失敗: {e}"

def get_weather_forecast(city):
    """ 使用 OpenWeather API 查詢未來 3 天天氣趨勢 並產生圖表 """
    # 確保 city 是 OpenWeather 可接受的名稱
    city = CITY_MAPPING.get(city, city)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=zh_tw"
    
    try:
        response = requests.get(url)
        data = response.json()
        print("🔍 狀態碼:", response.status_code)
        # print("🔍 回應內容:", response.text)

        if data.get("cod") != "200":
            print(f"❌ OpenWeather API 錯誤: {data}")
            return "❌ 無法取得天氣預報，請確認城市名稱是否正確", None

        daily_forecast = {}

        # 解析 5 天的 3 小時預測，整理成每日的天氣趨勢
        for forecast in data["list"]:
            date = forecast["dt_txt"].split(" ")[0]  # 只取日期
            temp = forecast["main"]["temp"]
            weather_desc = forecast["weather"][0]["description"]
            wind_speed = forecast["wind"]["speed"]
            humidity = forecast["main"]["humidity"]
            # 降雨機率欄位 pop，值介於 0~1
            pop = forecast.get("pop", 0)

            if date not in daily_forecast:
                daily_forecast[date] = {
                    "temp_min": temp,
                    "temp_max": temp,
                    "humidity": [humidity],
                    "wind_speed": [wind_speed],
                    "pop": [pop],
                    "weather_desc": weather_desc
                }
            else:
                daily_forecast[date]["temp_min"] = min(daily_forecast[date]["temp_min"], temp)
                daily_forecast[date]["temp_max"] = max(daily_forecast[date]["temp_max"], temp)
                daily_forecast[date]["humidity"].append(humidity)
                daily_forecast[date]["wind_speed"].append(wind_speed)
                daily_forecast[date]["pop"].append(pop)

        # 格式化輸出未來 3 天預測
        forecast_text = f"🌍 {city} 未來 3 天天氣趨勢：\n"
        count = 0

        for date, info in daily_forecast.items():
            if count >= 3:
                break
            avg_humidity = sum(info["humidity"]) // len(info["humidity"]) if info["humidity"] else 0
            avg_wind_speed = sum(info["wind_speed"]) / len(info["wind_speed"]) if info["wind_speed"] else 0
            avg_pop = (sum(info["pop"]) / len(info["pop"]) * 100) if info["pop"] else 0  # 百分比表示
            forecast_text += (
                f"\n📅 {date}:\n"
                f"🌡 溫度: {info['temp_min']}°C ~ {info['temp_max']}°C\n"
                f"💧 濕度: {avg_humidity}%\n"
                f"💨 風速: {avg_wind_speed:.1f} m/s\n"
                f"🌧 降雨機率: {avg_pop:.0f}%\n"
                f"🌤 天氣: {info['weather_desc']}\n"
            )
            count += 1

        # 讓 AI 進行天氣分析（參數示範取最後一筆資料）
        ai_analysis = analyze_weather_with_ai(city, temp, humidity, weather_desc, wind_speed)
        forecast_text += f"\n\n🧑‍🔬 狗蛋關心您：\n{ai_analysis}"

        # 產生圖表：使用原始預測資料，顯示未來 3 天每 3 小時的預測點
        import datetime
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        chart_times = []
        chart_temps = []
        chart_pops = []
        now = datetime.datetime.now()
        three_days_later = now + datetime.timedelta(days=3)
        for forecast in data["list"]:
            dt = datetime.datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
            if now <= dt <= three_days_later:
                chart_times.append(dt)
                chart_temps.append(forecast["main"]["temp"])
                chart_pops.append(forecast.get("pop", 0) * 100)  # 轉換成百分比

        # 繪製圖表：x 軸每 6 小時一個刻度
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(chart_times, chart_temps, marker="o", color="red", label="Temp (°C)")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Temp (°C)", color="red")
        ax1.tick_params(axis="y", labelcolor="red")
        # 設定 x 軸刻度：每6小時一個刻度，格式顯示「月-日 小時:分鐘」
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        fig.autofmt_xdate()

        # 新增第二條線：降雨機率，並用右側 y 軸顯示
        ax2 = ax1.twinx()
        ax2.plot(chart_times, chart_pops, marker="o", color="blue", label="Rain (%)")
        ax2.set_ylabel("Rain (%)", color="blue")
        ax2.tick_params(axis="y", labelcolor="blue")

        # 合併圖例，顯示在右上角
        # lines, labels = ax1.get_legend_handles_labels()
        # lines2, labels2 = ax2.get_legend_handles_labels()
        # ax2.legend(lines + lines2, labels + labels2, loc="upper right")

        plt.title(f"{city} Forcast in next 3 days")
        plt.grid(True)
        plt.tight_layout()
        chart_filename = f"./static/{city}_weather_chart.png"
        plt.savefig(chart_filename)
        plt.close()

        return forecast_text, f"{city}_weather_chart.png"

    except requests.exceptions.RequestException as e:
        return f"❌ 取得天氣資料失敗: {e}", None

def analyze_weather_with_ai(city, temp, humidity, weather_desc, wind_speed):
    """ 使用 OpenAI 進行天氣分析，提供穿搭 & 注意事項 """

    prompt = f"""
    目前 {city} 的天氣條件如下：
    - 溫度：{temp}°C
    - 濕度：{humidity}%
    - 天氣狀況：{weather_desc}
    - 風速：{wind_speed} m/s

    根據這些數據：
    1. 給出適合的穿搭建議（例如：冷天穿什麼、熱天注意什麼）。
    2. 提供出門注意事項（如可能下雨、空氣品質不好、強風等）。
    3. 回應時請使用繁體中文，字數控制在 50 字內，並用口語化的方式回答。
    """

    # Groq API 邏輯 (保持不變)
    chat_completion = client.chat.completions.create(
        messages=[
                    {"role": "system", "content": "你是一個名叫狗蛋的助手，跟使用者是朋友關係, 盡量只使用繁體中文方式進行幽默回答, 約莫20字內，限制不超過50字"},
                    {"role": "user", "content": prompt},
                ],
        model="deepseek-r1-distill-llama-70b",)
    if not chat_completion.choices:
        return "❌ 狗蛋無法回應，請稍後再試。"
    content = chat_completion.choices[0].message.content.strip()
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content

def get_video_data(search_query):
    url = f"https://jable.tv/search/{search_query}/?sort_by=post_date"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # ✅ 關閉 headless=False，提升速度
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context()
        page = context.new_page()

        # ✅ 避免被封鎖，使用 Stealth
        #stealth_sync(page)

        # ✅ 隨機 User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Mobile Safari/537.36",
        ]
        page.set_extra_http_headers({"User-Agent": random.choice(user_agents)})

        # ✅ **減少 `timeout` 時間，提升速度**
        page.goto(url, timeout=50000)  # **減少超時時間**
        page.wait_for_load_state("networkidle")  # 確保所有資源載入完成
        page.wait_for_selector(".video-img-box", timeout=15000)  # **減少等待時間**
        
        # ✅ **直接解析 HTML，不用 `set_content()`**
        html = page.content()

        # **確保 HTML 內容不是 Cloudflare 防護頁**
        if "Just a moment..." in html or "challenge-error-text" in html:
            print("❌ Cloudflare 防護阻擋，無法獲取內容")
            browser.close()
            return []

        # ✅ **直接解析 HTML**
        videos = page.query_selector_all('.video-img-box')
        video_list_data = []

        for video in videos[:2]:  # **只取前 2 部影片**
            title_elem, img_elem = video.query_selector('.title a'), video.query_selector('.img-box img')

            title = title_elem.text_content().strip() if title_elem else "N/A"
            link = title_elem.get_attribute('href') if title_elem else "N/A"
            thumbnail = img_elem.get_attribute('data-src') or img_elem.get_attribute('src') if img_elem else "N/A"

            video_list_data.append({"title": title, "link": link, "thumbnail": thumbnail})

        # ✅ **確保瀏覽器完全關閉**
        browser.close()
        return video_list_data

def get_video_data_hotest():
    url = "https://jable.tv/hot/"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context()
        page = context.new_page()

        # ✅ 避免被封鎖，使用 Stealth
        #stealth_sync(page)

        # ✅ 隨機 User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Mobile Safari/537.36",
        ]
        page.set_extra_http_headers({"User-Agent": random.choice(user_agents)})

        # ✅ **降低等待時間**
        page.goto(url, timeout=50000)  # **減少超時時間**
        page.wait_for_load_state("networkidle")  # 確保所有資源載入完成
        page.wait_for_selector(".video-img-box", timeout=15000)  # **減少 selector 等待時間**

        # ✅ **直接解析 HTML，不用 set_content()**
        videos = page.query_selector_all('.video-img-box')

        video_list_data = []
        for video in videos[:3]:  # **取前三個影片**
            title_elem, img_elem = video.query_selector('.title a'), video.query_selector('.img-box img')

            title = title_elem.text_content().strip() if title_elem else "N/A"
            link = title_elem.get_attribute('href') if title_elem else "N/A"
            thumbnail = img_elem.get_attribute('data-src') or img_elem.get_attribute('src') if img_elem else "N/A"

            video_list_data.append({"title": title, "link": link, "thumbnail": thumbnail})

        # ✅ **減少記憶體佔用**
        browser.close()
        return video_list_data

def get_video_data_newest():
    url = "https://jable.tv/latest-updates/"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context()
        page = context.new_page()

        # ✅ 啟用 Stealth 模式
        #stealth_sync(page)

        # ✅ 變更 User-Agent 以模擬真實瀏覽器
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })

        # ✅ 設定 Cookie 允許 JS 運行
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # ✅ 瀏覽網頁並等待完全加載
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle")  # 等待 JS 加載完成

        # ✅ 檢查是否仍然卡在驗證頁面
        if "Verifying you are human" in page.content():
            print("❌ Cloudflare 人機驗證擋住爬蟲，請改用手動 Cookie 或其他方法")
            browser.close()
            return []

        # ✅ 抓取影片資訊
        videos = page.query_selector_all('.video-img-box')
        video_list_data = []

        for video in videos[:3]:  # 取前三個影片
            title_elem = video.query_selector('.title a')
            title = title_elem.text_content().strip() if title_elem else "N/A"
            link = title_elem.get_attribute('href') if title_elem else "N/A"
            video_list_data.append({"title": title, "link": link})

        browser.close()
        return video_list_data

def create_flex_jable_message_nopic(videos):
    if not videos:
        return TextMessage(text="找不到相關影片，請嘗試其他關鍵字。")

    # 格式化影片資訊，標題 + 影片網址
    message_text = "🔥 最新影片 🔥\n\n"
    for video in videos:
        message_text += f"🎬 {video['title']}\n🔗 {video['link']}\n\n"

    return TextMessage(text=message_text.strip())  # 去掉最後的換行符號

# def create_flex_jable_message(videos):
#     if not videos:
#         return TextMessage(text="找不到相關影片，請嘗試其他關鍵字。")

#     contents = []
#     for video in videos:
#         print(f"✅ [DEBUG] 準備加入影片: {video}")  # Debug 確認資料格式

#         bubble = {
#             "type": "bubble",
#             "hero": {
#                 "type": "image",
#                 "url": video["thumbnail"],
#                 "size": "full",
#                 "aspectRatio": "16:9",
#                 "aspectMode": "cover",
#                 "action": {
#                     "type": "uri",
#                     "uri": video["link"]
#                 }
#             },
#             "body": {
#                 "type": "box",
#                 "layout": "vertical",
#                 "contents": [
#                     {
#                         "type": "text",
#                         "text": video["title"],
#                         "weight": "bold",
#                         "size": "md",
#                         "wrap": True
#                     }
#                 ]
#             },
#             "footer": {
#                 "type": "box",
#                 "layout": "vertical",
#                 "spacing": "sm",
#                 "contents": [
#                     {
#                         "type": "button",
#                         "style": "primary",
#                         "action": {
#                             "type": "uri",
#                             "label": "觀看影片",
#                             "uri": video["link"]
#                         }
#                     }
#                 ]
#             }
#         }
#         contents.append(bubble)

#     flex_message_content = {
#         "type": "carousel",
#         "contents": contents
#     }

#     # print(f"✅ [DEBUG] 最終 FlexMessage 結構: {json.dumps(flex_message_content, indent=2)}")  # Debug

#     # ✅ **轉換為 JSON 字串，讓 `FlexContainer.from_json()` 可以解析**
#     flex_json_str = json.dumps(flex_message_content)

#     flex_contents = FlexContainer.from_json(flex_json_str)  # ✅ 解析 JSON 字串
#     return FlexMessage(alt_text="搜尋結果", contents=flex_contents)

def create_flex_jable_message(user_id, videos):
    global video_batches, batch_index

    if not videos:
        return TextMessage(text="找不到相關影片，請嘗試其他關鍵字。")

    # ✅ **將 影片拆成組，每組 3 部**
    video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
    batch_index[user_id] = 0  # **初始化顯示第一組**

    return generate_flex_message(user_id)

def generate_videos_flex_message(user_id, video_selection="latest"):
    video_titles = {
        "movies": "Movies",
        "dramas": "Dramas",
        "cartones": "Cartoons",
        "expert": "Expert Picks",
    }

    selected_category = video_titles.get(video_selection, "Latest Videos")

    flex_contents_json = {
        "type": "carousel",
        "contents": [
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": f"{BASE_URL}/static/workegg.png",
                    "size": "md"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "justifyContent": "center",  # 讓內容垂直置中
                    "alignItems": "center",  # 讓內容水平置中
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{selected_category}\n功能施工中，忙不過來啦",
                            "wrap": True,
                            "size": "md",
                            "weight": "bold",
                            "align": "center"  # 文字置中
                        }
                    ]
                }
            }
        ]
    }

    # 轉換成 FlexContainer
    flex_container = FlexContainer.from_dict(flex_contents_json)

    return FlexMessage(alt_text="搜尋結果", contents=flex_container)

def generate_flex_message(user_id, mode="latest"):
    """ 根據當前批次，生成對應的 FlexMessage """
    global video_batches, batch_index

    if user_id not in video_batches:
        return TextMessage(text="請先搜尋影片！")

    batch = video_batches[user_id][batch_index[user_id]]

    # ✅ **隨機選擇一個人名**
    random_actress = get_random_actress()

    # ✅ **隨機選擇一個 AV 系列**
    random_series = get_random_series()

    # ✅ **獲取最新的 scraped_at（YYYY-MM-DD）**
    latest_scraped_at = get_latest_scraped_at()

    contents = []
    for video in batch:
        bubble = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": video["thumbnail"],
                "size": "full",
                "aspectRatio": "16:9",
                "aspectMode": "cover",
                "action": {
                    "type": "uri",
                    "uri": video["link"]
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": video["title"],
                        "weight": "bold",
                        "size": "md",
                        "wrap": True
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "觀看影片",
                            "uri": video["link"]
                        }
                    }
                ]
            }
        }
        contents.append(bubble)

    # ✅ **按使用者當前的 mode 變更按鈕**
    change_label = "換熱門" if mode == "latest" else "換最新"
    change_data = f"change_popular|{user_id}" if mode == "latest" else f"change_latest|{user_id}"

    button_bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "height": "300px",
            "justifyContent": "space-between",
            "contents": [
                {
                    "type": "button",
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": "換一批",
                        "data": f"change_batch|{user_id}"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": change_label,
                        "data": change_data
                    }
                },
                {
                    "type": "button",  # ✅ **隨機演員按鈕**
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": random_actress,  # ✅ **顯示隨機人名**
                        "data": f"change_actress|{user_id}|{random_actress}"  # ✅ **帶入人名**
                    }
                },
                {
                    "type": "button",  # ✅ **隨機系列按鈕**
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": random_series,  # ✅ **顯示隨機系列**
                        "data": f"change_series|{user_id}|{random_series}"  # ✅ **帶入系列名稱**
                    }
                },
                {
                    "type": "box",  # ✅ **圖片 + Last Update**
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "image",
                            "url": f"{BASE_URL}/static/badegg.png",
                            "size": "md",
                            "aspectRatio": "16:9",
                            "aspectMode": "cover",
                            "alignSelf": "flex-start",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": f"Last Update: {latest_scraped_at}",
                            "size": "xs",
                            "color": "#888888",
                            "align": "center",
                            "margin": "md",
                            "wrap": True
                        }
                    ]
                }
            ]
        }
    }

    contents.append(button_bubble)

    flex_message_content = {
        "type": "carousel",
        "contents": contents
    }

    flex_json_str = json.dumps(flex_message_content)
    flex_contents = FlexContainer.from_json(flex_json_str)
    return FlexMessage(alt_text="搜尋結果", contents=flex_contents)

def text_to_speech(text: str, rate: int = 0) -> bytes:
    """
    使用 VoiceRSS TTS API 將文字轉換成語音（二進位資料），並根據輸入文字自動偵測語言，
    同時將偵測到的語言轉換為 VoiceRSS 支援的語言代碼後再發送 API 請求。
    
    參數:
      - text: 要轉換的文字
      - rate: 語速參數 (-10 ~ 10)，預設為 0 (正常語速)
      
    回傳:
      - 轉換後的 MP3 格式音訊二進位資料，若失敗則回傳 None
    """
    # 自動偵測輸入文字的語言
    try:
        detected_lang = detect(text)
    except Exception as e:
        print("語言偵測失敗，預設使用英文。", e)
        detected_lang = "en"
    
    # 根據偵測結果取得對應的 VoiceRSS 語言代碼
    language = LANGUAGE_MAP.get(detected_lang.lower(), "en-us")
    print("偵測到的語言:", detected_lang, "=> 使用語言參數:", language)
    
    encoded_text = quote(text)
    
    # 使用傳入的 rate 參數
    tts_url = f"http://api.voicerss.org/?key={VRSS_API_KEY}&hl={language}&r={0}&src={encoded_text}"
    print("TTS URL:", tts_url)
    
    response = requests.get(tts_url)
    if response.status_code == 200:
        # 若回傳資料為二進位音訊，不要 decode，否則可能產生錯誤
        print("TTS API 回傳內容大小:", len(response.content))
        return response.content
    else:
        print("TTS API 錯誤，狀態碼:", response.status_code, "回傳內容:", response.content)
        return None

def upload_audio(audio_data: bytes) -> str:
    """
    將音檔存入 static/audio 目錄，並回傳公開 URL。
    請確認你的伺服器已設定好 static 目錄能夠公開存取。
    """
    audio_dir = os.path.join(app.static_folder, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    file_path = os.path.join(audio_dir, filename)
    with open(file_path, "wb") as f:
        f.write(audio_data)
    # 檢查檔案是否成功儲存
    if not os.path.exists(file_path):
        print("檔案不存在:", file_path)
    public_url = f"{BASE_URL}/static/audio/{filename}"
    private_url = f"./static/audio/{filename}"
    return public_url, private_url

def get_audio_duration(audio_bytes: bytes) -> int:
    """
    根據 MP3 的二進位資料自動偵測音訊長度，並回傳毫秒數。
    """
    # 使用 BytesIO 包裝二進位資料，讓 mutagen 能讀取
    audio_file = io.BytesIO(audio_bytes)
    audio = MP3(audio_file)
    duration_seconds = audio.info.length  # 時長（秒）
    duration_ms = int(duration_seconds * 1000)  # 換算成毫秒
    return duration_ms

def geocode_location(location_name):
    params = {'address': location_name, 'key': GOOGLE_SEARCH_KEY}
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
    data = response.json()
    if data.get('status') == 'OK' and data.get('results'):
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None

def search_nearby_location(latitude, longitude, store_type):
    params = {
        'location': f"{latitude},{longitude}",
        'radius': 1000,
        'keyword': store_type,  # 以關鍵字搜尋使用者指定的店面類型
        'key': GOOGLE_SEARCH_KEY
    }
    response = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)
    data = response.json()
    if data.get('status') == 'OK' and data.get('results'):
        results = data['results'][:3]
        reply_text = f"以下是最近的 3 個 {store_type}：\n"
        for i, place in enumerate(results, 1):
            name = place['name']
            address = place.get('vicinity', '地址未提供')
            place_lat = place['geometry']['location']['lat']
            place_lng = place['geometry']['location']['lng']
            maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
            reply_text += f"{i}. {name} - {address}\n{maps_url}\n\n"
        return reply_text
    return f"抱歉，附近找不到相關 {store_type}！"

def get_google_maps_link(lat, lng, place_name):
    """
    根據經緯度生成 Google Maps 連結
    """
    query = f"{lat},{lng}"
    return f"https://www.google.com/maps/search/?api=1&query={query}"

def get_latest_videos_from_database():
    response = supabase.table("videos_latest").select("title, link, thumbnail").order("scraped_at", desc=True).execute()
    # return response.data if response.data else []
    if not response.data:
        return []

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_hotest_videos_from_database():
    response = supabase.table("videos_hotest").select("title, link, thumbnail").order("scraped_at", desc=True).execute()
    # return response.data if response.data else []
    if not response.data:
        return []

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_videos_from_database(search_name, max_title_length):
    """ 從資料庫獲取影片，並限制標題長度 """
    response = supabase.table(f"videos_index_{search_name}").select("title, link, thumbnail").order("scraped_at", desc=True).execute()
    
    if not response.data:
        return []

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_videos_from_database_series(search_name, max_title_length):
    """ 從資料庫獲取影片，並限制標題長度 """
    response = supabase.table(f"videos_series_{search_name}").select("title, link, thumbnail").order("scraped_at", desc=True).execute()
    
    if not response.data:
        return []

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_random_actress():
    """ 隨機選擇一位演員 """
    return random.choice(ACTRESS_AV_NAMES)

def get_random_series():
    return random.choice(ACTRESS_AV_SERIES)

def get_random_movie_series():
    return random.choice(GENERAL_MOVIE_SERIES)

def get_random_netflix_drama_series():
    return random.choice(NETFLIX_DRAMA_SERIES)

def get_random_general_drama_series():
    return random.choice(GENERAL_DRAMA_SERIES)


from datetime import datetime  # ✅ 正確匯入

def get_latest_scraped_at():
    """ 獲取資料庫內最新的 scraped_at 時間，並轉換為 YYYY-MM-DD 格式 """
    response = supabase.table("videos_latest").select("scraped_at").order("scraped_at", desc=True).limit(1).execute()
    
    if not response.data:
        return "N/A"
    
    # ✅ **正確使用 `datetime.strptime()`**
    scraped_at = response.data[0]["scraped_at"]
    return datetime.strptime(scraped_at, "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d")

def get_AVVIDEO_description(name=None):
    """
    輸入女優名稱或系列名稱，返回對應的介紹。
    如果無輸入（name=None 或空字串），返回所有女優和系列介紹。
    如果名稱不存在，返回提示訊息。
    """
    if not name:  # 當 name 為 None 或空字串時
        all_descriptions = []
        all_descriptions.append("=== 女優介紹 ===")
        for actress, desc in ACTRESS_AV_DESCRIPTIONS.items():
            all_descriptions.append(f"{actress}: {desc}")
        all_descriptions.append("\n=== 系列介紹 ===")
        for series, desc in ACTRESS_AV_SERIES_DESCRIPTIONS.items():
            all_descriptions.append(f"{series}: {desc}")
        return "\n".join(all_descriptions)
    
    if name in ACTRESS_AV_DESCRIPTIONS:
        return ACTRESS_AV_DESCRIPTIONS[name]
    elif name in ACTRESS_AV_SERIES_DESCRIPTIONS:
        return ACTRESS_AV_SERIES_DESCRIPTIONS[name]
    else:
        return f"找不到 '{name}' 的介紹，請確認名稱是否正確！"

def find_full_name(keyword, name_list):
    keyword_lower = keyword.lower()
    for full_name in name_list:
        if keyword_lower in full_name.lower():
            return full_name
    return None

def create_flex_user_message(user_id, videos):
    global video_batches, batch_index

    if not videos:
        return TextMessage(text="找不到相關影片，請嘗試其他關鍵字。")

    # ✅ **將 影片拆成組，每組 3 部**
    video_batches[user_id] = [videos[i:i+3] for i in range(0, len(videos), 3)]
    batch_index[user_id] = 0  # **初始化顯示第一組**

    return generate_user_videos_flex_message(user_id)

def generate_user_videos_flex_message(user_id, mode="latest"):
    """ 根據當前批次，生成對應的 FlexMessage """
    global video_batches, batch_index

    if user_id not in video_batches:
        return TextMessage(text="請先搜尋影片！")

    batch = video_batches[user_id][batch_index[user_id]]

    # ✅ **隨機選擇一個電影系列**
    random_movie_series = get_random_movie_series()

    # ✅ **獲取最新的 scraped_at（YYYY-MM-DD）**
    latest_scraped_at = get_latest_scraped_at()

    contents = []
    for video in batch:
        bubble = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": video["thumbnail"],
                "size": "xl",
                "aspectRatio": "4:6",
                "aspectMode": "cover",
                "action": {
                    "type": "uri",
                    "uri": video["link"]
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": video["title"],
                        "weight": "bold",
                        "size": "md",
                        "wrap": True,
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "width": "auto",
                        "height" :"sm",
                        "cornerRadius": "md",  # 讓按鈕變小圓角
                        "paddingAll": "5px", 
                        "action": {
                            "type": "uri",
                            "label": "觀看影片",
                            "uri": video["link"]
                        }
                    }
                ]
            }
        }
        contents.append(bubble)

    # ✅ **按使用者當前的 mode 變更按鈕**
    change_label = "換熱門" if mode == "latest" else "換最新"
    change_data = f"change_popular|{user_id}" if mode == "latest" else f"change_latest|{user_id}"

    button_bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "height": "300px",
            "justifyContent": "space-between",
            "contents": [
                {
                    "type": "button",
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": "換一批",
                        "data": f"change_batch_videos|{user_id}"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": random_movie_series,
                        "data": f"change_movie_series|{user_id}|{random_movie_series}"
                    }
                },
                {
                    "type": "button",  
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": "Momovod Trending Movie", 
                        "data": f"change_latest_momo_videos|{user_id}"  
                    }
                },
                {
                    "type": "button",  
                    "style": "secondary",
                    "flex": 1,
                    "action": {
                        "type": "postback",
                        "label": "Netflix Trending drama",  
                        "data": f"change_latest_netflix_movies|{user_id}"  
                    }
                },
                {
                    "type": "box",  # ✅ **圖片 + Last Update**
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "image",
                            "url": f"{BASE_URL}/static/badegg.png",
                            "size": "md",
                            "aspectRatio": "16:9",
                            "aspectMode": "cover",
                            "alignSelf": "flex-start",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": f"Last Update: {latest_scraped_at}",
                            "size": "xs",
                            "color": "#888888",
                            "align": "center",
                            "margin": "md",
                            "wrap": True
                        }
                    ]
                }
            ]
        }
    }

    contents.append(button_bubble)

    flex_message_content = {
        "type": "carousel",
        "contents": contents
    }

    flex_json_str = json.dumps(flex_message_content)
    flex_contents = FlexContainer.from_json(flex_json_str)
    return FlexMessage(alt_text="搜尋結果", contents=flex_contents)

def get_remote_videos_from_database(search_name, max_title_length):
    """ 從資料庫獲取影片，並限制標題長度 """
    response = supabase.table(f"videos_movies_contents").select("title, link, thumbnail").limit(10).order("scraped_at", desc=True).execute()
    
    if not response.data:
        return []

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_remote_videos_from_momovod_database(search_name, max_title_length):
    """ 從資料庫獲取影片，並限制標題長度 """
    response = supabase.table(f"videos_movies_contents").select("title, link, thumbnail").eq("source_id", 1).limit(10).order("scraped_at", desc=True).execute()
    
    if not response.data:
        return []

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_remote_videos_from_database_movie_series(search_name, max_title_length):
    """ 從資料庫獲取影片，並限制標題長度 """
    response = supabase.table(f"videos_movies_contents").select("title, link, thumbnail").eq("note",search_name).limit(10).order("scraped_at", desc=True).execute()
    if not response.data:
        return [response]

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data

def get_remote_videos_from_database_drama_series(search_name, max_title_length):
    """ 從資料庫獲取影片，並限制標題長度 """
    print(1111111111111111111111111111)
    response = supabase.table(f"videos_movies_contents").select("title, link, thumbnail").eq("source_id", 2).limit(10).order("scraped_at", desc=True).execute()
    if not response.data:
        return [response]

    # ✅ **限制 title 長度**
    for video in response.data:
        if len(video["title"]) > max_title_length:
            video["title"] = video["title"][:max_title_length] + "..."  # **截取並加上 `...`**

    return response.data



if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))  # 使用 Render 提供的 PORT
    app.run(host="0.0.0.0", port=PORT, debug=False)  # 移除 debug=True

