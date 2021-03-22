import discord
import os
import re

from discord.ext import commands

from .utils import Singleton


class Sample(object):

    @staticmethod
    def index_match(filename):
        index_regex = re.compile(r"(?P<index>[0-9]+)\s(?P<shortname>.+)")
        return re.match(index_regex, filename)

    def __init__(self, name, path):
        self.name = name
        self.path = path
        index_match = self.index_match(self.name)
        if not index_match:
            message = 'Not a valid sound name: {}. Could not extract index'.format(self.name)
            raise ValueError(message)
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
        self.load()

    def getlist(self):
        return [sound.name for sound in self.playlist]

    def __getitem__(self, index):
        return self.playlist[index-1]

    def load(self):
        self.playlist = []
        sounds_files = os.listdir(self.sounds_path)
        for i in range(len(sounds_files)):
            sound_file = sounds_files[i]
            if sound_file.startswith('.'):
                continue
            sample = Sample(sound_file, os.path.join(self.sounds_path, sound_file))
            self.playlist.append(sample)
        self.playlist.sort()


class FcSampler(commands.Bot, metaclass=Singleton):

    def __init__(self, jukebox):
        super(FcSampler, self).__init__(command_prefix="$fc ")
        self.jukebox = jukebox
        self.add_command(leave)
        self.add_command(join)
        self.add_command(play)
        self.add_command(list_samples)


    def play(self, sample):
        print(sample.name)
        for voice_client in self.voice_clients:
            voice_client.play(discord.FFmpegPCMAudio(sample.path))


@commands.command()
async def join(ctx, *channel_name):
    """Joins a voice channel"""

    channel_name = ' '.join(channel_name)
    for channel in ctx.bot.get_all_channels():
        if channel.name == channel_name:
            break
    else:
        channel = ctx.author.voice.channel

    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)

    await channel.connect()


@commands.command()
async def leave(ctx):
    """Leave a voice channel"""

    for client in ctx.bot.voice_clients:
        await client.disconnect()


@commands.command()
async def play(ctx, index):
    sample = ctx.bot.jukebox[int(index)]
    ctx.bot.play(sample)


@commands.command()
async def list_samples(ctx):
    """Leave a voice channel"""
    sample_names = ctx.bot.jukebox.getlist()
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
