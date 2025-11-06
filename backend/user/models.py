from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator


class CustomUser(AbstractUser):
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        help_text=(
            '150 символов или меньше. Только буквы, цифры и @/./+/-/_ .'
        ),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким логином уже зарегистрирован.',
        },
    )
    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)
    email = models.EmailField('email address', unique=True)


class Subscription(models.Model):
    pass
