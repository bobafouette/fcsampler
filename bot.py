import discord
import json
import os
import re
import time

from discord.ext import commands
from flask import Flask
from flask import render_template
from flask import Response
from flask import flash, request, redirect, url_for
from functools import partial
from threading import Thread
from werkzeug.utils import secure_filename

from fcsampler.fcbot import FcSampler, JukeBox


UPLOAD_FOLDER = os.environ.get('SOUND_PATH')
ALLOWED_EXTENSIONS = {'mp3'}
jukebox = JukeBox(os.environ.get('SOUND_PATH'))
fcSampler = FcSampler(jukebox)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def bot_main():
    with open(os.environ['TOKEN_PATH'], 'r') as token_file:
        token = token_file.read()
    fcSampler.run(token)


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def hello_world():
    return render_template('index.html', samples=jukebox.playlist)


@app.route('/play/<index>')
def play_web(index=1):
    sample = jukebox[int(index)]
    try:
        fcSampler.play(sample)
    except discord.ClientException:
        return Response('Already playing audio', status=409)
    return Response('Playing Sound {}'.format(sample.shortname), status=202)


@app.route('/reload')
def reload():
    jukebox.load()
    return redirect(url_for('hello_world'))


@app.route('/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file_uploaded = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file_uploaded.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if not file_uploaded or not allowed_file(file_uploaded.filename):
            return redirect(request.url)

        filename = secure_filename(file_uploaded.filename)
        match_filename = Sample.index_match(filename)
        if match_filename:
            index = match_filename.group('index')
            if index == len(jukebox.playlist):
                file_uploaded.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(request.url)
            filename = match_filename.group('shortname')
        filename = str(len(jukebox.playlist) + 1) + ' ' + filename
        file_uploaded.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        jukebox.load()
        return redirect(url_for('hello_world'))


partial_run = partial(app.run, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
t = Thread(target=partial_run)
t.start()
bot_main()
