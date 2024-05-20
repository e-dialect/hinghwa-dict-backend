FROM python:3.10-bookworm

WORKDIR /usr/src/HinghwaDict-backend

RUN sed -i 's@deb.debian.org@repo.huaweicloud.com@g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update
RUN apt-get install ffmpeg -y

COPY requirements.txt .
RUN pip install -ihttps://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

COPY . .

RUN echo "yes" | python manage.py collectstatic

EXPOSE 8000

CMD [ "python","manage.py","runserver","0.0.0.0:8000","--insecure" ]
