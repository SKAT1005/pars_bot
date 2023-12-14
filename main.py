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

os.environ['DJANGO_SETTINGS_MODULE'] = 'pars_bot.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from Users.models import Users, Channels, SendMessages
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

bot = telebot.TeleBot('6701302705:AAG089UoJziV2Kg6WPoN842N00BWqA5I8oo')
API_ID = '25553568'
API_HASH = '30576b6fff3d7c61e80bd4cec380d76f'
API_PHONE = '+996999660415'

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
        for message in messages[1:]:
            text = message.message
            if await check_targets_and_stop_word(text, targets_word, stop_words) and not SendMessages.objects.filter(text=text):
                SendMessages.objects.create(
                    text=text,
                )
                if channel_1.need_send_contacts:
                    id = message.to_dict()
                    id = id['from_id']['user_id']
                    username = await get_full(id, client)
                    username = f'@{username.users[0].username}'
                    text = text + f"\n\nКонтакты для связи: {username}"
                for user in Users.objects.filter(subscription=True):
                    bot.send_message(chat_id=user.tg_id, text=text)
            if message.id <= c:
                finish_check_message = False
                break
        offset_msg = messages[-1].id


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    try:
        bot.delete_message(chat_id=user_id, message_id=message.id)
    except Exception:
        pass
    try:
        Users.objects.get(tg_id=user_id)
    except Exception:
        Users.objects.create(
            tg_id=user_id,
            username=message.from_user.username
        )
    menu(chat_id=user_id)


def menu(chat_id):
    subscribtion = len(Users.objects.filter(subscription=True))
    markup = types.InlineKeyboardMarkup()
    user = Users.objects.get(tg_id=chat_id)
    if not user.subscription:
        button1 = types.InlineKeyboardButton(text='Купить подписку', callback_data='subscribe')
        markup.add(button1)
    if user.is_admin:
        button2 = types.InlineKeyboardButton(text='Админ-панель', callback_data='admin')
        markup.add(button2)
    bot.send_message(
        text=f'Добро пожаловать в нашего бота. Уже более {subscribtion} швейных производств получают сообщения мгновенно!',
        chat_id=chat_id, reply_markup=markup)


def pagination(markup, page, pagination_start, pagination_end, counter, category=None):
    if pagination_start == 0 and pagination_end < counter:
        next_page = types.InlineKeyboardButton('Следующая страница',
                                               callback_data=f'next_page|{page}|{pagination_start}|{pagination_end}|{category}')
        markup.add(next_page)
    elif pagination_start > 0 and pagination_end >= counter:
        last_page = types.InlineKeyboardButton('Предыдущая страница',
                                               callback_data=f'last_page|{page}|{pagination_start}|{pagination_end}|{category}')
        markup.add(last_page)
    elif pagination_start > 0 and pagination_end < counter:
        next_page = types.InlineKeyboardButton('Следующая страница',
                                               callback_data=f'next_page|{page}|{pagination_start}|{pagination_end}|{category}')
        last_page = types.InlineKeyboardButton('Предыдущая страница',
                                               callback_data=f'last_page|{page}|{pagination_start}|{pagination_end}|{category}')
        markup.add(last_page, next_page)


def subscribe(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    one_month = types.LabeledPrice(label='Подписка на 1 месяц', amount=int(600) * 100)
    three_month = types.LabeledPrice(label='Подписка на 1 месяц', amount=int(1500) * 100)
    a = bot.create_invoice_link(title='Подписка на один месяц', description='Подписка на один месяц', currency='rub',
                                prices=[one_month], provider_token='410694247:TEST:eb41a4f2-318a-4c60-a7e1-3fffa4e401b3',
                                payload='test-invoice-payload')
    b = bot.create_invoice_link(title='Подписка на три месяца', description='Подписка на три месяца', currency='rub',
                                prices=[three_month], provider_token='410694247:TEST:eb41a4f2-318a-4c60-a7e1-3fffa4e401b3',
                                payload='test-invoice-payload', )
    pay1 = types.InlineKeyboardButton(text='Купить подписку на 1 месяц', url=a)
    pay2 = types.InlineKeyboardButton(text='Купить подписку на 2 месяца', url=b)
    markup.add(pay1, pay2)
    bot.send_message(chat_id=user_id, text='Купить подписку', reply_markup=markup)


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_query,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    print(message)
    user = Users.objects.get(tg_id=message.chat.id)
    user.subscription = True
    if message.successful_payment.total_amount == 600*100:
        user.end_subscription = datetime.date.today() + datetime.timedelta(30)
    elif message.successful_payment.total_amount == 1500*100:
        user.end_subscription = datetime.date.today() + datetime.timedelta(90)
    user.save()
    bot.send_message(message.chat.id, 'Оплата прошла успешно! Ваша подписка подключена')
    menu(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    message_id = call.message.id
    chat_id = call.message.chat.id
    user = Users.objects.get(tg_id=call.from_user.id)
    if call.message:
        data = call.data
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass
        if data == 'admin':
            admin_panel(chat_id)

        elif data == 'subscribe':
            subscribe(user_id=chat_id)


async def main_wrapper():
    await main()


async def polling_wrapper():
    bot.polling(none_stop=True)


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


if __name__ == '__main__':
    polling_thread = threading.Thread(target=polling_process)
    polling_thread.start()
    check_subscribe_thread = threading.Thread(target=check_subscribe)
    check_subscribe_thread.start()
    sleep(3)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
