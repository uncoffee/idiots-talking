import pymysql  #pip は a.txt
import uuid

from flask import Flask, make_response , render_template,request , redirect, url_for

#-------------------------------------------

#メモ 
#user_name = request.args.get("user_name")

#-------------------------------------------


app = Flask(__name__)
    
def getconnection():#データベースへ接続
    connection = pymysql.connect(
    host="localhost", #わからん
    db="myapp", #使ってるデータベースの名前
    user="root", #わからん
    password="", #パスワードは無し
    charset="utf8", #文字コード指定
    cursorclass=pymysql.cursors.DictCursor #dict型(辞書型)に型を変更している　これによってhtml上でのデータの取り出しが楽になる。らしい
    )

    return connection

@app.route("/friend" , methods = ["get"]) #フレンド一覧のurlがこれ。
def result():
    #-----DBに接続します。------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------
    
    user_data = check_uuid(cursor)

    if user_data:
        user_id = user_data["user_id"]
        user_name = user_data ["user_name"]

        friend_list , request_list = user_relations(cursor , user_id)

        #-----接続を解除します------
        cursor.close()
        connection.close()
        #---------------------------

        return render_template("friends.html" , friend_list = friend_list , request_list = request_list , user_name = user_name , user_id = user_id)

    else:
        #-----接続を解除します------
        cursor.close()
        connection.close()
        #---------------------------

        return redirect("/", code=302)
    
@app.route("/chatroom" , methods = ["get"]) #フレンド一覧のurlがこれ。
def result():


    user_id = request.args.get("user_id")
    friend_id = request.args.get("friend_id")

    #-----DBに接続します。------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------
    
    if not user_id == None AND not friend_id == None:

        #-----接続を解除します------
        cursor.close()
        connection.close()
        #---------------------------

        return render_template("friends.html" , friend_list = friend_list , request_list = request_list , user_name = user_name , user_id = user_id)

    else:
        #-----接続を解除します------
        cursor.close()
        connection.close()
        #---------------------------

        return redirect("/", code=302)
    
    
@app.route("/result" , methods = ["post"])
def result():
    name = request.form["name"]
    
    connection = getconnection()
    sql = "INSERT INTO players (name) VALUES (%s)"
    cursor = connection.cursor()
    cursor.execute(sql,name)
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return redirect("/", code=302)
    
@app.route("/login" , methods = ["post"])
def login():
    
    print("ログイン関数がたたかれたよ")
    user_name = request.form["user_name"]
    user_pass = request.form["user_pass"]
    
    print(f"\nuser_name:{user_name} user_pass:{user_pass}")
    
    #-----DBに接続します。------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------
    
    if user_name == "ad" and user_pass == "ad":
        print("\n管理者　認証完了")
        sql = "SHOW TABLES;"

        cursor.execute(sql)
        tables = cursor.fetchall()
        
        alldata = {}
        
        for table in tables:
            print(table)
            table_name = table['Tables_in_mydb']
            table_name = table_name.strip("'")
            
            print(f"\nshow columns from {table_name};")
            sql = "show columns from {table_name};"
            cursor.execute(sql)
            columns = cursor.fetchall()
            
            cursor_list = []
            print(columns)
            
            for i in columns:
                column_list = list(i.values())
                cursor_list.append(column_list[0])
                
            alldata.update({str(table_name):cursor_list})
            
        #-----接続を解除します------
        connection.commit()
        cursor.close()
        connection.close()
        #---------------------------
        
        print(alldata)
        return render_template("administrator.html" , alldata = alldata)
        
    #-------------------------------------------------------------------------
    else:
        print("\n通常のユーザ認証")
        user_pass = int(user_pass) #文字の形をdbに合わせる。必要か？これ
        
        print(f"\nuser_name:{user_name}")
        
        sql = "SELECT user_id FROM informations WHERE user_name = %s;"
        result = cursor.execute(sql , user_name)
        user_id = cursor.fetchone()


        if result == 1:
            user_id = user_id["user_id"] #返り血から欲しい値を取り出す。
            print(f"\nuser_id:{user_id}") 
            
            sql = "SELECT user_id FROM passwords WHERE (user_id = %s) AND (password = %s);"
            cursor.execute(sql , (user_id , user_pass))
            check_account = cursor.fetchall()
            
            if check_account:#もし入力された値に該当するアカウントがあれば変数の中にuser_idが入る。なければ、0の値。
    
                
                user_uuid = uuid.uuid4()
                
                print(f"uuid:{user_uuid} user_id{user_id}")

                sql = "INSERT INTO uuids (uuid , user_id) VALUES (%(user_uuid)s , %(user_id)s)"
                cursor.execute(sql, {"user_uuid" : user_uuid , "user_id" : user_id})

                print(f"\n認証完了 id:{user_id} name:{user_name} pass:{user_pass}")

                friend_list , request_list = user_relations(cursor , user_id)

                response = make_response(render_template("friends.html" , friend_list = friend_list , request_list = request_list , user_id = user_id , user_name = user_name ))
                response.set_cookie("uuid", value="user_ssid", max_age=60)

                return response

            #-----接続を解除します------
            connection.commit()
            cursor.close()
            connection.close()
            #---------------------------
    
    cursor.close()
    connection.close()
    return redirect("/", code=302)


    
def check_uuid(cursor): #openとcloseは別でやってね！！！！！
    user_uuid = request.cookies.get("uuid")

    sql = "SELECT user_id FROM uuids WHERE uuid = %(user_uuid)s"
    result = cursor.execute(sql, {"user_uuid" : user_uuid})
    
    if result == 1:
        user_id = cursor.fetchone()
        user_id = user_id["user_id"]

        sql = "SELECT * FROM informations WHERE = %(user_id)s"
        cursor.execute(sql, {"user_id" : user_id})

        return result

    else:
        return False #とりまFalse

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


def getinfo(cursor , user_id):#informatonからデータを取ってくる関数。
    sql = "SELECT * FROM informations WHERE user_id = %(user_id)s"
    cursor.execute(sql , {"user_id" : user_id})
    user_data = cursor.fetchall()

    return user_data

    
    
#開発中。    
@app.route("/getchatlog" , methods = ["get"])
def chatlog():
    print("getchatlog関数が叩かれたよ")

    user_id = request.args.get("user_id")
    friend_id = request.args.get("friend_id")

    user_id = int(user_id)
    friend_id = int(friend_id)

    print(f"\nuser_id:{user_id} friend_id:{friend_id}")
    
    #-----DBに接続します。-------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------
    
    sql = "SELECT log_id , timelog , chatlog FROM chatlogs WHERE sender_id = %(user_id)s AND recelver_id = %(friend_id)s;"
    
    cursor.execute(sql , {"user_id":user_id , "friend_id":friend_id})
    send_logs = cursor.fetchall()

    print(f"\nsend_log:{send_logs}")
    
    sql = "SELECT log_id , timelog , chatlog FROM chatlogs WHERE sender_id = %(friend_id)s AND recelver_id = %(user_id)s;"
    
    cursor.execute(sql , {"user_id":user_id , "friend_id":friend_id})
    recelver_logs = cursor.fetchall()

    print(f"\nrecelver_log:{recelver_logs}")
    
    chatlogs = []
    
    for send in send_logs:
        send["sender"] = True
        chatlogs.append(send)
        
    for recelver in recelver_logs:
        recelver["sender"] = False
        chatlogs.append(recelver)

    print(f"\nchatlogs:{chatlogs}")
        
    chatlogs = sorted(chatlogs ,key=lambda logdata: logdata["log_id"])
    
    #-----接続を解除します------
    connection.commit()
    cursor.close()
    connection.close()
    #---------------------------

    print(f"\n送信準備ok! chatlogs:{chatlogs} user_id:{user_id} user_name:{user_name} friend_id:{friend_id} friend_name:{friend_name}")
    
    #chatlogsには{"sender_id":"???","recelver_id":"???","timelog":"????y??m??d","chatlog":"?????????","sender":"True OR False"}　が入っている
    return render_template("chatroom.html", chatlogs = chatlogs , user_name = user_name , user_id = user_id, friend_name = friend_name , friend_id = friend_id)
        
        
@app.route("/friend_request" , methods = ["post"])
def friend_request():
    
    print("フレンド申請関数が叩かれたよ。")
    
    #リダイレクト難しいから値を取得する。
    user_name = request.form["user_name"]
    friend_list = request.form["friend_list"]
    request_list = request.form["request_list"]
    
    #フレンド認証に使う値
    user_id = int(request.form["user_id"])
    request_id = int(request.form["request_id"])
    
    print(f"\nuser_id:{user_id} request_id:{request_id}")
    
    #-----DBに接続します。------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------

    sql = "SELECT * FROM relations WHERE (user_id = %s AND friend_id = %s);"
    result = cursor.execute(sql , (user_id , request_id)) #相手と自分の関係性を確認
    
    #戻り値が「0」であれば関係がない。「typeがlist型」であれば、フレンド申請済みもしくは、フレンド登録済み。
    if result == 0:
        sql = "INSERT INTO relations (user_id , friend_id) VALUES (%s , %s);"
        cursor.execute(sql , (user_id , request_id))
        
        print(f"申請完了 相手のID:{request_id}")
            
    else:
        print("不正なリクエスト。分岐近くのコメントを参照。")
        
    print("-" * 50)
    
    #-----接続を解除します------
    connection.commit()
    cursor.close()
    connection.close()
    #---------------------------
    
    return redirect("/", code=302)
    
    
        
@app.route("/friend_judg" , methods = ["post"])
def friend_judg():
    print("フレンド判断関数が叩かれたよ。")
    
    user_id = int(request.form["user_id"])
    request_id = int(request.form["request_id"])
    judg = request.form["judg"]
    
    print(f"\nuser_id:{user_id} request_id:{request_id}")
    
    #-----DBに接続します。------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------

    sql = "SELECT * FROM relations WHERE user_id = %s AND friend_id = %s;"
    result = cursor.execute(sql , (request_id , user_id)) #相手と自分の関係性を確認
    
    print("\n注意 relation テーブルには主キーしか含まれていないため、SELECT文に対してレコードの数で返してくるよ。")
    print(f"関係性を確認。0であれば関係がない。listであれば関係あり。例外はしらん。:{result}")
    
    if result == 0:
        print("\n不正なリクエスト。関係性が存在していないよ。")
        
    elif result == 1:
        print("\n重複なしリクエストを確認。")
        
        if judg == "TRUE":
            print(f"id:{request_id}さんからのリクエストを受けたよ")
            sql = "INSERT INTO relations (user_id , friend_id) VALUES (%s , %s);"
            cursor.execute(sql , (user_id , request_id))
            
        else:
            print(f"id:{request_id}さんからのリクエストを断ったよ")
            sql = "DELETE FROM relations WHERE user_id = %s AND friend_id = %s;"
            cursor.execute(sql , (request_id , user_id))
        
    else:
        print("多分もうフレンドになってると思うよ。")
        
    print("-" * 50)
    
    #-----接続を解除します------
    connection.commit()
    cursor.close()
    connection.close()
    #---------------------------
    
    return redirect("/", code=302)
    
@app.route("/make_account" , methods = ["post"])
def make_account():
    print("make_account関数がたたかれたよ！")
    new_name = request.form["name"]
    new_pass = int(request.form["pass"])
    
    print(f"\nnew_name:{new_name} new_pass:{new_pass}")
    

    
    #新規作成のルールに則っているか確認。　ルール：名前の重複なし、かつ名前は１０文字まで。
    
        
    if len(new_name) > 10:
        print("\n名前が11文字以上です。")
        return render_template("make_account.html" , error = 1)
        
        
    #-----DBに接続します。------
    connection = getconnection()
    cursor = connection.cursor()
    #---------------------------
    
    sql = "SELECT * FROM informations WHERE user_name = %s;"
    result = cursor.execute(sql , new_name) #同じ名前のユーザがいないか確認
    print(f"\nresult:{result}")
    

    if not result == 0: 
        print("\n同じ名前のユーザーがいます。")
        #-----接続を解除します------
        cursor.close()
        connection.close()
        #---------------------------
        return render_template("make_account.html" , error = 2)
        
    #---------------------------------------------------------------------------------------
    
    print("\n入力されたデータにもんだいはなかったよん")
        
    sql = "INSERT INTO informations (user_name) VALUES (%s);"
    
    cursor.execute(sql , new_name) #まずは名前からDBに入れる
    new_id = cursor.lastrowid

    print(f"\nnew_id:{new_id}")
    
    sql = "INSERT INTO passwords VALUES (%s , %s);"
    
    result = cursor.execute(sql , (new_id , new_pass)) #まずは名前からDBに入れる
    
    print(f"\n新規アカウント作成完了。 名前:{new_name} ID:{new_id} Pass:{new_pass}")
    #-----接続を解除します------
    connection.commit()
    cursor.close()
    connection.close()
    #---------------------------
    return render_template("login.html")
    
            
@app.route("/make_account_html")
def getlink():

    return render_template("make_account.html" , error = 0)
        
@app.route("/")
def hello_world():
    return render_template("login.html")

if __name__ == "__main__":
    app.run()