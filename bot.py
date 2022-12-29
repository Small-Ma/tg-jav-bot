import telebot
from telebot import types, apihelper
import requests
import cfg
import json
import os
import sys
import re
import util_tg_sender

TG_CHAT_ID = cfg.TG_CHAT_ID
TG_BOT_TOKEN = cfg.TG_BOT_TOKEN
SERVER_URL = cfg.SERVER_URL

PROXY_ADDR = f'{cfg.PROXY_SCHEME}://{cfg.PROXY_ADDR_HOST}:{cfg.PROXY_ADDR_PORT}'
if cfg.USE_PROXY:
    apihelper.proxy = {'http': PROXY_ADDR, 'https': PROXY_ADDR}

bot = telebot.TeleBot(TG_BOT_TOKEN)

def get_nice_magnets(magnets:list, prop:str) -> list:
    '''过滤磁链列表

    :param list magnets: 要过滤的磁链列表
    :param str prop: 过滤属性 (属性值为 True 或 False)
    :return list: 过滤后的磁链列表
    '''
    if len(magnets) == 0: return []
    if len(magnets) == 1: return magnets
    
    magnets_nice = []
    for magnet in magnets:
        if magnet[prop]:
            magnets_nice.append(magnet)
    if len(magnets_nice) == 0:
        return magnets
    return magnets_nice

def get_record(classify_by:str=''):
    '''发送查询记录
    
    :param str classify_by: 分类字段, 演员: 'stars', 番号：'id', defaults to None
    '''
    avs = []
    if os.path.exists(PATH_RECORD_FILE):
        with open(PATH_RECORD_FILE, 'r') as f:
            record = json.load(f)
        avs = record['avs']
        if classify_by != '':
            avs.sort(key=lambda i : i[classify_by])
    else:
        bot.send_message(chat_id=TG_CHAT_ID, text='尚无记录 =_=')
        return
    msg = ''
    i = 1
    for av in avs:
        if classify_by == 'stars':
            msg += f'''{av["stars"]}  <a href="https://javbus.com/{av["id"]}">{av["id"]}</a>
'''
        else:
            msg += f'''<a href="https://javbus.com/{av["id"]}">{av["id"]}</a>  {av["stars"]}
'''
        i += 1
        if i == 30:
            bot.send_message(chat_id=TG_CHAT_ID, text=msg, disable_web_page_preview=True, parse_mode='HTML')
            msg = ''
    if msg != '':
        bot.send_message(chat_id=TG_CHAT_ID, text=msg, disable_web_page_preview=True, parse_mode='HTML')

def get_record_json():
    '''发送查询记录文件
    '''
    if os.path.exists(PATH_RECORD_FILE):
        bot.send_document(chat_id=TG_CHAT_ID, document=types.InputFile(PATH_RECORD_FILE))
    else:
        bot.send_message(chat_id=TG_CHAT_ID, text='尚无记录 =_=')

def record(id:str, stars:str):
    '''记录查询信息

    :param str id: 番号
    :param str stars: 演员
    '''
    avs = []
    new_av = {'id': id, 'stars': stars}
    if os.path.exists(PATH_RECORD_FILE):
        with open(PATH_RECORD_FILE, 'r') as f:
            record = json.load(f)
        avs = record['avs']
    exists = False
    for av in avs:
        if av['id'].lower() == id.lower():
            exists = True
            break
    if not exists:
        avs.append(new_av)
        record = {'avs': avs}
        with open(PATH_RECORD_FILE, 'w') as f:
            json.dump(record, f, separators=(',', ': '), indent=4, ensure_ascii=False)  

def get_av_by_id(id:str):
    '''根据番号获取 av
    
    :param str id: 番号
    '''
    resp = requests.get(SERVER_URL + id)
    if resp.status_code != 200:
        bot.send_message(chat_id=TG_CHAT_ID, text=f'妹查找到该番号：{id} Q_Q')
        return
    id = resp.json()['id']
    title = resp.json()['title']
    img = resp.json()['img']
    stars = resp.json()['stars']
    magnets = resp.json()['magnets']
    magnets = get_nice_magnets(magnets, 'isHD')
    magnets = get_nice_magnets(magnets, 'hasSubtitle')
    if len(magnets) > 3: magnets = magnets[0:3]
    stars_msg = ''
    for star in stars:
        stars_msg += f'{star["starName"]}  '
    stars_msg = stars_msg.strip()
    if stars_msg.strip() == '':
        stars_msg = 'unknown'
    url = f'https://www.javbus.com/{id}'
    msg = f'''<a href="{url}"><b>{title}</b></a>
Stars: {stars_msg}'''
    bot.send_photo(chat_id=TG_CHAT_ID, photo=img, caption=msg, parse_mode='HTML')
    for i, magnet in enumerate(magnets):
        if i == 0: 
            util_tg_sender.send_msg('@PikPak6_Bot', magnet)
            bot.send_message('已经筛选出的最佳磁链发送到@PikPak6_Bot ^-^')
        else:
            bot.send_message(chat_id=TG_CHAT_ID, text=f'<code>{magnet["link"]}</code>     {magnet["size"]}', parse_mode='HTML')
    if len(magnets) == 0:
        bot.send_message(chat_id=TG_CHAT_ID, text='妹找到磁链 Q_Q')
    record(id=id, stars=stars_msg)

def get_av(text):
    '''解析消息获得番号列表，遍历番号列表, 依次查询 av

    :param text 消息
    '''
    ids = re.compile(r"[a-zA-Z]+-\d+").findall(text)
    if not ids:
        bot.send_message(chat_id=TG_CHAT_ID, text='你滴消息不存在番号捏 =_=')
        return
    for i in range(0, len(ids)):
        ids[i] = ids[i].lower().strip()
    ids = list(set(ids))
    for id in ids:
        get_av_by_id(id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    '''处理文本消息

    :param _type_ message: 消息
    '''
    if str(message.from_user.id) != TG_CHAT_ID:
        bot.send_message(chat_id=message.from_user.id, text='该机器人仅供私人使用哦, 如需使用请自行部署, \
项目地址：https://github.com/akynazh/tg-javbus-bot')
        return
    my_msg = message.text.strip()
    if my_msg == '/record':
        get_record()
    elif my_msg == '/record_id':
        get_record('id')
    elif my_msg == '/record_stars':
        get_record('stars')
    elif my_msg == '/record_json':
        get_record_json()
    else:
        get_av(my_msg)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    '''处理图像消息

    :param _type_ message: 消息
    '''
    if message.caption:
        get_av(message.caption)
    
@bot.message_handler(content_types=['video'])
def handle_video(message):
    '''处理视频消息

    :param _type_ message: 消息
    '''
    if message.caption:
        get_av(message.caption)

def set_command():
    '''设置机器人命令
    '''
    tg_cmd_dict = {
        'record': '获取查询记录（默认根据查询时间排序）',
        'record_id': '获取查询记录，根据番号名称排序',
        'record_stars': '获取查询记录，根据演员名称排序',
        'record_json': '发送查询记录文件'
    }
    cmds = []
    for cmd in tg_cmd_dict:
        cmds.append(types.BotCommand(cmd, tg_cmd_dict[cmd]))
    bot.set_my_commands(cmds)
    
if __name__ == '__main__':
    PATH_ROOT = sys.path[0]
    PATH_RECORD_FILE = PATH_ROOT + '/record.json'
    os.chdir(PATH_ROOT)
    set_command()
    bot.infinity_polling()