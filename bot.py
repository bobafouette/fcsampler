import discord
import json
import os
import re
import time

from discord.ext import commands
from flask import Flask
from flask import render_template
from functools import partial
from threading import Thread

YADUMONDE = 240872092965404693
BOTMUSIC = 690959439842508863
LAGALETTE = 240974139572224010

class Sample(object):

    def __init__(self, name, path):
        self.name = name
        self.path = path
        index_regex = re.compile(r"(?P<index>[0-9]+)\s(?P<shortname>.+)")
        index_match = re.match(index_regex, self.name)
        if not index_match:
            raise ValueError('Not a valid sound name: {}. Could not extract index'.format(self.name))
        self.index = int(index_match.group('index'))
        self.shortname = index_match.group('shortname')
        if len(self.shortname) > 30:
            self.shortname = self.shortname[:30] + '...'

    def __eq__(self, sample):
        return self.index == sample.index

    def __ne__(self, sample):
        return self.index != sample.index

    def __lt__(self, sample):
        return self.index < sample.index

    def __le__(self, sample):
        return self.index <= sample.index

    def __gt__(self, sample):
        return self.index > sample.index

    def __ge__(self, sample):
        return self.index >= sample.name

class JukeBox(object):

    def __init__(self, sounds_path):

        self.sounds_path = sounds_path
        if not os.path.isdir(sounds_path):
            raise ValueError('{} is not a folder or does not exists'.format(self.sounds_path))

        self.playlist = []
        sounds_files = os.listdir(self.sounds_path)
        for i in range(len(sounds_files)):
            sound_file = sounds_files[i]
            if sound_file.startswith('.'):
                continue
            sample = Sample(sound_file, os.path.join(self.sounds_path, sound_file))
            self.playlist.append(sample)

        self.playlist.sort()

    def getlist(self):
        return [sound.name for sound in self.playlist]

    def __getitem__(self, index):
        return self.playlist[index-1]

class FcSampler(commands.Bot):

    def __init__(self):
        super(FcSampler, self).__init__(command_prefix="$fc ")

    def play(self, sample):
        print(sample.name)
        for voice_client in self.voice_clients:
            if voice_client.is_playing():
                continue
            voice_client.play(discord.FFmpegPCMAudio(sample.path))

fcSampler = FcSampler()
jukebox = JukeBox(os.environ.get('SOUND_PATH'))

@fcSampler.event
async def on_ready():
    print('Logged in as')
    print(fcSampler.user.name)
    print(fcSampler.user.id)
    print('------')

@fcSampler.command()
async def join(ctx, *channel_name):
    """Joins a voice channel"""

    channel_name = ' '.join(channel_name)
    for channel in fcSampler.get_all_channels():
        if channel.name == channel_name:
            break
    else:
        channel = ctx.author.voice.channel

    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)

    await channel.connect()

@fcSampler.command()
async def leave(ctx):
    """Leave a voice channel"""

    for client in ctx.bot.voice_clients:
        await client.disconnect()

@fcSampler.command()
async def play(ctx, index):
    sample = jukebox[int(index)]
    fcSampler.play(sample)

@fcSampler.command()
async def list(ctx):
    """Leave a voice channel"""
    sample_names = jukebox.getlist()
    message = ''
    for index in range(len(sample_names)):
        sample_name = sample_names[index]
        message += sample_name + '\n'
        if index + 1 >= len(sample_names):
            await ctx.channel.send(message)
            message = ''
            break
        if (len(message) + len(sample_names[index + 1]) + 1 > 2000):
            await ctx.channel.send(message)
            message = ''

def bot_main():
    with open(os.environ['TOKEN_PATH'], 'r') as token_file:
        token = token_file.read()
    fcSampler.run(token)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('index.html', samples=jukebox.playlist)

@app.route('/play/<index>')
def play_web(index=1):
    print('play')
    sample = jukebox[int(index)]
    fcSampler.play(sample)
    return render_template('index.html', samples=jukebox.playlist)

partial_run = partial(app.run, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
t = Thread(target=partial_run)
t.start()
bot_main()

