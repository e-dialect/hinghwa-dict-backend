#   小工具集合
##  1. quiz_voice_upload

    测试题语音上传工具

### 使用方法：
        在文件目录下建立.env环境变量文件，文件内填充
            user=xxxxx
            password=xxxxx
        管理员级账号信息
        随后执行程序，根据提示输入待上传语音所在目录地址，即可上传
    注：语音文件需命名为xxx.mp3 或 xxx.m4a xxx代指quiz编号
    .env文件示例：
        user=123456
        password=123456
##  2.data_process

    数据处理工具
### 2.1 add_tradition.py、re_add_tradition.py
    将简体中文转换为繁体中文，根据参考文件对目标文件进行繁体生成
    数据集格式为 xls,字段顺序可以自行调整

### 2.2 datachar.py
    单字文件处理，根据字符、拼音、ipa,生成对应声母、韵母、声调信息
    数据集格式为 xls,字段顺序可以自行调整

### 2.3 worddata.py
    单词文件处理，生成对应切片信息
    数据集格式为 xls,字段顺序可以自行调整

### 2.4 qiepian.py
    根据IPA信息生成对应声母、韵母、声调信息，生成.mp3文件，worddata.py的基础
    数据集格式为 xls,字段顺序可以自行调整

### 2.5 translate.py
    拼音信息翻译文件，datachar.py 的基础
    数据集格式为 xls,字段顺序可以自行调整

### 2.6 pre_datachar.py
    单字文件预处理脚本，将多音字进行拆分
    数据集格式为 xls,字段顺序可以自行调整

### 2.7 tradition_to_simple.py
    繁体字转换简体字
    数据集格式为 xls,字段顺序可以自行调整

##  3. easy_test

    后端测试小工具
    
    python3 manage.py makemigrations
    python3 manage.py migrate
    DJANGO_SUPERUSER_PASSWORD=testtest123 python manage.py createsuperuser --username admin --email test@test.com --no-input
    echo -e "from django.contrib.auth.models import User\nuser=User.objects.create_user('user_test','user_test@user_test.com','123456')\nuser.set_password('123456')\nuser.save()\nexit()" | python manage.py shell
    echo -e "from django.contrib.auth.models import User\nuser=User.objects.create_user('user_test_old_password','user_test_old_password@user_test_old_password.com','12')\nuser.set_password('12')\nuser.save()\nexit()"| python manage.py shell
