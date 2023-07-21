cd hinghwa-dict-backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
admin
test@test.com
testtest123
testtest123
python manage.py shell
from django.contrib.auth.models import User
user=User.objects.create_user("user_test","user_test@user_test.com","123456")
user.set_password("123456")
user.save()
exit()