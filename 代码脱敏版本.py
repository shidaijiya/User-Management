# -*- coding: UTF-8-*-
import datetime
import hashlib
import random
import re
import smtplib
import time
import uuid
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
import pymysql
import sys

while True:
    # 尝试连接数据库
    try:
        # 创建数据库连接
        db = pymysql.connect(
            host='localhost',  # 连接主机, 默认localhost
            user='root',  # 用户名
            passwd='root',  # 密码
            port=3306,  # 端口，默认为3306
            db='user_data',  # 数据库名称
            charset='utf8'  # 字符编码
        )

        break  # 退出循环
    except Exception as e:
        print('连接数据库失败，错误代码:', str(e))
        print("将在5s后重试")
        time.sleep(5)


# 验证邮箱格式
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# 验证码过期时间
def code_exp_time():
    # 获取当前日期和时间
    now = datetime.datetime.now()
    five_minutes_later = now + datetime.timedelta(minutes=5)
    # 移除微秒部分
    five_minutes_later = five_minutes_later.replace(microsecond=0)
    return five_minutes_later


# 发送验证邮件
def send_mail(receiver):
    try:
        # SMTP服务器信息
        smtp_server = 'smtp.office365.com'
        smtp_port = 587  # SMTP端口

        # 发件人和收件人信息
        sender_email = 'YOUR EMAIL'
        password = 'YOUR PASSWORD'

        # 发件人昵称
        nickname = 'your-nickname'
        sender = formataddr((Header(nickname, 'utf-8').encode(), sender_email))

        # 生成随机验证码
        verification_code = ''.join(random.choices('0123456789', k=6))

        # 创建邮件
        email_body = f'''
            <html>
            <body>
            <p>你好,</p>
            <p>这是你的验证码:</p>
            <p style="font-size:30px;color:blue;">{verification_code}</p>
            <p>请在5分钟内使用此验证码。</p>
            <p>谢谢！<br>your team</p>
            </body>
            </html>
            '''
        message = MIMEText(email_body, 'html', 'utf-8')
        message['From'] = sender
        message['To'] = receiver
        message['Subject'] = '您的验证码'

        # 连接SMTP服务器并发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender, [receiver], message.as_string())

        return verification_code

    except Exception as e:
        print('发送验证码失败，错误代码:', str(e))


# 上传验证码数据至数据库
def up_val_data(val_code, ipt_mail, exp_time):
    # 创建游标对象cursor
    cursor = db.cursor()

    # 检查是否已存在相同user_mail的记录
    check_query = f"SELECT * FROM mail_val_code WHERE user_mail = '{ipt_mail}';"
    cursor.execute(check_query)
    existing_record = cursor.fetchone()

    if existing_record:
        # 如果已存在记录，执行UPDATE或DELETE操作，然后再执行INSERT操作
        update_query = f'''UPDATE mail_val_code 
        SET mail_val_code = {val_code}, 
            udid = '{uuid.uuid1()}', 
            exp_time = '{exp_time}' 
        WHERE user_mail = '{ipt_mail}';'''

        try:
            cursor.execute(update_query)
            db.commit()  # 提交UPDATE操作
            # print('数据更新成功！')
        except Exception as e:
            print('更新失败，错误代码:', str(e))
    else:
        # 如果不存在记录，直接执行INSERT操作
        insert_query = f'''INSERT INTO mail_val_code (mail_val_code, user_mail, udid, exp_time)
        VALUES ({val_code}, '{ipt_mail}', '{uuid.uuid1()}', '{exp_time}');'''

        try:
            cursor.execute(insert_query)
            db.commit()  # 提交INSERT操作
            # print('数据插入成功！')
        except Exception as e:
            print('插入失败，错误代码:', str(e))

    # 关闭游标
    cursor.close()


# 整合验证码内容上传数据库
def send_val_mail(ipt_mail):
    # 定义验证代码
    val_code = send_mail(ipt_mail)
    print("验证码已发送5分钟有效")
    # 定义设置过期时间
    exp_time = code_exp_time()
    # 传入邮箱、验证码和过期时间到上传数据库
    up_val_data(val_code, ipt_mail, exp_time)  # 提供 val_code、ipt_mail 和 exp_time 参数


# 比较验证码是否过期并返回
def val_code_exp(future_time):
    # 获取当前日期和时间
    now = datetime.datetime.now()
    now = now.replace(microsecond=0)  # 移除微秒部分
    # 比较两个日期时间对象
    if now < future_time:
        return False
    else:
        return True


# MySQL数据库中查找验证码
def find_val_code(user_mail_to_search):
    cursor = db.cursor()
    try:
        # 执行查询语句
        query = """
        SELECT mvc.mail_val_code, mvc.exp_time
        FROM mail_val_code AS mvc
        INNER JOIN (
            SELECT user_mail, MAX(exp_time) AS latest_exp_time
            FROM mail_val_code
            WHERE user_mail = %s
        ) AS subquery
        ON mvc.user_mail = subquery.user_mail AND mvc.exp_time = subquery.latest_exp_time;
        """
        cursor.execute(query, (user_mail_to_search,))

        # 获取查询结果
        result = cursor.fetchone()
        if result:
            mail_val_code, exp_time = result
            return mail_val_code, exp_time
        else:
            print("未找到匹配记录")
            return None
    except pymysql.MySQLError as e:
        print(f"数据库错误: {e}")
    finally:
        cursor.close()


# 验证验证码是否过期
def val_mail_code(user_mail):
    result = find_val_code(user_mail)
    if result:
        mail_val_code, exp_time = result
        while True:
            ipt_val_code = ipt_non_empty('请输入6位验证码：')
            if not val_code_exp(exp_time):
                if int(ipt_val_code) == mail_val_code:
                    print("恭喜验证成功！")
                    break
                else:
                    print("验证码过期或错误")
                    continue
            else:
                print('验证码过期或错误')
                continue
    else:
        print("未找到匹配记录")


# 验证密码格式
def validate_password(pwd):
    pattern = r'(?=.*[!@#$%^&*().]).{6,12}'
    return re.search(pattern, pwd) is not None


# 检测输入是否为空
def ipt_non_empty(prompt):
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        else:
            print("输入不能为空")


# 哈希加密密码
def hash_password(pwd, salt):
    salted_password = str(pwd) + str(salt)
    hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
    return hashed_password


# 上传用户注册数据
def up_signup_data(user_mail, user_name, user_id, hash_pwd):
    # 创建游标对象cursor
    cursor = db.cursor()
    val_code = f'''INSERT INTO new_user_data (user_mail, user_name, user_id, user_pwd, user_udid, user_signin_time)
    VALUES ('{user_mail}', '{user_name}', '{user_id}', '{hash_pwd}', '{uuid.uuid4()}', NOW());'''
    try:
        cursor.execute(val_code)
        db.commit()  # 提交事务！！！
        # print('数据上传成功！')
    except Exception as e:
        print('数据上传失败，错误代码:', str(e))
    # 关闭数据库连接
    db.close()
    # print('已关闭MySQl连接')


# 用户输入注册数据
def ipt_signup_data():
    ipt_name = ipt_non_empty('请输入你的昵称：')
    print("------------------------------------------------------------\n"
          "确保密码长度至少为6位且不超过12位,并且至少有一个特殊字符\n"
          "我们不会保存您的密码!,您的密码会通过哈希加密,除了您自己没人会知道您的密码\n"
          "------------------------------------------------------------")
    ipt_pwd = ipt_non_empty('请输入你的密码：')
    while not validate_password(ipt_pwd):
        print("密码无效,确保密码长度至少为6位且不超过12位,并且至少有一个特殊字符")
        ipt_pwd = ipt_non_empty('请输入你的密码：')
    ipt_val_pwd = ipt_non_empty('请再次确认密码:')
    while ipt_pwd != ipt_val_pwd:
        print("密码不一致")
        ipt_val_pwd = ipt_non_empty('请再次确认密码:')
    # 随机用户4位id
    random_id = random.randint(1000, 9999)
    # 哈希值加密密码
    hash_pwd = hash_password(ipt_pwd, random_id)
    print(f"你的id为:{ipt_name}#{random_id}")
    return ipt_name, random_id, hash_pwd


# 检查是否有相同邮箱
def check_user_mail(user_mail_to_check):
    global cursor
    try:
        # 创建游标对象cursor
        cursor = db.cursor()

        # 编写SQL查询
        query = f"SELECT user_mail FROM new_user_data WHERE user_mail = '{user_mail_to_check}';"

        # 执行查询
        cursor.execute(query)

        # 获取查询结果
        result = cursor.fetchone()

        # 如果查询结果不为空，表示存在相同的邮箱地址
        if result:
            return True
        else:
            return False

    except Exception as e:
        print('查询失败，错误代码:', str(e))
        return False
    finally:
        # 关闭游标
        cursor.close()


# 查找用户数据
def find_user_data(user_mail):
    try:
        # 创建游标对象cursor
        cursor = db.cursor()

        # 执行查询语句，根据user_mail查询数据
        query = f"""
        SELECT user_name, user_id, user_pwd, user_udid, user_signin_time
        FROM new_user_data
        WHERE user_mail = '{user_mail}';
        """
        cursor.execute(query)

        # 获取查询结果
        result = cursor.fetchone()

        if result:
            user_name, user_id, user_pwd, user_udid, user_signin_time = result
            return user_name, user_id, user_pwd, user_udid, user_signin_time
        else:
            print("未找到匹配记录")
    except Exception as e:
        print("数据库错误:", str(e))
    finally:
        # 关闭游标
        cursor.close()


def login():
    print("-------------------------------------\n"
          "找到你的账号啦!\n"
          "密码登陆请输入:1\n"
          "邮箱登陆请输入:2\n"
          "--------------------------------------")
    found = False
    while not found:
        login_choice = ipt_non_empty('请选择:')
        if login_choice == '1':
            user_data = find_user_data(ipt_email)  # 执行查询
            user_name, user_id, user_pwd, user_udid, user_signin_time = user_data
            while True:
                ipt_pwd = ipt_non_empty('请输入账号密码：')
                hash_pwd = hash_password(ipt_pwd, user_id)
                if hash_pwd == user_pwd:
                    print("密码正确！")
                    print(f"欢迎回来!{user_name}#{user_id}")
                    return True
                    pass
                    break
                else:
                    print("密码错误！")
                    continue
            found = True
        elif login_choice == '2':
            send_val_mail(ipt_email)
            val_mail_code(ipt_email)
            print("验证成功!")
            user_data = find_user_data(ipt_email)  # 执行查询
            user_name, user_id, user_pwd, user_udid, user_signin_time = user_data
            print(f"欢迎回来!{user_name}#{user_id}")
            return True
        else:
            print("无效字符")
            continue


while True:
    ipt_email = input('请输入你的邮箱:').strip()
    if validate_email(ipt_email):
        # 调用函数检查邮箱地址是否存在于数据库中
        if check_user_mail(ipt_email):
            login_result = login()
            break
        else:
            send_val_mail(ipt_email)
            val_mail_code(ipt_email)
            ipt_name, random_id, hash_pwd = ipt_signup_data()
            up_signup_data(ipt_email, ipt_name, random_id, hash_pwd)
            print("恭喜注册成功！")
            break
    else:
        print("无效的邮箱地址")

if login_result:
    print("函数返回登陆状态为True")
else:
    print("函数返回登陆状态为False")

input("目前程序已经做到此处,请回车关闭")
