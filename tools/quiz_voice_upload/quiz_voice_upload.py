import json
import os
from os.path import splitext
from requests_toolbelt import sessions
from environs import Env
from upload_file import upload_file

#   http = sessions.BaseUrlSession(base_url="https://api.pxm.edialect.top")
http = sessions.BaseUrlSession(base_url="https://api.pxm.test.edialect.top")

env = Env()
env.read_env(path=".env")
username = env.str("user")
password = env.str("password")
data = {"username": username, "password": password}
token = http.post("/login", data=json.dumps(data)).json()["token"]
url = input("请输入文件夹路径:")
#   url = os.path.pardir
files = os.listdir(url)
for f in files:
    suffix = splitext(f)[-1]
    if suffix == ".m4a" or suffix == ".mp3":
        id = f.split(".")[0].split("/")[-1]
        res = http.get(f"/quizzes/{id}", headers={"token": token}).json()
        result = {"quiz": {}}
        result["quiz"]["question"] = res["quiz"]["question"]
        result["quiz"]["options"] = res["quiz"]["options"]
        result["quiz"]["answer"] = res["quiz"]["answer"]
        result["quiz"]["explanation"] = res["quiz"]["explanation"]
        #   result["quiz"]["voice_source"] = f"https://cos.edialect.top/quizzes/{id}{suffix}"
        result["quiz"][
            "voice_source"
        ] = f"https://cos.test.edialect.top/quizzes/{id}{suffix}"
        http.put(
            f"/quizzes/{id}",
            data=json.dumps(result),
            headers={"token": token},
        )
