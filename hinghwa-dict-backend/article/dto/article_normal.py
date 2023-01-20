from django.utils.timezone import localtime
from ..models import Article


# 返回文章基本信息
def article_normal(article: Article) -> dict:
    response = {
        "id": article.id,
        "likes": article.like(),
        "author": article.author.id,
        "views": article.views,
        "publish_time": localtime(article.publish_time).__format__("%Y-%m-%d %H:%M:%S"),
        "update_time": localtime(article.update_time).__format__("%Y-%m-%d %H:%M:%S"),
        "title": article.title,
        "description": article.description,
        "content": article.content,
        "cover": article.cover,
        "visibility": article.visibility,
    }
    return response
