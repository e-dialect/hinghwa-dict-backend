from environs import Env
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client


def upload_file(path, key):
    env = Env()
    env.read_env(path=".env")
    COS_REGION = env.str("COS_REGION")
    COS_SECRET_ID = env.str("COS_SECRET_ID")
    COS_SECRET_KEY = env.str("COS_SECRET_KEY")
    COS_BUCKET = env.str("COS_BUCKET")
    config = CosConfig(
        Region=COS_REGION,
        SecretId=COS_SECRET_ID,
        SecretKey=COS_SECRET_KEY,
    )
    client = CosS3Client(config)
    response = client.upload_file(Bucket=COS_BUCKET, LocalFilePath=path, Key=key)
    # if bucket name contains 'test'
    if COS_BUCKET.find("test") != -1:
        return f"https://cos.test.edialect.top/{key}"
    return f"https://cos.edialect.top/{key}"
