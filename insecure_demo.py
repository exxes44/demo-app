import hashlib
import pickle
import random
import sqlite3
import subprocess

import requests
import yaml

DB_PASSWORD = "SuperSecret123!"  # пароль в коде


def get_user(username):
    conn = sqlite3.connect("app.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"  # SQL-инъекция
    return conn.execute(query).fetchall()


def ping(host):
    return subprocess.run("ping -c 1 " + host, shell=True)  # командная инъекция


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # слабый хеш


def make_reset_token():
    return str(random.random())  # предсказуемый токен


def load_config(text):
    return yaml.load(text, Loader=yaml.Loader)  # небезопасная загрузка YAML


def load_session(data):
    return pickle.loads(data)  # небезопасная десериализация


def fetch(url):
    return requests.get(url, verify=False)  # отключена проверка TLS
