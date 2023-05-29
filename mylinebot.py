from flask import Flask, abort, request, send_file
import requests
from bs4 import BeautifulSoup
import json
import os
import io
import re
#import random
# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
load_dotenv()
base_url = 'https://deorsum.serveo.net'

FlexMessage = {
"replyToken": "00",
    "messages": [{
    "type": "flex",
    "altText": "Flex Message",
    "contents": {
        "type": "bubble",
        "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
            "type": "box",
            "layout": "vertical",
            "margin": "lg",
            "spacing": "sm",
            "contents": [
                {
                "type": "box",
                "layout": "baseline",
                "contents": [
                    {
                    "type": "text",
                    "text": "請確認您是否想要建立一個屬於自己的 Preamble。",
                    "flex": 5,
                    "wrap": True
                    }
                ]
                }
            ]
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
            "style": "link",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": "是",
                "data": "Yes"
            }
            },
            {
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {
                "type": "postback",
                "label": "否",
                "data": "No"
            }
            },
            {
            "type": "box",
            "layout": "vertical",
            "contents": [],
            "margin": "sm"
            }
        ],
        "flex": 0
        }
    }
    }
    ]
}

try:
    connection = mysql.connector.connect(
    host = os.getenv('DATABASE_ADRESS'),          # 主機名稱
    database='linebot_latex', # 資料庫名稱
    user=os.getenv('DATABASE_USERNAME'),        # 帳號
    password=os.getenv('DATABASE_USERPASS'))
    with connection.cursor() as c:
        c.execute(f"SELECT * FROM linelatexpreamble WHERE lineid = \'defult\'")
        file = c.fetchall()
        for i in file:
            file = "".join(i)
            file = file.strip("'").strip("(").strip(")").strip(",")
            with open(f"preambles/{file}.tex", "r") as f:
                LaTeX_Preamble = ""
                for i in f.readlines():
                    LaTeX_Preamble += i
    connection.close()
except:
    pass

def connect_database():
    try:
        connection = mysql.connector.connect(
        host = os.getenv('DATABASE_ADRESS'),          # 主機名稱
        database='linebot_latex', # 資料庫名稱
        user=os.getenv('DATABASE_USERNAME'),        # 帳號
        password=os.getenv('DATABASE_USERPASS'))
        return connection
    except:
        pass


def check_msg (msg: str, tk, access_token, lineid, ):
    regex = re.compile('\s+') 
    msg_split = regex.split(msg)
    tex = False
    insert = False
    delete = False
    for i in msg_split:
        if i == ".tex":
            msg = msg[len(i)+1:]
            tex = True
        elif i == "insert" and tex:
            msg = msg[len(i)+1:]
            insert = True
            return insert_preamble(lineid, msg, access_token, tk)
        elif i == "replace" and tex:
            msg = msg[len(i)+1:]
            return replace_preamble(lineid, msg, access_token, tk)
        elif i == "delete" and tex:
            delete = True
            msg = msg[len(i)+1:]
        elif i == "new" and tex:
            return ask_preamble(tk, access_token, lineid)
        elif i == "show" and tex:
            return show_preamble(lineid, tk, access_token)
        elif i == 'line' and insert:
            return 
        elif i == 'preamble' and delete:
            return 
        elif tex:
            return run_latex(tk, msg, access_token, lineid)
        else:
            print("Error")
            return 4

def preamble_check(lineid):
    with connect_database() as connection:
        with connection.cursor() as c:
            c.execute(f"SELECT * FROM linelatexpreamble WHERE lineid = \'{lineid}\'")
            result = c.fetchall()
    if len(result) == 0:
        return False
    else:
        for i in result:
            val = ''.join(i)
            val = val.strip("'").strip("(").strip(")").strip(",")
            return val

def show_preamble(lineid, tk, access_token):
    file = preamble_check(lineid)
    if file == False:
        reply = "您的 LaTeX Preamble 是預設的，以下是詳細資料：\n" + LaTeX_Preamble
        reply_msg(reply, tk, access_token)
    else:
        with open(f"preambles/{lineid}.tex", "r") as f:
            file = f.readlines()
            preamble = ""
            for i in file:
                preamble += i
            reply = "您的 LaTeX Preamble 是客製化的，以下是詳細資料：\n" + preamble
            reply_msg(reply, tk, access_token)

def ask_preamble(tk, access_token, lineid):
    if not preamble_check(lineid):
        return reply_flex_msg(tk, access_token)
    else:
        return show_preamble(lineid, tk, access_token)
    
def new_preamble(lineid, tk, access_token):
    os.system(f"cat preambles/defult.tex > preambles/{lineid}.tex")
    with connect_database() as connection:
        with connection.cursor() as c:
            c.execute(f"INSERT INTO linelatexpreamble VALUES('{lineid}')")
            connection.commit()
    return show_preamble(lineid, tk, access_token)

def insert_preamble(lineid, msg, access_token, tk):
    if preamble_check(lineid) == False:
        return reply_msg("Fuck", tk, access_token)
    with open(f"preambles/{lineid}.tex", "r") as f:
        for count, line in enumerate(f):
            pass
    command = rf"""
sed -i ' ' '{count + 1}a\ 
\{msg}
' preambles/Ue81ff6c316b6ebe482264e577453b1da.tex
"""
    print(command)
    os.system(command)
    return show_preamble(lineid, tk, access_token)

def replace_preamble(lineid, msg, access_token, tk):
    regex = re.compile('\s+') 
    msg_split = regex.split(msg)
    if preamble_check(lineid) == False:
        return reply_msg("Fuck", tk, access_token)
    command = rf"sed -i '' 's/\{msg_split[0]}/\{msg_split[1]}/' preambles/Ue81ff6c316b6ebe482264e577453b1da.tex"
    print(command)
    os.system(command)
    return show_preamble(lineid, tk, access_token)

def delete_preamble(lineid, access_token, tk):
    os.system(f"rm preambles/{lineid}.tex")
    with connect_database() as connection:
        with connection.cursor() as c:
            c.execute(f"DELETE FROM linelatexpreamble VALUES('{lineid}')")
            connection.commit()
    return reply_msg("已刪除您的 Preamble", tk, access_token)

def run_latex(tk, msg, access_token, lineid):
    preamble = preamble_check(lineid)
    if not preamble:
        preamble = LaTeX_Preamble
    else:
        with open(f"preambles/{lineid}.tex", "r") as f:
            file = f.readlines()
            preamble = ""
            for i in file:
                preamble += i
    f = open("file.tex", "w")
    f.write(preamble)
    print(preamble)
    f.write("\n\\begin{document}\n")
    if msg[:4] == '.tex':
        f.write(msg[4:])
    else:
        f.write(msg)
    f.write("\n\\end{document}")
    f.close()
    os.system("xelatex --interaction=nonstopmode file.tex")
    os.system("pdftoppm -jpeg -r 1200 file.pdf file ")
    command = f"mv file-1.jpg ./image/{tk[:10]}.jpg"
    os.system(command)
    reply_image(tk[:10], tk, access_token)


def food(time):
    time_list= ["breakfirst", "lunch", "dinner"]
    url = "http://junyi.tw/"
    junyi = requests.get(url)
    web = BeautifulSoup(junyi.text,"html.parser")#處理網頁內容
    what = web.find("div", class_=f"views-field views-field-field-{time_list[time]}") #將標題提取出來
    what = what.find("div", class_="field-content").text
    return "今天的晚餐是：\n\n" + what

def nearest_weather(lot, lat): # 利用經緯度算出最近的測站
    msg = "出錯"
    try:
        nearest_distance = 10000
        code = os.getenv('GOV_AUTH')
        data = requests.get(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={code}&downloadType=WEB&format=JSON')
        jsondata = data.json()
        location = jsondata['cwbopendata']['location']
        position = {}
        nearest_distance = 10000
        for i in location:
            lat_change = (lat - float(i['lat'])) **2 # 利用畢氏定理 a^2 + b^2 = c^2 算出直線距離
            lot_change = (lot - float(i['lon'])) **2
            distance = (lat_change + lot_change) **0.5
            if distance < nearest_distance: # 如果已知的最短距離小於新計算出的數值，就更新最短距離
                nearest_distance = distance
                position = i
        data = requests.get(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={code}&downloadType=WEB&format=JSON')
        jsondata = data.json()
        location = jsondata['cwbopendata']['location']
        for i in location:
            lat_change = (lat - float(i['lat'])) **2 # 利用畢氏定理 a^2 + b^2 = c^2 算出直線距離
            lot_change = (lot - float(i['lon'])) **2
            distance = (lat_change + lot_change) **0.5
            if distance < nearest_distance: # 如果已知的最短距離小於新計算出的數值，就更新最短距離
                nearest_distance = distance
                position = i
        print(position['locationName'])
        print('a')
        temp = position['weatherElement'][3]['elementValue']['value']
        print(temp)
        humid = position['weatherElement'][4]['elementValue']['value']
        print(humid)
        msg = f"離您最近的測站是{position['locationName']}。\n\n目前觀測數據是：\n溫度：{temp}\n濕度：{humid}"
        return msg
    except:
        return msg

def forecast(address):
    area_list = {}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    msg = '找不到天氣預報資訊。'    # 預設回傳訊息
    try:
        code = 'CWB-C26ED602-B0F7-49E1-A71C-28D88906ACAD'
        url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={code}&downloadType=WEB&format=JSON'
        f_data = requests.get(url)   # 取得主要縣市預報資料
        f_data_json = f_data.json()  # json 格式化訊息內容
        location = f_data_json['cwbopendata']['dataset']['location']  # 取得縣市的預報內容
        for i in location:
            city = i['locationName']    # 縣市名稱
            wx8 = i['weatherElement'][0]['time'][0]['parameter']['parameterName']    # 天氣現象
            mint8 = i['weatherElement'][1]['time'][0]['parameter']['parameterName']  # 最低溫
            maxt8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']  # 最高溫
            ci8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']    # 舒適度
            pop8 = i['weatherElement'][2]['time'][0]['parameter']['parameterName']   # 降雨機率
            area_list[city] = f'未來 8 小時{wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %'  # 組合成回傳的訊息，存在以縣市名稱為 key 的字典檔裡
        for i in area_list:
            if i in address:        # 如果使用者的地址包含縣市名稱
                msg = area_list[i]  # 將 msg 換成對應的預報資訊
                # 將進一步的預報網址換成對應的預報網址
                url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/{json_api[i]}?Authorization={code}&elementName=WeatherDescription'
                f_data = requests.get(url)  # 取得主要縣市裡各個區域鄉鎮的氣象預報
                f_data_json = f_data.json() # json 格式化訊息內容
                location = f_data_json['records']['locations'][0]['location']    # 取得預報內容
                break
        for i in location:
            city = i['locationName']   # 取得縣市名稱
            wd = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']  # 綜合描述
            if city in address:           # 如果使用者的地址包含鄉鎮區域名稱
                msg = f'未來八小時天氣{wd}' # 將 msg 換成對應的預報資訊
                break
        return msg  # 回傳 msg
    except:
        return msg  # 如果取資料有發生錯誤，直接回傳 msg

def reply_image(number, rk, token):
    headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}    
    body = {
    'replyToken':rk,
    'messages':[{
          'type': 'image',
          'originalContentUrl': f'{base_url}/upload/{number}',
          'previewImageUrl': f'{base_url}/upload/{number}'
        }]
    }
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(body).encode('utf-8'))
    print(req.text)

def reply_msg(reply, tk, access_token):
    line_bot_api = LineBotApi(access_token)
    line_bot_api.reply_message(tk, TextSendMessage(reply))

def reply_flex_msg(tk, access_token, reply = FlexMessage):
    headers = {'Authorization':f'Bearer {access_token}','Content-Type':'application/json'}
    reply.update({'replyToken':tk})
    req = requests.request('POST', 'https://api.line.me/v2/bot/message/reply', headers=headers,data=json.dumps(reply).encode('utf-8'))



app = Flask(__name__)

@app.route('/upload/<path>', methods=['GET'])
def upload(path):
    with open(f"image/{path}.jpg", 'rb') as bites:
        return send_file(io.BytesIO(bites.read()),mimetype='image/jpg')

@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                    # 取得收到的訊息內容
    try:
        print(body)
        json_data = json.loads(body)                         # json 格式化訊息內容
        access_token = os.getenv('TEST_CHANNEL')
        secret = os.getenv('TEST_SECRET')
        handler = WebhookHandler(secret)                     # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']      # 加入回傳的 headers
        handler.handle(body, signature)                      # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']            # 取得回傳訊息的 Token
        lineid = json_data['events'][0]['source']['userId']
        try:
            type = json_data['events'][0]['message']['type']     # 取得 LINe 收到的訊息類型
        except:
            type = json_data['events'][0]['type']
        if type == 'location':
            x = json_data['events'][0]['message']['latitude']  # 取得經緯度
            y = json_data['events'][0]['message']['longitude']
            address = json_data['events'][0]['message']['address'].replace('台','臺')
            reply = nearest_weather(y,x) + "\n"
            reply += forecast(address)
            print(reply)
        elif type=='text':
            msg = json_data['events'][0]['message']['text']  # 取得 LINE 收到的文字訊息
            if msg[:2] == "均一":
                if msg[2:4] == "早餐":
                    reply = food(0)
                elif msg[2:4] == "午餐":
                    reply = food(1)
                elif msg[2:4] == "晚餐":
                    reply = food(2)
                else:
                    reply = "出錯"
                print(reply)
                reply_msg(reply, tk, access_token)
            else:
                check_msg(msg, tk, access_token, lineid)
        elif type == "postback":
            data = json_data['events'][0]['postback']['data']
            print(lineid)
            if data == "Yes":
                new_preamble(lineid, tk, access_token)
            else:
                reply_msg("Fuck", tk, access_token)
        else:
            print('No Reaction')
    except:
        print("Fuck")                                          # 如果發生錯誤，印出收到的內容
    return 'OK'                                              # 驗證 Webhook 使用，不能省略

if __name__ == "__main__":
    app.run(debug=True)