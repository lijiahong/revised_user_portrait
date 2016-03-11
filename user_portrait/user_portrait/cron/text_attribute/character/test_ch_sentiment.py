# -*- coding: UTF-8 -*-

import sys
import csv
import datetime
import time
from search import search_text_sentiment,search_text,search_profile
from global_utils_ch import COUNT_STA,re_cut,ZERO_STA,SEN_DICT,TOTAL_STA,abs_path
from triple_sentiment_classifier import triple_classifier
#from test_data import input_data2,input_data  

def sentiment_classify(uid_sentiment,start_date,end_date):
    '''
        冲动型+抑郁型的划分：根据用户发布文本的情绪进行划分
        输入数据：字典对象 {uid:{time1:[sentiment1,sentiment2,...],time2:[sentiment1,sentiment2,...]}...}
        2表示冲动型，1表示抑郁型，0表示未知
    '''
    uid_s = dict()
    for k,v in uid_sentiment.iteritems():
        impulse = 0
        depressed = 0
        for item in v:
            n = item[2]
            i_r = item[0]/float(n)
            d_r = item[1]/float(n)
            if abs(i_r-d_r) > ZERO_STA and (i_r+d_r) >= TOTAL_STA:
                if i_r > d_r:
                    impulse = impulse + 1
                else:
                    depressed = depressed + 1

        if impulse >= COUNT_STA and impulse > depressed:
            flag = 1
        elif depressed >= COUNT_STA and impulse < depressed:
            flag = 2
        else:
            flag = 0
        uid_s[k] = flag

    return uid_s       

def sta_time_list(min_ts,max_ts):#按照时间进行排序

    during = 24*3600
    max_ts = max_ts + during
    time_index = dict()
    time_list = []
    count = 0
    for ts in range(min_ts,max_ts,during):
        date_str = time.strftime('%Y-%m-%d',time.localtime(float(ts)))
        time_index[date_str] = count
        count = count + 1
        time_list.append([0,0,0])

    return time_index,time_list

def classify_without_sentiment(uid_weibo,uid_list,start_date,end_date):
    '''
      没有情感标签的分类主函数
      输入数据：list对象 [[uid,text,time],[uid,text,time],...]
      输出数据：字典对象 {uid1:str1,uid2:str2,...}
    '''

    uid_sentiment = dict()
    com_result = dict()
    min_ts = int(time.mktime(time.strptime(start_date,'%Y-%m-%d')))
    max_ts = int(time.mktime(time.strptime(end_date,'%Y-%m-%d')))
    time_index,time_list = sta_time_list(min_ts,max_ts)
    for uid,text,ts in uid_weibo:
        sentiment = triple_classifier({'text':text})
        date_str = time.strftime('%Y-%m-%d',time.localtime(float(ts)))
        if uid_sentiment.has_key(uid):
            item = uid_sentiment[uid]
            index = time_index[date_str]
            if sentiment == 2 or sentiment == 5:
                item[index][0] = item[index][0] + 1
            if sentiment == 3 or sentiment == 4:
                item[index][1] = item[index][1] + 1
            item[index][2] = item[index][2] + 1
            uid_sentiment[uid] = item
        else:
            item = time_list
            index = time_index[date_str]
            if sentiment == 2 or sentiment == 5:
                item[index][0] = item[index][0] + 1
            if sentiment == 3 or sentiment == 4:
                item[index][1] = item[index][1] + 1
            item[index][2] = item[index][2] + 1
            uid_sentiment[uid] = item

    s_result = sentiment_classify(uid_sentiment,min_ts,max_ts)

    com_result = dict()
    for uid in uid_list:
        if s_result.has_key(uid):
            com_result[uid] = SEN_DICT[s_result[uid]]
        else:
            com_result[uid] = SEN_DICT[0]

    return com_result

def classify_with_sentiment(uid_weibo,uid_list,start_date,end_date):
    '''
      有情感标签的分类主函数
      输入数据：list对象 [[uid,text,time],[uid,text,time],...]
      输出数据：字典对象 {uid1:str1,uid2:str2,...}
    '''
    uid_sentiment = dict()
    min_ts = int(time.mktime(time.strptime(start_date,'%Y-%m-%d')))
    max_ts = int(time.mktime(time.strptime(end_date,'%Y-%m-%d')))
    time_index,time_list = sta_time_list(min_ts,max_ts)
    for uid,text,s,ts in uid_weibo:
        sentiment = s
        date_str = time.strftime('%Y-%m-%d',time.localtime(float(ts)))
        if uid_sentiment.has_key(uid):
            item = uid_sentiment[uid]
            index = time_index[date_str]
            if sentiment == 2 or sentiment == 5:
                item[index][0] = item[index][0] + 1
            if sentiment == 3 or sentiment == 4:
                item[index][1] = item[index][1] + 1
            item[index][2] = item[index][2] + 1
            uid_sentiment[uid] = item
        else:
            item = time_list
            index = time_index[date_str]
            if sentiment == 2 or sentiment == 5:
                item[index][0] = item[index][0] + 1
            if sentiment == 3 or sentiment == 4:
                item[index][1] = item[index][1] + 1
            item[index][2] = item[index][2] + 1
            uid_sentiment[uid] = item

    s_result = sentiment_classify(uid_sentiment,min_ts,max_ts)

    com_result = dict()
    for uid in uid_list:
        if s_result.has_key(uid):
            com_result[uid] = SEN_DICT[s_result[uid]]
        else:
            com_result[uid] = SEN_DICT[0]

    return com_result

def classify_sentiment(uid_list,uid_weibo,start_date,end_date,flag):
    '''
        分类主函数：
        输入：用户id列表，微博列表，查询es的开始时间（字符串），查询es的结束时间（字符串），是否需要再计算情绪（int，1表示需要计算，0表示不需要计算）
        输入样例：
        示例1（需要计算情感）：[uid1,uid2,uid3,...],[[uid1,text1,ts1],[uid2,text2,ts2],...],'2013-09-01','2013-09-07',1
        示例0（不需要计算情感）：[uid1,uid2,uid3,...],[[uid1,text1,s1,ts1],[uid2,text2,s2,ts2],...],'2013-09-01','2013-09-07',0
    '''

    if flag == 1:#需要重新计算情绪
        com_result = classify_without_sentiment(uid_weibo,uid_list,start_date,end_date)
    else:#不需要重新计算情绪
        com_result = classify_with_sentiment(uid_weibo,uid_list,start_date,end_date)
        
    return com_result 

###以下函数仅供测试使用，目的是学习对应的参数
def get_sentiment(uid_weibo,name):#学习情绪有关的参数

    uid_sentiment = dict()
    uid_list = []
    min_ts = MIN_TS
    max_ts = MAX_TS
    for item in uid_weibo:
        uid = item[0]
        text = item[1]
        ts = item[2]
        if int(ts) <= min_ts:
            min_ts = int(ts)
        if int(ts) >= max_ts:
            max_ts = int(ts)
        if uid not in uid_list:
            uid_list.append(uid)
        sentiment = triple_classifier({'text':text})
        date_str = time.strftime('%Y-%m-%d',time.localtime(float(ts)))
        if uid_sentiment.has_key(uid):
            item = uid_sentiment[uid]
            if item.has_key(date_str):
                row = item[date_str]
                row.append(sentiment)
                item[date_str] = row
            else:
                row = []
                row.append(sentiment)
                item[date_str] = row
            uid_sentiment[uid] = item
        else:
            item = dict()
            row = []
            row.append(sentiment)
            item[date_str] = row
            uid_sentiment[uid] = item

    s_result = sentiment_classify(uid_sentiment,min_ts,max_ts)

    write_e_result(s_result,name)    

def write_result(result_dict,name):

    with open(abs_path + '/result0122/%s_data.csv' % name, 'wb') as f:
        writer = csv.writer(f)
        for k,v in result_dict.iteritems():
            writer.writerow((k,v))

def write_e_result(result_dict,name):

    with open(abs_path + '/result0122/%s_data.csv' % name, 'wb') as f:
        writer = csv.writer(f)
        for k,v in result_dict.iteritems():
            for k1,v1 in v.iteritems():
                writer.writerow((k,k1,v1[0],v1[1],v1[2]))   

if __name__ == '__main__':

    uid_list,uid_weibo = input_data2('test_0126')
    start = time.time()
    result_dict = classify_sentiment(uid_list,uid_weibo,'2013-09-01','2013-09-07',1)
    end = time.time()
    print 'it takes %s seconds...' % (end-start)

    with open('/home/ubuntu8/yuanshi/character/result0122/test_0226_data_new.csv', 'wb') as f:
        writer = csv.writer(f)
        for k,v in result_dict.iteritems():
            writer.writerow((k,v))
##    with open('/home/ubuntu8/yuanshi/character/result0122/count_0226_data.csv', 'wb') as f:
##        writer = csv.writer(f)
##        for k,v in uid_test.iteritems():
##            c = len(v['i_r'])
##            for i in range(0,c):
##                writer.writerow((k,v['i_r'][i],v['d_r'][i],v['n_r'][i]))
##    get_event(uid_weibo,'sta_in_event')
##    get_sentiment(uid_weibo,'sta_in_sentiment')
##    uid_weibo = input_data2('notin')
##    get_event(uid_weibo,'notin_event')
##    get_sentiment(uid_weibo,'notin_sentiment')
    






   
