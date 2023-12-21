import datetime

from django.db import models


class Users(models.Model):
    tg_id = models.CharField(max_length=128, verbose_name='ID пользователя в телеграмме')
    username = models.CharField(max_length=64, verbose_name='Ник пользовател в телеграмме')
    subscription = models.BooleanField(default=False, verbose_name='Есть ли у пользователя подписка')
    is_pay = models.BooleanField(default=False, verbose_name='Начал ли оплату на YooMoney')
    is_admin = models.BooleanField(default=False, verbose_name='Является ли пользователь админом')
    end_subscription = models.DateField(default=None, null=True, verbose_name='Дата окончания подписки')

    def __str__(self):
        return self.tg_id

    def check_subscription(self):
        now_date = datetime.date.today()
        a = self.end_subscription
        if a == now_date:
            return True


class Channels(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название канала. Может быть любым')
    channel_url = models.CharField(max_length=256, verbose_name='Ссылка на канал')
    target_word = models.CharField(max_length=1024, verbose_name='Слова таргеты.')
    stop_word = models.CharField(max_length=1024, verbose_name='Стоп слова.')
    in_use = models.BooleanField(default=False, verbose_name='использовался ли этот канал ранее')
    last_message = models.IntegerField(default=0, verbose_name='Последнее прочитанное соощение')
    need_send_contacts = models.BooleanField(default=False,
                                             verbose_name='Нужно ли отправлять сообщении контакты для связи')

    def __str__(self):
        return self.name


class SendMessages(models.Model):
    text = models.TextField(verbose_name='Текст сообщения')
