import telebot
import sqlite3 as sqlite
import re
import config as cfg
from peewee import *
import bot_strings as bs
from telebot import types
from datetime import datetime, date, time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import linecache
import sys

botname = '@Bistriy_Design_bot'
token = '321912583:AAH5DhO3wq7-8T4QRZXoHL2eR7lO8TeY0gs'
db_name = 'design_order_bot'
bot = telebot.TeleBot(cfg.token)
months = {1:'Январь', 2:'Февраль', 3:'Март', 4:'Апрель', 5:'Май', 6:'Июнь', 7:'Июль', 8:'Август', 9:'Сентябрь', 10:'Октябрь', 11:'Ноябрь', 12:'Декабрь'}
weekdays = {1:'Понедельник', 2:'Вторник', 3:'Среда', 4:'Четверг', 5:'Пятница', 6:'Суббота', 7:'Воскресенье'}

db = SqliteDatabase('bot.db')

duplicate = [268653382, 5844335, -1001117829937]
bd_email = "Bistriy_Design@mail.ru"


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


class User(Model):
	user_id = IntegerField(unique = True, primary_key = True)
	username = CharField(null=True)
	first_name = CharField(null=True)
	last_name = CharField(null=True)
	step = IntegerField()
	task = TextField(null=True)
	deadline = CharField(null=True)
	budget = CharField(default=0)
	email = CharField(null=True)
	mobile = CharField(null=True)

	class Meta:
		database = db

class SentOrder(Model):
	order_id = IntegerField(unique = True, primary_key = True)
	user_id = IntegerField(null=True)
	username = CharField(null=True)
	first_name = CharField(null=True)
	last_name = CharField(null=True)
	task = TextField(null=True)
	deadline = CharField(null=True)
	budget = CharField(default=0)
	email = CharField(null=True)
	mobile = CharField(null=True)

	class Meta:
		database = db

class Oferta(Model):
	oferta_id = IntegerField(unique = True, primary_key = True)
	link = CharField(null = True)

	class Meta:
		database = db

@bot.message_handler(commands = ['init'])
def init(message):
	#db.connect()
	try:
		db.create_table(User)
		db.create_table(SentOrder)
		db.create_table(Oferta)
	except:
		print("Error during table create")
		PrintException()
	user = User.create(user_id = message.chat.id, username = message.chat.username, step = 1)

@bot.message_handler(commands = ['add_oferta'])
def add_oferta(message):
	sender_id = message.chat.id
	oferta = Oferta.get(Oferta.oferta_id == 1)
	link = re.sub(r'/add_oferta ', '', message.text)
	if re.match(r'^(https?:\/\/)?([\w\.]+)\.([a-z]{2,6}\.?)(\/[\w\.]*)*\/?$', link):
		oferta.link = link
		oferta.save()
		bot.send_message(sender_id, bs.oferta_confirmed)
	else:
		bot.send_message(sender_id, bs.oferta_rejected)


@bot.message_handler(commands = ['reboot'])
def reboot(message):
	try:
		user = User.get(User.user_id == message.chat.id)
		user.delete_instance()
	except:
		print("Error")
		PrintException()

@bot.message_handler(commands = ['start'])
def start(message):
	sender_id = message.chat.id
	first_name = message.chat.first_name
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	checkout_button = types.KeyboardButton(bs.checkout)
	markup.add(checkout_button)
	bot.send_message(sender_id, bs.greeting.format(first_name), reply_markup=markup)



def greeting(message):
	try:
		user = User.create(user_id = message.chat.id, username = message.chat.username, first_name = message.chat.first_name, last_name = message.chat.last_name, step = 1)
	except:
		user = User.get(User.user_id == message.chat.id)
		user.step = 1;
		user.save()
	first_name = message.chat.first_name
	sender_id = message.chat.id
	user = User.select().where(User.user_id == sender_id).get()
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	cancel_button = types.KeyboardButton(bs.cancel)
	markup.add(cancel_button)
	bot.send_message(message.chat.id, bs.task, reply_markup=markup)
	user.step += 1
	user.save()

def deadline(sender_id, message):
	user = User.select().where(User.user_id == sender_id).get()
	if message.text != bs.back:
		user.task = message.text
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	back_button = types.KeyboardButton(bs.back)
	markup.add(back_button)
	cancel_button = types.KeyboardButton(bs.cancel)
	markup.add(cancel_button)
	bot.send_message(sender_id, bs.deadline, reply_markup=markup)
	user.step += 1
	user.save()

def budget(sender_id, message):
	user = User.select().where(User.user_id == sender_id).get()
	if message.text != bs.back:
		if not re.match(r'\d{1,2}\s+\d{1,2}', message.text):
			bot.send_message(sender_id, bs.deadline_error)
			return True
		else:
			date = message.text
			day = int((re.search(r'^\d+', date)).group(0))
			month = int((re.search(r'\d+$', date)).group(0))
			if int(day) > 31 or int(day) < 1:
				bot.send_message(sender_id, bs.day_error)
				return False
			if int(month) > 12 or int(month) < 1:
				bot.send_message(sender_id, bs.month_error)
				return False
			dt = datetime.now()
			dt = dt.replace(month=month, day=day)
			final_date = str(day)+' {0} ({1})'.format(months[month], weekdays[dt.isoweekday()])
			user.deadline = final_date
			
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
	budget_min_button = types.KeyboardButton(bs.budget_min)
	budget_avg_button = types.KeyboardButton(bs.budget_avg)
	budget_big_button = types.KeyboardButton(bs.budget_big)
	budget_max_button = types.KeyboardButton(bs.budget_max)
	back_button = types.KeyboardButton(bs.back)
	cancel_button = types.KeyboardButton(bs.cancel)
	markup.add(budget_min_button, budget_avg_button, budget_big_button, budget_max_button, back_button, cancel_button)
	bot.send_message(sender_id, bs.budget, reply_markup=markup)
	user.step += 1
	user.save()

def email(sender_id, message):
	user = User.select().where(User.user_id == sender_id).get()
	if message.text != bs.back:
		if message.text == '1':
			message.text = bs.budget_min
		if message.text == '2':
			message.text = bs.budget_avg
		if message.text == '3':
			message.text = bs.budget_big
		if message.text == '4':
			message.text = bs.budget_max
		user.budget = message.text
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	try:
		order =SentOrder.select().where(SentOrder.user_id == sender_id).order_by(-SentOrder.order_id).get()
		accept_button = types.KeyboardButton(bs.accept)
		back_button = types.KeyboardButton(bs.back)
		cancel_button = types.KeyboardButton(bs.cancel)
		markup.add(accept_button)
		markup.add(back_button)
		markup.add(cancel_button)
		bot.send_message(sender_id, bs.your_email.format(order.email), reply_markup=markup)
	except:
		back_button = types.KeyboardButton(bs.back)
		markup.add(back_button)
		bot.send_message(sender_id, bs.email, reply_markup=markup)
	user.step += 1
	user.save()

def mobile(sender_id, message):
	user = User.select().where(User.user_id == sender_id).get()
	if message.text != bs.back:
		if message.text != bs.accept:
			message.text = message.text.strip()
			if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", message.text):
				user.email = message.text
			else:
				bot.send_message(sender_id, bs.email_error)
				return False
		else:
			order =SentOrder.select().where(SentOrder.user_id == sender_id).order_by(-SentOrder.order_id).get()
			user.email = order.email
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	try:
		order =SentOrder.select().where(SentOrder.user_id == sender_id).order_by(-SentOrder.order_id).get()
		accept_button = types.KeyboardButton(bs.accept)
		back_button = types.KeyboardButton(bs.back)
		cancel_button = types.KeyboardButton(bs.cancel)
		markup.add(accept_button)
		markup.add(back_button)
		markup.add(cancel_button)
		bot.send_message(sender_id, bs.your_mobile.format(order.mobile), reply_markup=markup)
	except:
		back_button = types.KeyboardButton(bs.back)
		markup.add(back_button)
		bot.send_message(sender_id, bs.mobile, reply_markup=markup)
	user.step = user.step + 1
	user.save()
	

def rules(sender_id, message):
	user = User.select().where(User.user_id == sender_id).get()
	print('6 user:')
	print(user.mobile)
	oferta = Oferta.select().where(Oferta.oferta_id == 1).get()	
	print('6 oferta:')
	print(oferta.link)
	if message.text != bs.back:
		if message.text != bs.accept:
			if re.match(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{3,10}$', message.text):
				user.mobile = message.text
			else:
				bot.send_message(sender_id, bs.mobile_error)
				return False
		else:
			order =SentOrder.select().where(SentOrder.user_id == sender_id).order_by(-SentOrder.order_id).get()
			user.mobile = order.mobile
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	agreement_button = types.KeyboardButton(bs.agreement)
	back_button = types.KeyboardButton(bs.back)
	cancel_button = types.KeyboardButton(bs.cancel)
	markup.add(agreement_button)
	markup.add(back_button)
	markup.add(cancel_button)
	bot.send_message(sender_id, bs.rules.format(oferta.link), reply_markup=markup, parse_mode="Markdown")
	user.step += 1
	user.save()

def final(sender_id, message):
	user = User.select().where(User.user_id == sender_id).get()
	oferta = Oferta.select().where(Oferta.oferta_id == 1).get()
	if message.text != bs.agreement:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
		back_button = types.KeyboardButton(bs.back)
		markup.add(back_button)
		bot.send_message(sender_id, bs.rules.format(oferta.link), reply_markup=markup, parse_mode="Markdown")
	else:
		order = '''
		Имя: {0} {1} ({2})
		{3}
		Дедлайн: {4}
		Бюджет: {5}
		E-mail: {6}
		тел: {7}
		'''.format(user.first_name, user.last_name, user.username, user.task, user.deadline, user.budget, user.email, user.mobile)

		try:
			send_email(user.email, order)
		except:
			print("Mailing to user error")
			PrintException()

		try:
			send_email(bd_email, order)
		except:
			print("Mailing to dispatcher error")
			PrintException()

		for i in duplicate:
			bot.send_message(i, order)	
		try:
			order = SentOrder.create(user_id = user.user_id, username = user.username, first_name = user.first_name, last_name = user.last_name, task = user.task, deadline = user.deadline, budget = user.budget, email = user.email, mobile = user.mobile)
		except:
			print("Can't save order")
			PrintException()

		markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
		checkout_button = types.KeyboardButton(bs.checkout)
		markup.add(checkout_button)
		bot.send_message(sender_id, bs.thanks, reply_markup=markup)
		user.delete_instance()	


def send_email(address, text):
	fromaddr = "bistriy.design@mail.ru"
	toaddr = address
	mypass = "qazwsx123"
	 
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = bs.design_order
	 
	body = text
	msg.attach(MIMEText(body, 'plain'))
	 
	server = smtplib.SMTP('smtp.mail.ru', 587)
	server.starttls()
	server.login(fromaddr, mypass)
	text = msg.as_string()
	try:
		server.sendmail(fromaddr, toaddr, text)
	except:
		print("Mail send error")
		PrintException()
	server.quit()


@bot.message_handler(content_types=['text'])
def reply(message):
	sender_id = message.chat.id
	first_name = message.chat.first_name
	if message.text == bs.checkout:
		try:
			user = User.select().where(User.user_id == sender_id).get()
			user.delete_instance()
		except:
			print("Error")
			PrintException()
		route(message.chat.id, message, 1)
		return True
	if message.text == bs.cancel:
		user = User.select().where(User.user_id == sender_id).get()
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
		checkout_button = types.KeyboardButton(bs.checkout)
		markup.add(checkout_button)
		bot.send_message(sender_id, bs.greeting.format(first_name), reply_markup=markup)
		user.delete_instance()
		return False
	try:
		user = User.select().where(User.user_id == sender_id).get()
		step = user.step
	except:
		start(message)
		return True
	if message.text == bs.back:
		if step > 0:
			step -= 2
		user.step = step
		user.save()
		route(sender_id, message, step)
		return True
	if message.text == bs.new_order:
		reboot(message)
		return True
	try:
		route(sender_id, message, step)
	except:
		print("Step error")
		PrintException()

def route(sender_id, message, step):
	if step == 0 or step == 1 :
		print('0' + ' ' + '1')
		greeting(message)
	if step == 2:
		print(2)
		deadline(sender_id, message)
	if step == 3:
		print(3)
		budget(sender_id, message)
	if step == 4:
		print(4)
		email(sender_id, message)
	if step == 5:
		print(5)
		mobile(sender_id, message)
	if step == 6:
		print(6)
		rules(sender_id, message)
	if step == 7:
		print(7)
		final(sender_id, message)



if __name__ == '__main__':
	bot.polling(none_stop=True)
