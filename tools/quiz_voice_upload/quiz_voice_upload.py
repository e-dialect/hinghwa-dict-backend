import json
import os
from os.path import splitext

import requests

from environs import Env

env = Env()
env.read_env(path='.env')
username = env.str('user')
password = env.str('password')
data = {"username": username, "password": password}
token = requests.post(f"https://api.pxm.edialect.top/login", data=json.dumps(data)).json()["token"]
url = input("请输入文件夹路径:")
#   url = os.path.pardir
file = os.listdir(url)
for f in file:
    str = splitext(f)[-1]
    if str == ".m4a" or str == ".mp3":
        id = f.split(".")[0].split("/")[-1]
        #   正式
        res = requests.get(f"https://api.pxm.edialect.top/quizzes/{id}", headers={'token': token}).json()
        #   测试服
        #   res = requests.get(f"https://api.pxm.test.edialect.top/quizzes/{id}", headers={'token': token}).json()
        #   本地
        #   res = requests.get(f"http://127.0.0.1:8000/quizzes/{id}", headers={'token': token}).json()
        result = {"quiz": {}}
        result["quiz"]["question"] = res["quiz"]["question"]
        result["quiz"]["options"] = res["quiz"]["options"]
        result["quiz"]["answer"] = res["quiz"]["answer"]
        result["quiz"]["explanation"] = res["quiz"]["explanation"]
        result["quiz"]["voice_source"] = f"https://cos.edialect.top/quizzes/{id}{str}"
        requests.put(f"https://api.pxm.edialect.top/quizzes/{id}", data=json.dumps(result), headers={'token': token})
        # requests.put(f"https://api.pxm.test.edialect.top/quizzes/{id}", data=json.dumps(result), headers={'token': token})
        # requests.put(f"http://127.0.0.1:8000/quizzes/{id}", data=json.dumps(result), headers={'token': token})
