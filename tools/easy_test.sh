python3 manage.py makemigrations
python3 manage.py migrate
DJANGO_SUPERUSER_PASSWORD=testtest123 python manage.py createsuperuser --username admin --email test@test.com --no-input
echo -e "from django.contrib.auth.models import User\nuser=User.objects.create_user('user_test','user_test@user_test.com','123456')\nuser.set_password('123456')\nuser.save()\nexit()" | python manage.py shell
echo -e "from django.contrib.auth.models import User\nuser=User.objects.create_user('user_test_old_password','user_test_old_password@user_test_old_password.com','12')\nuser.set_password('12')\nuser.save()\nexit()"| python manage.py shell
