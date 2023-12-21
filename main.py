import asyncio
import datetime
import os
import threading
from multiprocessing import Process
from time import sleep

import django
import telebot
from telebot import types
from telethon.tl.functions.users import GetFullUserRequest
from yoomoney import Quickpay, Client

os.environ['DJANGO_SETTINGS_MODULE'] = 'pars_bot.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from Users.models import Users, Channels, SendMessages
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

bot = telebot.TeleBot('BOT_TOKEN')
API_ID = 'API_ID'
API_HASH = 'API_HASH'
API_PHONE = 'API_PHONE'
chat = 'INT_CHAT_ID'

client = TelegramClient('parser', api_id=API_ID, api_hash=API_HASH, system_version="4.16.30-vxCUSTOM")
client.start(phone=API_PHONE)


async def get_full(id, client):
    return await client(GetFullUserRequest(id))


async def check_targets_and_stop_word(text, targets_word, stop_words):
    text = text.lower()
    for i in stop_words:
        if i.lower() in text:
            return False
    for i in targets_word:
        a = len(i)
        for f in i:
            if f.lower() in text:
                a -= 1
        if a == 0:
            return True
    return False


async def main():
    while True:
        urls = Channels.objects.all()
        for channel in urls:
            targets_word = []
            stop_words = channel.stop_word.split('|')
            for i in channel.target_word.split('&'):
                targets_word.append(i.split('|'))
            url = channel.channel_url
            print(url)
            channel_1 = await client.get_entity(url)
            await get_messages(channel_1, channel, client, targets_word, stop_words)


async def get_messages(channel, channel_1, client, targets_word, stop_words):
    offset_msg = 0
    limit_msg = 50
    finish_check_message = True
    a = True

    while finish_check_message:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=0,
            hash=0))
        if not history.messages:
            break
        messages = history.messages
        if not channel_1.in_use:
            channel_1.in_use = True
            channel_1.last_message = messages[0].id - 50
            c = channel_1.last_message
            channel_1.save()
        elif channel_1.in_use and a:
            c = channel_1.last_message
            channel_1.last_message = messages[0].id
            channel_1.save()
            a = False
        for message in messages:
            text = message.message
            if await check_targets_and_stop_word(text, targets_word, stop_words) and not SendMessages.objects.filter(
                    text=text):
                SendMessages.objects.create(
                    text=text,
                )
                await client.forward_messages(chat, message)
            if message.id <= c:
                finish_check_message = False
                break
        offset_msg = messages[-1].id


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    message_id = call.message.id
    chat_id = call.message.chat.id
    if call.message:
        data = call.data
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass
        if data.split('|')[0] == 'approve':
            month = int(data.split('|')[1])
            id = data.split('|')[2]
            user = Users.objects.get(tg_id=id)
            user.end_subscription = datetime.date.today() + datetime.timedelta(30 * month)
            user.subscription = True
            user.save()
            bot.approve_chat_join_request(chat_id=chat, user_id=id)


def subscribe(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    one_month = types.LabeledPrice(label='Подписка на 1 месяц', amount=int(600) * 100)
    three_month = types.LabeledPrice(label='Подписка на 1 месяц', amount=int(1500) * 100)
    a = bot.create_invoice_link(title='Подписка на один месяц', description='Подписка на один месяц', currency='rub',
                                prices=[one_month],
                                provider_token='410694247:TEST:eb41a4f2-318a-4c60-a7e1-3fffa4e401b3',
                                payload='test-invoice-payload')
    b = bot.create_invoice_link(title='Подписка на три месяца', description='Подписка на три месяца', currency='rub',
                                prices=[three_month],
                                provider_token='410694247:TEST:eb41a4f2-318a-4c60-a7e1-3fffa4e401b3',
                                payload='test-invoice-payload', )
    pay1 = types.InlineKeyboardButton(text='Купить подписку на 1 месяц', url=a)
    pay2 = types.InlineKeyboardButton(text='Купить подписку на 2 месяца', url=b)
    markup.add(pay1, pay2)
    bot.send_message(chat_id=user_id, text='Купить подписку', reply_markup=markup)


def pay_yoo_money(chat_id):
    pay1 = Quickpay(
        receiver="410019014512803",
        quickpay_form="shop",
        targets="one_months",
        paymentType="SB",
        sum=600,
        label=str(chat_id)
    )
    pay2 = Quickpay(
        receiver="410019014512803",
        quickpay_form="shop",
        targets="three_months",
        paymentType="SB",
        sum=1100,
        label=str(chat_id)
    )
    pay3 = Quickpay(
        receiver="410019014512803",
        quickpay_form="shop",
        targets="six_months",
        paymentType="SB",
        sum=1500,
        label=str(chat_id)
    )
    markup = types.InlineKeyboardMarkup()
    pay1 = types.InlineKeyboardMarkup('Подписка на один месяц', url=pay1.redirected_url)
    pay2 = types.InlineKeyboardMarkup('Подписка на три месяца', url=pay2.redirected_url)
    pay3 = types.InlineKeyboardMarkup('Подписка на шесть месяцев', url=pay3.redirected_url)
    markup.add(pay1, pay2, pay3)
    bot.send_message(chat_id=chat_id, text='Подписка', reply_markup=markup)


def check_pay_card(message, chat_id):
    text = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    user = Users.objects.get(chat_id=chat_id)
    approve1 = types.InlineKeyboardButton(text='Одобрить 1 месяц', callback_data=f'approve|1|{user.tg_id}')
    approve2 = types.InlineKeyboardButton(text='Одобрить 2 месяца', callback_data=f'approve|2|{user.tg_id}')
    approve3 = types.InlineKeyboardButton(text='Одобрить 3 месяца', callback_data=f'approve|3|{user.tg_id}')
    cancel = types.InlineKeyboardButton(text='Отказать', callback_data=f'cancel|{user.tg_id}')
    markup.add(approve1, approve2, approve3, cancel)
    admins = Users.objects.filter(is_admin=True)
    for admin in admins:
        bot.send_message(chat_id=admin.tg_id, text=f'{user.tg_id} Перевел оплату на вашу карту. Его ФИО: {text}',
                         reply_markup=markup)
    bot.send_message(chat_id=chat_id, text='')


def pay_card(chat_id):
    msg = bot.send_message(chat_id=chat_id,
                           text='Переведите оплату на этот номер телефона и скиньте ФИО того, кто переводил в этот чат\n\n'
                                '600 рблей - месяц\n'
                                '1100 рублей - 2 месяца\n'
                                '1600 рублей - 3 месяца')
    bot.register_next_step_handler(msg, check_pay_card, chat_id)


@bot.chat_join_request_handler()
def main(message: telebot.types.ChatJoinRequest):
    chat_id = message.chat.id
    try:
        Users.objects.get(chat_id=chat_id)
    except Users.DoesNotExist:
        Users.objects.create(chat_id=chat_id, username=message.from_user.username)
    markup = types.InlineKeyboardMarkup()
    pay1 = types.InlineKeyboardMarkup('Опталить в YooMoney', callback_data='yoomoney')
    pay2 = types.InlineKeyboardButton('Оплатить переводом на карту', callback_data='card')
    markup.add(pay1, pay2)
    msg = bot.send_message(message.user_chat_id, text="Подписка", reply_markup=markup)


def check_subscribe():
    print(2)
    while True:
        users = Users.objects.filter(subscription=True)
        for i in users:
            if i.check_subscription():
                i.subscription = False
                i.save()
        sleep(60 * 60 * 24)


def polling_process():
    print(1)
    bot.polling(none_stop=True)


def check_pay_yoomoney():
    client_yoominey = Client()
    while True:
        users = Users.objects.filter(is_pay=True)
        for i in users:
            for f in range(10):
                history = client.operation_history(label=i.tg_id)
                for operation in history.operations:
                    if operation.status == 'success':
                        if operation.amount == 600:
                            month = 1
                        elif operation.amount == 1100:
                            month = 2
                        elif operation.amount == 1600:
                            month = 3
                        i.is_pay = False
                        i.subscription = True
                        i.end_subscription = datetime.date.today() + datetime.timedelta(30 * month)
                        bot.approve_chat_join_request(chat_id=chat, user_id=i.tg_id)
                        i.save()
        sleep(30)


if __name__ == '__main__':
    polling_thread = threading.Thread(target=polling_process)
    polling_thread.start()
    check_subscribe_thread = threading.Thread(target=check_subscribe)
    check_subscribe_thread.start()
    sleep(0.5)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
