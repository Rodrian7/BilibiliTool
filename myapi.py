#!/usr/bin/python
# coding=utf-8
import json
import time
from base64 import b64encode
from hashlib import md5
from urllib.parse import urlencode
import logging

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

APP_KEY = '1d8b6e7d45233436'
APP_SECRET = '560c52ccd288fed045859ed18bffd973'

logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("myapi")


def get_sign(params):
    items = list(params.items())
    items.sort()
    return md5(str.encode(urlencode(items) + APP_SECRET)).hexdigest()


def get_access_key(userid, password):
    headers = {
        'User-Agent': 'Mozilla/5.0 BiliDroid/5.51.1 (bbcallen@gmail.com)'
    }
    base_url = "https://passport.bilibili.com/api/v3/oauth2/login?"
    url = 'http://passport.bilibili.com/login?act=getkey'
    get_key_res = requests.get(url)
    token = json.loads(get_key_res.content.decode('utf-8'))
    key = token['key'].encode('ascii')
    _hash = token['hash'].encode('ascii')
    key = RSA.importKey(key)
    cipher = PKCS1_v1_5.new(key)
    password = b64encode(cipher.encrypt(str.encode(_hash.decode() + password)))
    item = {'appkey': APP_KEY,
            'password': password,
            'username': userid}
    item['sign'] = get_sign(item)
    page_temp = json.loads(requests.post(base_url, data=item,headers=headers).text)
    if page_temp['code'] != 0:
        logging.info(page_temp)
        logging.info(page_temp['data'])
        return '-1'
    access_key = page_temp["data"]['token_info']['access_token']
    return access_key


def get_cookies(access_key):
    session = requests.Session()
    url = "http://passport.bilibili.com/api/login/sso?"
    item = {'access_key': access_key,
            'appkey': APP_KEY,
            'gourl': 'https://account.bilibili.com/account/home',
            'ts': str(int(time.time()))}
    item['sign'] = get_sign(item)
    session.get(url, params=item)
    return session.cookies.get_dict()
