FROM python:3.10-bookworm

WORKDIR /usr/src/HinghwaDict-backend

# Update apt sources to use Huawei Cloud mirror
RUN sed -i 's@deb.debian.org@repo.huaweicloud.com@g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN echo "yes" | python manage.py collectstatic

EXPOSE 8000

CMD [ "python","manage.py","runserver","0.0.0.0:8000","--insecure" ]
