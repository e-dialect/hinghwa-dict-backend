# -*-coding:utf-8-*-
import os

import requests
from django.conf import settings
from qcloud_cos import CosConfig, CosS3Client


def upload_file(path, key):
    config = CosConfig(
        Region=settings.COS_REGION,
        SecretId=settings.COS_SECRET_ID,
        SecretKey=settings.COS_SECRET_KEY,
    )
    client = CosS3Client(config)
    response = client.upload_file(
        Bucket=settings.COS_BUCKET, LocalFilePath=path, Key=key
    )
    # if bucket name contains 'test'
    if settings.COS_BUCKET.find("test") != -1:
        return f"https://cos.test.edialect.top/{key}"
    return f"https://cos.edialect.top/{key}"


def delete_file(key):
    config = CosConfig(
        Region=settings.COS_REGION,
        SecretId=settings.COS_SECRET_ID,
        SecretKey=settings.COS_SECRET_KEY,
    )
    client = CosS3Client(config)
    client.delete_object(Bucket=settings.COS_BUCKET, Key=key)


def download_file(url, type, user_id, filename):
    try:
        folder = os.path.join(settings.MEDIA_ROOT, type, user_id)
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, filename)
        response = requests.get(url)
        with open(path, "wb") as f:
            f.write(response.content)
        key = f'files/{type}/{user_id}/{filename.replace("_", "/")}'
        url = upload_file(path, key)
        return url
    except Exception as e:
        print("Error occurred when downloading file, error message:")
        print(e)
        return None
