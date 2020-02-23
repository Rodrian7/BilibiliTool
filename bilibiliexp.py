#!/usr/bin/env python
# coding=utf-8

import random
import re
import logging
import traceback
import time

import json
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import myapi
from accountclass import bilibili

import sqlite3

db_file = "bilibili.db"
scheduler = BlockingScheduler()


def create_table():
    with sqlite3.connect(db_file) as db:
        c = db.cursor()
        sql = """CREATE TABLE Account (
                ID CHAR(50) NOT null,
                Password CHAR(50) NOT null,
                Access_Key CHAR(50),
                Cookies TEXT,
                coinnum INT,
                aid CHAR(50),
                a_type INT,
                finished INT,
                logined INT,
                watched INT,
                shared INT,
                coin_added INT,
                double_watch INT,
                s2c INT,
                signed INT,
                current_level INT,
                last_like_dynamic INT)"""
        c.execute(sql)


def insertdb(ID, Password, a_type):
    with sqlite3.connect(db_file) as db:
        cursor = db.cursor()
        access_key = myapi.get_access_key(ID, Password)
        cookies = myapi.get_cookies(access_key)
        if access_key == '-1':
            logging.info('密码错误')
            return
        if a_type != 4:
            sql = """INSERT INTO Account
             VALUES ("%s", "%s","%s","%s",0,"3770834",%d,0,0,0,0,0,0,0,0,0,0)""" % (
                ID, Password, access_key, cookies, a_type)
        else:
            sql = """INSERT INTO Account
             VALUES ("%s", "%s","%s","%s",0,"3770834",%d,0,0,0,0,1,1,1,0,0,0)""" % (
                ID, Password, access_key, cookies, a_type)

        try:
            cursor.execute(sql)
            logging.info("%s 插入成功" % ID)
            db.commit()
        except:
            logging.info('插入数据失败!')
            logging.info(sql)
            db.rollback()


def querydball(finish=True):
    with sqlite3.connect(db_file) as db:
        cursor = db.cursor()
        id_list = []

        if finish:
            sql = "SELECT * FROM Account WHERE finished = 0"
        else:
            sql = "SELECT * FROM Account"
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                ID = row[0]
                id_list.append(ID)
        except:
            logging.info("Error: unable to fecth data")
        return id_list


def delete_db(ID):
    with sqlite3.connect(db_file) as db:
        cursor = db.cursor()

        sql = "DELETE FROM Account WHERE ID = '%s'" % ID

        try:
            cursor.execute(sql)
            db.commit()
        except:
            logging.info('删除数据失败!')
            db.rollback()


def delete_all_in_db():
    with sqlite3.connect(db_file) as db:
        cursor = db.cursor()

        sql = "DELETE FROM Account"

        try:
            cursor.execute(sql)
            db.commit()
        except:
            logging.info('删除数据失败!')
            db.rollback()


def everyday_set():
    with sqlite3.connect(db_file) as db:
        cursor = db.cursor()
        sql = "UPDATE Account SET finished = 0,logined = 0,watched = 0,shared = 0,coin_added = 0,double_watch = 0,s2c = 0,signed = 0"
        try:
            cursor.execute(sql)
            db.commit()
            logging.info('更新数据成功')
        except:
            logging.info('更新数据失败!')
            db.rollback()
        sql = "UPDATE Account SET double_watch = 1,s2c = 1,coin_added = 1 WHERE a_type=4"
        try:
            cursor.execute(sql)
            db.commit()
            logging.info('更新数据成功')
        except:
            logging.info('更新数据失败!')
            db.rollback()


def flush_db(bilibili_temp):
    with sqlite3.connect(db_file) as db:
        key_temp = myapi.get_access_key(bilibili_temp.ID, bilibili_temp.Password)
        cookies_temp = str(myapi.get_cookies(key_temp))
        cursor = db.cursor()
        sql = "UPDATE Account SET access_key = '%s' , cookies = \"%s\" WHERE ID = '%s'" % (
            key_temp, cookies_temp, bilibili_temp.ID)
        try:
            cursor.execute(sql)
            db.commit()
        except:
            logging.info('更新数据失败!')
            db.rollback()
    return key_temp, json.loads(cookies_temp.replace("'", '"'))


def query_db(id):
    with sqlite3.connect(db_file) as db:
        c = db.cursor()
        sql = "SELECT * FROM Account WHERE ID = %s" % id
        result = c.execute(sql).fetchone()
        bilibili_temp = bilibili(result[0], result[1], result[2], result[3], result[5], result[6], result[7], result[8],
                                 result[9], result[10], result[11], result[12], result[13], result[14], result[16])
        if not bilibili_temp.cookies_test():
            logging.info("%s cookies需重新获取" % id)
            bilibili_temp.access_key, bilibili_temp.cookie = flush_db(bilibili_temp)
        if not bilibili_temp.token_test():
            logging.info("%s token需重新获取" % id)
            bilibili_temp.access_key, bilibili_temp.cookie = flush_db(bilibili_temp)
    return bilibili_temp


def back2db(bilibili_temp):
    with sqlite3.connect(db_file) as db:
        cursor = db.cursor()
        sql = "UPDATE Account SET finished = %r,logined = %r,watched = %r,shared = %r,coin_added = %r,double_watch = %r,s2c = %r,signed = %r,current_level = %d,last_like_dynamic = %d WHERE ID='%s'" % (
            bilibili_temp.didfinished(), bilibili_temp.logined, bilibili_temp.watched, bilibili_temp.shared,
            bilibili_temp.coin_added, bilibili_temp.double_watch, bilibili_temp.s2c, bilibili_temp.signed,
            bilibili_temp.get_current_level(), bilibili_temp.last_like_dynamic, bilibili_temp.ID,)
        try:
            cursor.execute(str(sql))
            db.commit()
        except:
            logging.info('更新数据失败!')
            logging.info(sql)
            db.rollback()



def task_begin():
    with sqlite3.connect(db_file) as db:
        id_list = querydball(db)
        avlist = get_avlist()
        logging.info(avlist)
        # for id in id_list:
        for id in id_list:
            bilibili_temp = query_db(str(id))
            bilibili_temp.vip_privilege_1()   #领取会员权益(B币)
            bilibili_temp.vip_privilege_2()  # 领取会员权益(会员购)
            logging.info(bilibili_temp.coin_num())
            if not bilibili_temp.double_watch:  # 非三无小号
                if bilibili_temp.taskinfo_get():  # 双端任务
                    bilibili_temp.double_watch = 1
                    bilibili_temp.receive_double()

            if not bilibili_temp.logined:
                bilibili_temp.access_key, bilibili_temp.cookie = flush_db(bilibili_temp)
                if not bilibili_temp.get_login_info():  #
                    bilibili_temp.access_key, bilibili_temp.cookie = flush_db(bilibili_temp)
                else:
                    bilibili_temp.logined = 1

            if not bilibili_temp.signed:
                if not bilibili_temp.get_sign_info():  # 直播签到
                    bilibili_temp.sign()
                else:
                    bilibili_temp.signed = 1

#            if not bilibili_temp.watched:
#                if not bilibili_temp.get_watch_info():  # 每日观看视频任务
#                    bilibili_temp.watch(avlist[0])
#                else:
#                    bilibili_temp.watched = 1

            if not bilibili_temp.shared:
                if not bilibili_temp.get_share_info():  # 每日分享视频任务
                    bilibili_temp.share(avlist[0])
                else:
                    bilibili_temp.shared = 1

            if not bilibili_temp.s2c:
                if not bilibili_temp.get_giftinfo():  # 是否已做每日兑换
                    bilibili_temp.silver2coins()
                else:
                    bilibili_temp.s2c = 1

            if not bilibili_temp.coin_added:
                if bilibili_temp.a_type in [0, 2]:
                    for av_temp in avlist[bilibili_temp.get_coin_add_num() // 10:]:
                        if bilibili_temp.coin_num() < 1:
                            break
                        bilibili_temp.watch(av_temp)        # 观看对应视频
                        time.sleep(random.randint(60, 180))   # 延时60~180s后投币
                        bilibili_temp.coin_add(av_temp)

                    if bilibili_temp.get_coin_add_num() == 50 or (
                            bilibili_temp.s2c == 1 and bilibili_temp.coin_num() < 1):
                        bilibili_temp.coin_added = 1

            back2db(bilibili_temp)
            logging.info('------------------')


def dynamic_task():
    id_list = querydball(False)
    for id in id_list:
        bilibili_dynamic = query_db(id)
        bilibili_dynamic.thumb_and_comment_new()
        back2db(bilibili_dynamic)


def heart_beat():
    id_list = querydball(False)
    for id in id_list:
        bilibili_dynamic = query_db(id)
        bilibili_dynamic.heart_web('6') # lol直播间
        bilibili_dynamic.heart_mobile('21469968')   # 朱一旦直播间
        # bilibili_dynamic.watch('53498875')


def get_avlist():
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'https://www.bilibili.com/'
    }
    guichu_page = requests.get('https://www.bilibili.com/ranking/all/155/1/1', headers=headers).text
    avlist_tmp = re.findall('/av(.*?)\"', guichu_page)
    random.shuffle(avlist_tmp)
    return avlist_tmp[:5]

def spider_schedule():
    scheduler.remove_job('spider_schedule')

    try:
        logging.info('spider start...', datetime.now().strftime('%Y-%m-%d %X'))
        # my job code
        heart_beat()
        interval_seconds = random.randint(360, 400)
        logging.info('双端观看直播中..., 时长', interval_seconds)
        time.sleep(interval_seconds)
        task_begin()
        logging.info('spider end...', datetime.now().strftime('%Y-%m-%d %X'))

    except Exception as e:
        logging.info(traceback.format_exc(e))
    finally:
        interval_hours = random.randint(3, 5)
        interval_minutes = random.randint(1, 60)
        logging.info('下次运行任务时间为', interval_hours, 'h', interval_minutes, 'm后')
        scheduler.add_job(spider_schedule, 'interval', hours=interval_hours,
                minutes=interval_minutes, id='spider_schedule')




def main():
    # create_table() #建立表
    # insertdb('账号17367****', '密码****', 2)  # 向数据库中插入账号 2为实名制
    everyday_set()
    task_begin()
    heart_beat()
    logging.basicConfig()
    scheduler.add_job(everyday_set, 'cron', hour=0, minute=1)
    scheduler.add_job(heart_beat, 'cron', minute='*/5')
    scheduler.add_job(spider_schedule, 'interval', seconds=1, id='spider_schedule')
    scheduler.start()


if __name__ == '__main__':
    main()
