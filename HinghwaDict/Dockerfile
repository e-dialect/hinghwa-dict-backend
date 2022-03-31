FROM python:3.8.11

WORKDIR /usr/src/HinghwaDict-backend

COPY requirements.txt .
#更新apt-get源 使用163的源
RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak && \
    echo "deb https://mirrors.163.com/debian/ bullseye main non-free contrib" >/etc/apt/sources.list && \
    echo "deb https://mirrors.163.com/debian-security/ bullseye-security main" >>/etc/apt/sources.list && \
    echo "deb https://mirrors.163.com/debian/ bullseye-updates main non-free contrib" >>/etc/apt/sources.list && \
    echo "deb https://mirrors.163.com/debian/ bullseye-backports main non-free contrib" >>/etc/apt/sources.list
RUN apt-get update
RUN apt-get install ffmpeg -y
RUN pip install -ihttps://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

COPY . .

RUN echo "yes" | python manage.py collectstatic

EXPOSE 8000

CMD [ "python","manage.py","runserver","0.0.0.0:8000","--insecure" ]