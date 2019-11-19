import random
import os
import sys
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import unquote as decode
from flask import Flask, request
import requests
import feedparser
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from apscheduler.schedulers.blocking import BlockingScheduler 
import time,datetime

TELEGRAM_TOKEN = 'Need_to_replace'
chat_id = 'Need_to_replace'
firebase_key = {Need_to_replace}

cred = credentials.Certificate(firebase_key)
firebase_admin.initialize_app(cred)
db = firestore.client()
scheduler = BlockingScheduler()

def get_new_mess_data():
    params = {
        "access_token": 'EAAEuhWHb0DIBAC2BczFkmF0Jb3ZADB2dsgZA2Cch3kelRgZA4ZA7UOE182I5kg40Aj0PcdkaSGLtit7XAGZAVM5tuI9ofqLc98rI2nlLv2LaMY3TQxWzRaTEE73lEUZBJgGgKOkAdUdu2PFowsghrduA2zYl9G1FG6esrKEvy1mgZDZD'
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://new.ntpu.edu.tw/%E5%85%AC%E5%91%8A",
        "Origin": "https://new.ntpu.edu.tw",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
        "DNT": "1",
        "Sec-Fetch-Mode": "cors",
        "Content-type": "application/json; charset=UTF-8"
    }
    now_time = str(time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.localtime()))
    data_data  = "\n{\npublications(\nstart: 0,\nlimit: 20,\nsort: \"publishAt:desc,createdAt:desc\",\nwhere: {\nsitesApproved: \"www_ntpu\",\npublishAt_lte: \""
    data_data += now_time
    data_data += "\",\nunPublishAt_gte: \""
    data_data += now_time
    data_data += "\"\n}\n)\n{_id title tags contactPerson publishAt coverImage{url}}\n}"
    data = json.dumps({"query":data_data})
    try:
        r = requests.post("https://cms.carrier.ntpu.edu.tw/graphql", params=params, headers=headers, data=data)
        r.encoding = 'utf8'
        soup = BeautifulSoup(r.text, 'html.parser')
        logs_yellow('Get data!')
    except:
        print('\033[33m [' + get_nowtime() + '] ' + 'Error!' + ' \033[0m')
        logs_yellow('[Get data!] Fail')
        return 'no'
    else:
        logs_yellow('[Get data!] Success')
        return str(soup)

def data_processer(json_data):
    json_dict = json.loads(json_data)
    json_data = json_dict['data']['publications']

    final_post_time = read_final_post_time()

    for i in range(19,-1,-1):
        time_y  = json_data[i]['publishAt'][0:4]
        time_mo = json_data[i]['publishAt'][5:7]
        time_d  = json_data[i]['publishAt'][8:10]
        time_h  = json_data[i]['publishAt'][11:13]
        time_mi = json_data[i]['publishAt'][14:16]
        time_s  = json_data[i]['publishAt'][17:19] #23
        seconds = time.mktime(datetime.datetime(int(time_y),int(time_mo),int(time_d),int(time_h),int(time_mi),int(time_s)).timetuple()) #year, month, day, hour, minute, second
        print(seconds)
        if final_post_time < seconds:
            mess = '<b>' + json_data[i]['title'] + '</b>' + '\n<a>https://new.ntpu.edu.tw/公告/' + json_data[i]['_id'] + '</a>'
            send_mes(mess)
            registered_to_firebase(seconds)

def send_mes(mess):
    url = 'https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage?chat_id=@' + chat_id + '&text=' + mess + '&parse_mode=html'
    requests.get(url)
    print('send url:' + chat_id + '\n' + url + '\n')
    return 'ok'

def read_final_post_time():
    doc_ref = db.collection("ntpu_rss").document("final_post_time")
    doc = doc_ref.get().to_dict()
    print('\033[33m [' + get_nowtime() + '] ' + 'read_firebase_num:' + str(doc['end_time']) + ' \033[0m')
    return doc['end_time']

def registered_to_firebase(final_post_time):
    doc = {
        'end_time': int(final_post_time)
    }
    doc_ref = db.collection("ntpu_rss").document("final_post_time")
    doc_ref.update(doc)
    print('\033[33m [' + get_nowtime() + '] ' + 'write_firebase_num:'+ str(doc['end_time']) + ' \033[0m')
    return "success" 

def get_nowtime():
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

def logs_yellow(mess):
    print('\033[33m [' + get_nowtime() + '] ' + mess + ' \033[0m')
    return "success"

def logs_green(mess):
    print('\033[32m [' + get_nowtime() + '] ' + mess + ' \033[0m')
    return "success"

def a_mission():
    print('\033[32m [' + get_nowtime() + '] ' + 'mission start \033[0m')
    data_processer(get_new_mess_data())
    print('\033[35m [' + get_nowtime() + '] ' + 'mission end \033[0m')
    print('----------------------')

print('\033[32m [' + get_nowtime() + '] ' + 'start \033[0m')
scheduler.add_job(a_mission, 'interval', minutes=10, start_date='2019-11-19 15:00:00') 
scheduler.start()
