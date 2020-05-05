FROM python:3

RUN pip install discord.py
RUN apt-get update
RUN apt-get install ffmpeg -y
RUN pip install PyNaCl

COPY ./bot.py work/
RUN mkdir /work/ressources
COPY ./token.secret work/ressources/
COPY ./audio work/ressources/audio/
# VOLUME /work/ressources
ENV SOUND_PATH '/work/ressources/audio'
ENV TOKEN_PATH '/work/ressources/token.secret'
CMD python work/bot.py bot
