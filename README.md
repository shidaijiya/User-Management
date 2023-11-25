# 登陆注册验证Demo

## 此代码基于py和MySQL，仅作为演示

#### 1.克隆这个仓库：#####`https://github.com/shidaijiya/User-Management.git`

#### 2.需要安装的软件包
##### `pip install -r requirements.txt`
#### 3.在MySQL中创建一个名为：`user_data`的数据库
##### 数据库里创建2个表
##### `mail_val_code`
```mysql
CREATE TABLE `mail_val_code` (
  `mail_val_code` int NOT NULL COMMENT '6位邮箱验证码',
  `user_mail` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户邮箱',
  `udid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '会话udid',
  `exp_time` datetime NOT NULL COMMENT '过期时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```
##### `new_user_data`
```mysql
CREATE TABLE `new_user_data` (
  `user_mail` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户邮箱',
  `user_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户昵称',
  `user_id` int NOT NULL COMMENT '用户4位id',
  `user_pwd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户密码',
  `user_udid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户唯一标识符',
  `user_signin_time` datetime NOT NULL COMMENT '用户注册日期',
  PRIMARY KEY (`user_udid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```
#### 4.修改代码里的MySQL和邮箱服务器信息
## 许可证 [Apache license 2.0](https://apache.org/licenses/LICENSE-2.0.txt)协议

