import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request as flask_request, redirect, url_for, flash, jsonify
import os
from web_tools import *
from file_tools import *
from pid_tools import *
from dotenv import load_dotenv


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

load_dotenv()
secret_key = os.getenv('SECRET_KEY')
app.secret_key = secret_key


@app.route('/')
def index():
    return render_template('test.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)