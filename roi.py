# Nikolay Chernov, May 2020

import http.client
import urllib.parse
import json
import time
import configparser


def get_time_str():
    return time.strftime("%Y-%m-%d %H:%M")


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


def save_results_str(filename, results_str):
    file = open(filename, "a")
    file.write(results_str)
    file.write("\n")
    file.close()


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
    str_to_write = time.strftime("%Y-%m-%d %H:%M") + ',' + str(number_of_yes) + ',' + str(number_of_no)
    save_results_str("roi-" + petition + ".csv", str_to_write)
    hour = time.localtime(time.time()).tm_hour
    if True or hour == 11:
        msg = 'Yes: ' + str(number_of_yes) + '; No: ' + str(number_of_no)
        send_telegram_msg(bot_token, chat_id, msg)
else:
    log_error("Something was wrong...")
