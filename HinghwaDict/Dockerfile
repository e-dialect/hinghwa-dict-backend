FROM python:3.8.11

WORKDIR /usr/src/HinghwaDict-backend

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "python","manage.py","runserver","0.0.0.0:8000" ]