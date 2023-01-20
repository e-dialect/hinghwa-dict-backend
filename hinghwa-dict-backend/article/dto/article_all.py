from ..models import Article
from user.dto.user_all import user_all
from django.utils.timezone import localtime


# 返回文章详细信息
def article_all(article: Article) -> dict:
    user = article.author
    response = {
        "id": article.id,
        "author": user_all(user),
        "likes": article.like(),
        "views": article.views,
        "publish_time": localtime(article.publish_time).__format__("%Y-%m-%d %H:%M:%S"),
        "update_time": localtime(article.update_time).__format__("%Y-%m-%d %H:%M:%S"),
        "title": article.title,
        "description": article.description,
        "content": article.content,
        "cover": article.cover,
        "visibility": article.visibility,
        "like_users": [x.id for x in article.like_users.all()],
    }
    return response
