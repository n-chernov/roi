# Nikolay Chernov, May 2020

import http.client
import urllib.parse
import json
import time
import configparser
import requests
import csv
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


time_format = '%Y-%m-%d %H:%M'
chart_filename = 'graph.png'


def get_time_str():
    return time.strftime(time_format)


def log_error(message):
    error_log = open("roi-errors.log", "a")
    error_log.write(get_time_str() + " - " + message + "\n")
    error_log.close()


def load_petition(petition):
    attempts = 3
    success = False
    while attempts > 0 and not success:
        try:
            conn = http.client.HTTPSConnection("www.roi.ru")
            url="/api/petition/" + petition + ".json"
            conn.request("GET", url)
            resp = conn.getresponse()
            success = (resp.status == 200)
            if success:
                return resp.read().decode('UTF-8')
            else:
                log_error("Response was " + str(resp.status) + resp.reason)
        except Exception as e:
            log_error("Exception has been caught" + "\n" + str(e))
        attempts = attempts - 1
        time.sleep(10)
    return ""


def send_telegram_msg(token, chat_id, message):
    try:
        conn = http.client.HTTPSConnection("api.telegram.org")
        encoded_msg = urllib.parse.quote(message)
        url = '/bot' + token + '/sendMessage?chat_id=' + chat_id + '&text=' + encoded_msg
        conn.request("GET", url)
        resp = conn.getresponse()
        if resp.status != 200:
            log_error('Failed to send telegram message')
    except Exception as e:
        log_error("Exception has been caught" + "\n" + str(e))


def send_telegram_file(token, chat_id, file_name):
    try:
        url = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + chat_id
        files = [('document', (file_name, open(file_name, 'rb')))]
        resp = requests.post(url, files=files)
        if resp.status_code != 200:
            log_error('Failed to send file')
            log_error(str(resp))
            log_error(resp.text)
    except Exception as e:
        log_error("Exception has been caught" + "\n" + str(e))


def send_telegram_photo(token, chat, file_name):
    try:
        url = 'https://api.telegram.org/bot' + token + '/sendPhoto?chat_id=' + chat
        files = [('photo', (file_name, open(file_name, 'rb')))]
        resp = requests.post(url, files=files)
        if resp.status_code != 200:
            log_error('Failed to send photo')
            log_error(str(resp))
            log_error(resp.text)
    except Exception as e:
        log_error("send_telegram_photo: exception has been caught" + "\n" + str(e))


def save_results_str(filename, results_str):
    file = open(filename, "a")
    file.write(results_str)
    file.write("\n")
    file.close()


def draw_chart(csv_file_name, chart_filename):
    x = []
    yes = []
    no = []
    try:
        with open(csv_file_name, 'r') as csvfile:
            plots = csv.reader(csvfile, delimiter=',')
            for row in plots:
                datetime_obj = datetime.datetime.strptime(str(row[0]), time_format)
                x.append(datetime_obj)
                yes.append(int(row[1]))
                no.append(int(row[2]))
        # Generate the figure **without using pyplot**.
        fig = Figure()
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        ax.plot(x, yes, 'g', label="За")
        ax.plot(x, no, 'r', label="Против")
        ax.tick_params(axis='x', rotation=20)
        ax.legend()
        ax.grid(True)
        ax.set_title('Ход голосования по инициативе №47Ф63007')
        fig.savefig(chart_filename)
    except Exception as e:
        log_error("draw_chart: exception has been caught" + "\n" + str(e))


config = configparser.ConfigParser()
config.read('config.ini')
petition = config['config']['petition']
bot_token = config['config']['bot_token']
chat_id = config['config']['chat_id']

petition_data = load_petition(petition)
if len(petition_data) > 0:
    petition_json = json.loads(petition_data)
    number_of_yes = petition_json["data"]["vote"]["affirmative"]
    number_of_no = petition_json["data"]["vote"]["negative"]
    str_to_write = time.strftime(time_format) + ',' + str(number_of_yes) + ',' + str(number_of_no)
    results_filename = "roi-" + petition + ".csv"
    save_results_str(results_filename, str_to_write)

    cur_time = time.localtime(time.time())
    hour = cur_time.tm_hour
    day = cur_time.tm_wday
    if hour == 11:
        msg = 'Yes: ' + str(number_of_yes) + '; No: ' + str(number_of_no)
        send_telegram_msg(bot_token, chat_id, msg)
        if day == 0:
            send_telegram_file(bot_token, chat_id, results_filename)
            draw_chart(results_filename, chart_filename)
            send_telegram_photo(bot_token, chat_id, chart_filename)
else:
    log_error("Something was wrong...")
