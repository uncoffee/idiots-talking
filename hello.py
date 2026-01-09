import pymysql  #pip は a.txt
import uuid

from kansuu import check_uuid , user_relations , getinfo , use_db ,check_none

from flask import Flask, make_response , render_template,request , redirect, url_for

"""
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
作品名はUnchartChat
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
https://zenn.dev/japan/articles/82d80f0764ecc2
"""

#-------------------------------------------

#メモ 
#user_name = request.args.get("user_name")

#-------------------------------------------

app = Flask(__name__)

#一番最初のログインページに飛ばす。
@app.route("/")
def hello_world():
    return render_template("login.html")

#フレンドの一覧が見れるページに飛ばす。cookieが必要。
@app.route("/menu" , methods = ["get"]) #フレンド一覧のurlがこれ。
@use_db
@check_uuid
def menu(cursor , user_data , error = 0):
    friend_list , request_list = user_relations(cursor , user_data["user_id"])

    return render_template("menu.html" , friend_list = friend_list , request_list = request_list , user_data = user_data , error = error)

#チャット部屋のページに飛ばす。cookieが必要
@app.route("/chatroom" , methods = ["get"])
@use_db
@check_uuid
def chatroom(cursor , user_data , error = 0):
    print("chatroom関数が叩かれたよ")

    friend_id = request.args.get("friend_id")
    if check_none(friend_id):
        return redirect("/menu" , code=302)

    user_id = user_data["user_id"]
    user_name = user_data["user_name"]

    if check_none(user_id , user_name):
        return redirect("/chatroom" , code=302)

    print(f"\nuser_id:{user_id} friend_id:{friend_id}")

    friend_data = getinfo(cursor , friend_id)

    sql = """SELECT sender_id , log_id , timelog , chatlog 
    FROM chatlogs 
    WHERE (sender_id = %(user_id)s AND recelver_id = %(friend_id)s) 
    OR (sender_id = %(friend_id)s AND recelver_id = %(user_id)s) 
    ORDER BY chatlogs.log_id
    ;"""
    cursor.execute(sql , {"user_id":user_id , "friend_id":friend_id})
    chatlogs = cursor.fetchall()

    print(f"\n送信準備ok! chatlogs:{chatlogs} user_data:{user_data} friend_data:{friend_data}")
    
    #chatlogsには{"sender_id":"???","recelver_id":"???","timelog":"????y??m??d","chatlog":"?????????","sender":"True OR False"}　が入っている
    return render_template("chatroom.html", error = error, chatlogs = chatlogs , user_data = user_data , friend_data = friend_data , UTC = -9)

@app.route("/make_account" , methods = ["get"])
def make_account(error = 0):
    return render_template("make_account.html" , error = error) 


#こっからpostゾーン

@app.route("/chatroom" , methods = ["post"])
@use_db
@check_uuid
def chatroom_post(cursor , user_data):
    print("chatroom_post関数が叩かれたよ。")

    sender_id = user_data["user_id"]

    recelver_id = request.form.get("recelver_id")
    text = request.form.get("text")

    print(f"recelver_id:{recelver_id} text:{text}")

    if check_none(recelver_id,text):
        return redirect("/menu" , code=302)

    if len(text) >= 250:
        return chatroom(cursor , user_data , error = 1)
    
    sql = "INSERT INTO chatlogs (sender_id , recelver_id , timelog , chatlog) VALUES (%(sender_id)s, %(recelver_id)s, NOW(), %(text)s);"
    cursor.execute(sql , {"sender_id" : sender_id , "recelver_id" : recelver_id , "text" : text})

    return redirect(f"/chatroom?friend_id={recelver_id}" , code=302)

@app.route("/login" , methods = ["post"])
@use_db
def login(cursor):
    
    print("ログイン関数がたたかれたよ")
    user_name = request.form.get("user_name")
    user_pass = request.form.get("user_pass")

    if check_none(user_name , user_pass):
        return redirect("/" , code=302)
    
    print(f"\nuser_name:{user_name} user_pass:{user_pass}")
    print("\n通常のユーザ認証")
    
    sql = "SELECT * FROM informations WHERE user_name = %(user_name)s;"
    result = cursor.execute(sql , {"user_name" : user_name})
    user_data = cursor.fetchone()

    if result == 1:
        user_id = user_data["user_id"] #返り血から欲しい値を取り出す。
        print(f"\nuser_id:{user_id}")
        
        sql = "SELECT user_id FROM passwords WHERE (user_id = %(user_id)s) AND (password = %(user_pass)s);"
        cursor.execute(sql , {"user_id" : user_id , "user_pass" : user_pass})
        check_account = cursor.fetchone()

        print(check_account["user_id"] , user_id)
        print(type(check_account["user_id"]) , type(user_id))

        if check_account["user_id"] == user_id:
            print("認証が成功")

            user_uuid = uuid.uuid4().hex

            print(f"uuid:{user_uuid} user_id{user_id}")
            sql = "INSERT INTO uuids (uuid , user_id) VALUES (%(user_uuid)s , %(user_id)s);"
            cursor.execute(sql, {"user_uuid" : user_uuid , "user_id" : user_id})

            print(f"\n認証完了 id:{user_id} name:{user_name} pass:{user_pass}")
            friend_list , request_list = user_relations(cursor , user_id)

            response = make_response(render_template("menu.html" , friend_list = friend_list , request_list = request_list , user_data = user_data))
            response.set_cookie("uuid", value=user_uuid, max_age=60)

            return response

    return redirect("/", code=302)
        
@app.route("/friend_request" , methods = ["post"])
@use_db
@check_uuid
def friend_request(cursor , user_data):
    print("フレンド申請関数が叩かれたよ。")

    user_id = user_data["user_id"]

    request_id = request.form.get("request_id")

    if check_none(request_id):
        return redirect("/menu" , code=302)
    
    print(f"\nuser_id:{user_id} request_id:{request_id}")

    sql = "SELECT * FROM relations WHERE (user_id = %(user_id)s AND friend_id = %(request_id)s);"
    result = cursor.execute(sql , {"user_id" : user_id , "request_id" : request_id}) #相手と自分の関係性を確認
    
    if not result == 0:
        return menu(cursor , user_data , error = 2)
    
    sql = "INSERT INTO relations (user_id , friend_id) VALUES (%(user_id)s , %(request_id)s);"
    cursor.execute(sql , {"user_id" : user_id , "request_id" : request_id})
    
    print(f"申請完了 相手のID:{request_id}")
    return redirect("/menu", code=302)
    

@app.route("/friend_judg" , methods = ["post"])
@use_db
@check_uuid
def friend_judg(cursor , user_data):
    print("フレンド判断関数が叩かれたよ。")
    
    user_id = user_data["user_id"]

    request_id = request.form.get("request_id")
    judg = request.form.get("judg")

    if check_none(request_id , judg):
        return redirect("/menu" , code=302)
    
    print(f"\nuser_id:{user_id} request_id:{request_id}")

    sql = "SELECT * FROM relations WHERE user_id = %(request_id)s AND friend_id = %(user_id)s;"
    result = cursor.execute(sql , {"user_id" : user_id , "request_id" : request_id}) #相手と自分の関係性を確認
    
    print("\n注意 relation テーブルには主キーしか含まれていないため、SELECT文に対してレコードの数で返してくるよ。")
    print(f"関係性を確認。0であれば関係がない。listであれば関係あり。例外はしらん。:{result}")
    
    if result == 0:
        print("\n不正なリクエスト。関係性が存在していないよ。")
        return redirect("/menu" , code=302)
        
    elif result == 1:
        print("\n重複なしリクエストを確認。")
        
        if judg == "TRUE":
            print(f"id:{request_id}さんからのリクエストを受けたよ")
            sql = "INSERT INTO relations (user_id , friend_id) VALUES (%(user_id)s , %(request_id)s);"
            cursor.execute(sql , {"user_id" : user_id , "request_id" : request_id})
            
        else:
            print(f"id:{request_id}さんからのリクエストを断ったよ")
            sql = "DELETE FROM relations WHERE user_id = %(request_id)s AND friend_id = %(user_id)s;"
            cursor.execute(sql , {"user_id" : user_id , "request_id" : request_id})
    
    return redirect("/menu", code=302)
    
@app.route("/make_account" , methods = ["post"])
@use_db
def make_account_post(cursor):
    print("make_account関数がたたかれたよ！")
    new_name = request.form["name"]
    new_pass = int(request.form["pass"])
    
    print(f"\nnew_name:{new_name} new_pass:{new_pass}")
    
    #新規作成のルールに則っているか確認。　ルール：名前の重複なし、かつ名前は１０文字まで。
    
    if len(new_name) > 10:
        print("\n名前が11文字以上です。")
        return make_account(error = 1)
    
    user_data = getinfo(cursor , None , new_name)

    if not user_data == None: 
        print("\n同じ名前のユーザーがいます。")
        return make_account(error = 2)
    
    print("\n入力されたデータにもんだいはなかったよん")
        
    sql = "INSERT INTO informations (user_name) VALUES (%(new_name)s);"
    cursor.execute(sql , {"new_name" : new_name}) #まずは名前からDBに入れる
    new_id = cursor.lastrowid

    print(f"\nnew_id:{new_id}")
    
    sql = "INSERT INTO passwords VALUES (%(new_id)s , %(new_pass)s);"
    cursor.execute(sql , {"new_id" : new_id , "new_pass" : new_pass}) #次にpasswordを登録する
    
    print(f"\n新規アカウント作成完了。 名前:{new_name} ID:{new_id} Pass:{new_pass}")

    return redirect("/" , code = 302)

if __name__ == "__main__":
    app.run()