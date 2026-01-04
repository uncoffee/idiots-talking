#dbに接続しないと死ぬ。

#check_uuid(cursor) : cookieでユーザ認証を行い、ユーザのidと名前を返す。
# 何もなければ、Falseを返す。

#user_relations(cursor , user_id) : フレンド一覧と、フレンド申請一覧を返す。
# 何もなければ、Noneを返す。

#user_chatlogs(cursor , user_id , friend_id) : chatlogsテーブルから、会話の履歴を取ってくる。logidとchatlogとtimelogとsenderが返ってくる。
# その人が送っている文章はsender=Trueそうでなければ,sender=False。
# 何もなければNoneが返ってくる。

#getinfo(curosor , user_id) : informationsテーブルから、ユーザの名前を取ってくる。
# 無ければNoneを返す。

#getcursor("dbの名前") : データベースに接続してcursorを返す。名前がなければしらん。
# ※dbの名前はstr型で書いてね。

#closecursor() : コミットをして、cursorとデータベースを閉じる。

import pymysql  
import uuid

from flask import Flask, make_response , render_template,request , redirect, url_for

def use_db(func):
    def wakaran(*args , **keyword):
        connection = pymysql.connect(
        host="localhost", #わからん
        db="myapp", #使ってるデータベースの名前
        user="root", #わからん
        password="", #パスワードは無し
        charset="utf8", #文字コード指定
        cursorclass=pymysql.cursors.DictCursor #dict型(辞書型)に型を変更している　これによってhtml上でのデータの取り出しが楽になる。らしい
        )

        cursor = connection.cursor()

        yokuwakaran = func(cursor , *args , **keyword)

        connection.commit()
        cursor.close()
        connection.close()
        
        return yokuwakaran
    
    wakaran.__name__ = func.__name__

    return wakaran

def check_uuid(func):
    def wakaran(cursor , *args , **keyword):
        user_uuid = request.cookies.get("uuid")

        sql = "SELECT user_id FROM uuids WHERE uuid = %(user_uuid)s;"
        result = cursor.execute(sql, {"user_uuid" : user_uuid})
        
        if result == 1:
            user_id = cursor.fetchone()
            user_id = user_id["user_id"]

            sql = "SELECT * FROM informations WHERE user_id = %(user_id)s;"
            cursor.execute(sql, {"user_id" : user_id})
            user_data = cursor.fetchone()

            return func(cursor , user_data , *args , **keyword)

        else:
            return redirect("/" , code=302)
    
    wakaran.__name__ = func.__name__

    return wakaran

        
def check_none(*args):
    count = 0
    for i in args:
        count += 1
        if i == None:
            print(f"{count}番目の変数がNoneです。")
            return True
    
    return False


def user_relations(cursor , user_id):
    sql = "SELECT friend_id FROM relations WHERE user_id = %s;"
    cursor.execute(sql , user_id)
    my_relation = cursor.fetchall()
    
    sql = "SELECT user_id FROM relations WHERE friend_id = %s;" 
    request_check = cursor.execute(sql , user_id)
    others_relation = cursor.fetchall()
    
    if request_check > 0: #そもそもフレンド申請が来ているかを確認する。 ちなみに双方からフレンド申請している状態を、フレンド同士としている。
        print("\nお友達いるみたいです。よかったね")
        print(f"\nmy_relation:{my_relation}")
        print(f"\nothers_relation:{others_relation}")
        
        my_li = []
        oth_li = []
        
        request_list = []
        friend_list = []
        
        for i in my_relation:
            my_li.append(i["friend_id"])
            
        for i in others_relation:
            oth_li.append(i["user_id"])
            
        friend_list = set(oth_li) & set(my_li)
        request_list = set(oth_li) - set(my_li)
        
        print(f"\nfriend_list:{friend_list}")
        print(f"\nrequest_list:{request_list}")
        
        if friend_list:
            tuple(friend_list)
            print(friend_list)
            sql = "SELECT user_id , user_name FROM informations WHERE user_id in %s;" 
            cursor.execute(sql,friend_list)
            friend_list = cursor.fetchall()
        
        if request_list:
            tuple(request_list)
            print(request_list)
            sql = "SELECT user_id , user_name FROM informations WHERE user_id in %s;" 
            cursor.execute(sql,request_list)
            request_list = cursor.fetchall()
            
        print(f"\nmy_relation:{my_relation}")
        print(f"\nothers_relation:{others_relation}")
        print(f"\nrequest_list:{request_list}")
        print(f"\nfriend_list:{friend_list}")
        
        return friend_list , request_list

    else:
        #一応求められてるから、変数を作成する。
        friend_list = []
        request_list = []
        
        print("\nフレンドもないし、申請もない。")
        return (friend_list , request_list)
    
def getinfo(cursor , user_id = None, user_name = None):#informatonから情報を取ってくる関数。
    if user_id:
        sql = "SELECT * FROM informations WHERE user_id = %(user_id)s"
        cursor.execute(sql , {"user_id" : user_id})
        user_data = cursor.fetchone()

    elif user_name:
        sql = "SELECT * FROM informations WHERE user_id = %(user_name)s"
        cursor.execute(sql , {"user_name" : user_name})
        user_data = cursor.fetchone()

    else:
        user_data = None

    return user_data