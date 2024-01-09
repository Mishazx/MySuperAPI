from django.db import IntegrityError
from django.http import JsonResponse
from django.views import View
from django.conf import settings

from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token

from telebot import TeleBot, types

from YandexAPI.models import Device, OAuthKey
from YandexAPI.utils import control_device, get_reconnect_device, register_allDevice

from .keyboard import create_DeviceKeyboard, create_MainKeyboard, create_SettingsKeyboard, create_DevicesKeyboard

from .utils import create_token_for_user


token = settings.TELEGRAM_BOT_TOKEN
url_domain = settings.DOMAIN_URL


bot = TeleBot(token)
url_tg_webhook = f'{url_domain}/tg/webhook/'
bot.set_webhook(url=url_tg_webhook)


class UpdateBot(View):
    def post(self, request):
        try:
            json_str = request.body.decode('UTF-8')
            update = types.Update.de_json(json_str)
            bot.process_new_updates([update])

            return JsonResponse({'code': 200})
        except Exception as e:
            print(f"Error processing update: {e}")
            return JsonResponse({'code': 500, 'error': str(e)})


# Function start bot
@bot.message_handler(commands=['start'])
def start_message(message):
    text = '<b>Бот успешно запущен!</b>\n\n'
    text += "Чтобы начать использовать бота и настроить его нажмите '🖊️ Начать', .\n\n"
 
    keyboard = types.InlineKeyboardMarkup()
    key_begin = types.InlineKeyboardButton(text='🖊️ Начать', callback_data='runbot')
    keyboard.add(key_begin)
 
    bot.send_message(message.chat.id, text=text, reply_markup=keyboard, parse_mode='HTML')        
    
    
# Register user on the System
@bot.callback_query_handler(func=lambda call: call.data == 'runbot')
def handle_begin_callback(call):
    try:
        username = call.from_user.username
        first_name = call.from_user.first_name
        last_name = call.from_user.last_name
        last_name = last_name if last_name is not None else ''

        try:
            user, created = User.objects.get_or_create(username=username, first_name=first_name, last_name=last_name)
        except IntegrityError:
            user = User.objects.get(username=username)
            created = False
            
        create_token_for_user(call.from_user.username)
        
        if created:
            print(f'Пользователь (user) {username} был успешно создан.')
        else:
            print('Пользователь не создался')
            
        keyboard = create_MainKeyboard()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f'Доброго {username}',reply_markup=keyboard)
       
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка: {e}")
        import traceback
        bot.send_message(call.message.chat.id, f'{traceback.format_exc()}')


# Function re-register device yandex
@bot.message_handler(func=lambda message: "Перерегистрировать все устройства" in message.text)
def settingsMenu(message):
    try:
        username = message.chat.username
        user = User.objects.get(username=username)     
        Device.objects.filter(user=user).delete()
        bot.send_message(message.chat.id, f"Устройства удалены")
        output = register_allDevice(username)
        if output == 'Success':
            bot.send_message(message.chat.id, f'Устройства успешно добавлены')
        else:
            bot.send_message(message.chat.id, output)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")    


# Function handle 'Main menu"
@bot.message_handler(func=lambda message: 'Главное меню' in message.text)
def mainMenu(message):
    try:
        keyboard = create_MainKeyboard()
        bot.send_message(message.chat.id, f'Вы находитесь в главном меню', reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


# Function handle 'Settings menu'
@bot.message_handler(func=lambda message: 'Настройки' in message.text)
def settingsMenu(message):
    try:
        keyboard = create_SettingsKeyboard(message.chat.username)
        bot.send_message(message.chat.id, f'Вы находитесь в меню настроек',reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

from .handler.MenuDevices import *