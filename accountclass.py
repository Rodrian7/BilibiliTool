#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import myapi
import time, json, requests
import random
import logging


logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("myapi")

class bilibili:
    def __init__(self, ID, Password, access_key, cookies, aid, a_type, finished, logined, watched, shared, coin_added,
                 double_watch, s2c, signed, last_like_dynamic):
        self.ID = ID
        self.Password = Password
        self.access_key = access_key
        self.cookie = json.loads(cookies.replace("'", '"'))
        self.aid = aid
        self.a_type = a_type
        self.finished = finished
        self.logined = logined
        self.watched = watched
        self.shared = shared
        self.coin_added = coin_added
        self.double_watch = double_watch
        self.s2c = s2c
        self.signed = signed
        self.last_like_dynamic = last_like_dynamic

    # 显示账号信息
    def show(self):
        logging.info("id=%s,Password=%s,access_key=%s,cookies=%s" % (self.ID, self.Password, self.access_key, self.cookie))

    # 检测今日任务是否已经完成
    def didfinished(self):
        if self.logined and self.watched and self.shared and self.coin_added and self.double_watch and self.s2c and self.signed:
            return 1
        else:
            return 0

    # 检测cookie是否有效
    def cookies_test(self):
        url = "https://api.bilibili.com/x/space/myinfo"
        response = requests.get(url, cookies=self.cookie)
        if json.loads(response.text)['code'] == 0:
            return True
        else:
            logging.info(response.text)
            return False

    # 检测token是否有效
    def token_test(self):
        url = "https://passport.bilibili.com/api/v3/oauth2/info?"
        item = {'access_key': self.access_key,
                'appkey': myapi.APP_KEY,
                'ts': int(time.time())}
        item['sign'] = myapi.get_sign(item)
        test_page = json.loads(requests.get(url, params=item).text)
        if test_page['code'] == 0:
            return True
        else:
            logging.info(test_page)
            return False

    # 观看av号为aid的视频
    def watch(self, aid):
        url = "https://api.bilibili.com/x/web-interface/view?aid=%s" % aid
        response = json.loads(requests.get(url).text)
        if response['code'] == 0:
            cid = response['data']['cid']
            duration = response['data']['duration']
        else:
            logging.info("av%s信息解析失败" % aid)
            return False
        url = "https://api.bilibili.com/x/report/click/now?jsonp=jsonp"
        response = json.loads(requests.get(url).text)
        if response['code'] == 0:
            start_ts = response['data']['now']
            url = "https://api.bilibili.com/x/report/web/heartbeat"
            data = {'aid': aid,
                    'cid': cid,
                    'mid': self.cookie['DedeUserID'],
                    'csrf': self.cookie['bili_jct'],
                    'played_time': 1,
                    'realtime': 1,
                    'play_type': 2,
                    'start_ts': start_ts,
                    'type': 3,
                    'dt': 7}
            response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
            if response['code'] == 0:
                logging.info("av%s观看成功" % aid)
                return True
        logging.info("av%s观看失败 %s" % (aid, response))
        return False

    # 点赞某条动态
    def thumb(self, did):
        url = "https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb"
        data = {'uid': self.cookie['DedeUserID'],
                'dynamic_id': did,
                'up': 1,
                'csrf_token': self.cookie['bili_jct']}
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        if response['code'] == 0:
            logging.info("动态%s点赞成功" % did)
            return True
        else:
            logging.info("动态%s点赞失败 %s" % (did, response))
            return False

    # 直播区签到
    def sign(self):
        response = json.loads(requests.get("https://api.live.bilibili.com/sign/doSign", cookies=self.cookie).text)
        if response['code'] == 0:
            return True
        else:
            logging.info("签到失败 %s" % (response))
            return False

    # 评论某视频
    def comment(self, aid, content):
        url = "https://api.bilibili.com/x/v2/reply/add"
        data = {'oid': aid,
                'type': 1,
                'message': content,
                'plat': 1,
                'jsonp': 'jsonp',
                'csrf': self.cookie['bili_jct']}
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        if response['code'] == 0:
            logging.info("av%s评论成功" % aid)
            return True
        else:
            logging.info("av%s评论失败 %s" % (aid, response))
            return False

    # 分享某视频
    def share(self, aid):
        url = "https://api.bilibili.com/x/web-interface/share/add"
        data = {'aid': aid,
                'jsonp': "jsonp",
                'csrf': self.cookie['bili_jct']}
        headers = {
            'Host': "api.bilibili.com",
            'Origin': "https://www.bilibili.com",
            'Referer': "https://www.bilibili.com/video/av%s" % aid
        }
        response = json.loads(requests.post(url, data=data, headers=headers, cookies=self.cookie).text)
        if response['code'] == 0:
            return True
        else:
            logging.info("av%s分享失败 %s" % (aid, response))
            return False

    # 得到领取硬币的情况
    def get_coin_info(self):
        sign_page = json.loads(
            requests.get("https://api.bilibili.com/x/member/web/coin/log?jsonp=jsonp", cookies=self.cookie).text)
        if sign_page['data']['list']:
            for info in sign_page['data']['list']:
                if info['reason'] == u"登录奖励" and info['time'][:10] == time.strftime("%Y-%m-%d", time.localtime()):
                    # logging.info() "今日已领硬币"
                    return True
            return False
        else:
            return False

    # 得到换取硬币的情况
    def get_giftinfo(self):
        sign_page = json.loads(
            requests.get("https://api.bilibili.com/x/member/web/coin/log?jsonp=jsonp", cookies=self.cookie).text)
        if sign_page['data']['list']:
            for info in sign_page['data']['list']:
                if info['reason'] == u"礼品兑换" and info['time'][:10] == time.strftime("%Y-%m-%d", time.localtime()):
                    logging.info("今日已换硬币")
                    return True
            return False
        else:
            return False

    # 检测直播签到情况
    def get_sign_info(self):
        sign_page = json.loads(requests.get("https://api.live.bilibili.com/sign/GetSignInfo", cookies=self.cookie).text)
        if sign_page['data']['status'] == 0:
            # logging.info() "今日直播还未签到"
            return False
        else:
            # logging.info() "今日直播已经签到"
            return True

    # 转发动态
    def dynamic_repost(self, did, message):
        url = "https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost"
        data = {'uid': self.cookie['DedeUserID'],
                'dynamic_id': did,
                'content': message,
                'at_uids': None,
                'ctrl': "[]",
                'csrf_token': self.cookie['bili_jct']}
        headers = {'Content-Type': "application/x-www-form-urlencoded",
                   'Cookie': str(self.cookie),
                   'Host': "api.vc.bilibili.com",
                   'Origin': "https://space.bilibili.com"}
        response = json.loads(requests.post(url, data=data, headers=headers).text)
        if response['code'] == 0:
            logging.info("转发成功")
            return True
        else:
            logging.info("转发失败")
            return False

    # 给某视频投币
    def coin_add(self, aid):
        prompt_data = {
            'aid': str(aid),
            'multiply': '1',
            'cross_domain': 'true',
            'csrf': self.cookie['bili_jct']}
        headers = {
            "Host": "api.bilibili.com",
            "Cache-Control": "no-cache",
            "Proxy-Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://www.bilibili.com",
            "Referer": "https://www.bilibili.com/video/av" + str(aid),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"}
        response = json.loads(
            requests.post("https://api.bilibili.com/x/web-interface/coin/add", data=prompt_data, headers=headers,
                          cookies=self.cookie).text)
        if response['code'] == 0:
            logging.info("投币成功")
            return True
        else:
            logging.info("投币失败 %s" % response['message'])
            return False

    # 得到应比数量
    def coin_num(self):
        sign_page = json.loads(requests.get("https://account.bilibili.com/site/getCoin", cookies=self.cookie).text)
        if sign_page['data']['money']:
            return sign_page['data']['money']
        else:
            return 0

    # 银瓜子兑换硬币
    def silver2coins(self):
        url = "https://api.live.bilibili.com/pay/v1/Exchange/silver2coin"
        data = {'platform': "pc",
                'csrf_token': self.cookie['bili_jct']}
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        if response['code'] == 0:
            logging.info("银瓜子兑换成功")
            return True
        else:
            logging.info("银瓜子兑换失败 %s" % (response['message'].encode("utf-8")))
            return False

    # 检测观看任务
    def get_watch_info(self):
        url = "https://account.bilibili.com/home/reward"
        sign_page = json.loads(requests.get(url, cookies=self.cookie).text)
        return sign_page['data']['watch_av']

    # 网页端直播心跳
    def heart_web(self, room_id):
        data = {'room_id': room_id,
                'csrf_token': self.cookie['bili_jct']}
        data['sign'] = myapi.get_sign(data)
        url = "https://api.live.bilibili.com/User/userOnlineHeart"
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        if response['code'] == 0:
            logging.info("[" + time.asctime(time.localtime(time.time())) + "]\tHeart_web")
        else:
            logging.info("[" + time.asctime(time.localtime(time.time())) + "]\tHeart_web Error!!!")

    # 手机端直播心跳
    def heart_mobile(self, room_id):
        url = "https://api.live.bilibili.com/mobile/userOnlineHeart"
        data = {'room_id': room_id,
                'csrf_token': self.cookie['bili_jct']}
        data['sign'] = myapi.get_sign(data)
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        if response['code'] == 0:
            logging.info("[" + time.asctime(time.localtime(time.time())) + "]\tHeart_mobile")
        else:
            logging.info("[" + time.asctime(time.localtime(time.time())) + "]\tHeart_mobile Error!!!")

    # 检测直播区任务
    def taskinfo_get(self):
        url = "https://api.live.bilibili.com/i/api/taskInfo"
        response = json.loads(requests.get(url, cookies=self.cookie).text)
        if response['data']['double_watch_info']['mobile_watch'] == 1 and response['data']['double_watch_info'][
            'web_watch'] == 1:
            return True
        else:
            return False

    # 领取双端观看奖励
    def receive_double(self):
        url = "https://api.live.bilibili.com/activity/v1/task/receive_award"
        data = {'task_id': "double_watch_task",
                'csrf_token': self.cookie['bili_jct']}
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        logging.info(response['message'])

    # 获取投币任务情况
    def get_coin_add_num(self):
        url = "https://account.bilibili.com/home/reward"
        sign_page = json.loads(requests.get(url, cookies=self.cookie).text)
        return sign_page['data']['coins_av']

    # 获取登录任务情况
    def get_login_info(self):
        url = "https://account.bilibili.com/home/reward"
        sign_page = json.loads(requests.get(url, cookies=self.cookie).text)
        return sign_page['data']['login']

    # 获取分享任务情况
    def get_share_info(self):
        url = "https://account.bilibili.com/home/reward"
        sign_page = json.loads(requests.get(url, cookies=self.cookie).text)
        return sign_page['data']['share_av']

    # 获取当前等级
    def get_current_level(self):
        url = "https://account.bilibili.com/home/reward"
        sign_page = json.loads(requests.get(url, cookies=self.cookie).text)
        return sign_page['data']['level_info']['current_level']

    # 获取up的粉丝数
    def get_up_followers(self, uid):
        url = "https://api.bilibili.com/x/relation/followers?vmid=" + str(uid)
        followers_page = json.loads(requests.get(url).text)
        logging.info(followers_page['data']['total'])
        return followers_page['data']['total']

    # 点赞并且如果是视频投稿抢前排评论
    def thumb_and_comment_new(self):
        url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid=" + self.cookie[
            'DedeUserID'] + '&type=268435455'
        dynamic_page = json.loads(requests.get(url, cookies=self.cookie).text)
        if self.last_like_dynamic == 0:
            self.last_like_dynamic = dynamic_page['data']['cards'][0]['desc']['timestamp']
            return
        for card in reversed(dynamic_page['data']['cards']):
            if card['desc']['timestamp'] > self.last_like_dynamic and card['desc'].has_key('user_profile'):
                if ('\"aid\"' in card['card'] and self.get_up_followers(
                        card['desc']['user_profile']['info']['uid']) > 100000 and random.random() > 0.7):
                    self.comment(json.loads(card['card'])['aid'], u"前排")
                self.thumb(card['desc']['dynamic_id'])
                self.last_like_dynamic = card['desc']['timestamp']

    def vip_privilege_1(self):
        url = "https://api.bilibili.com/x/vip/privilege/receive"
        data = {'type': 1,
                'csrf': self.cookie['bili_jct']}
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        logging.info(response['message'])

    def vip_privilege_2(self):
        url = "https://api.bilibili.com/x/vip/privilege/receive"
        data = {'type': 2,
                'csrf': self.cookie['bili_jct']}
        response = json.loads(requests.post(url, data=data, cookies=self.cookie).text)
        logging.info(response['message'])
