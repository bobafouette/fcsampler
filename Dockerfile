FROM python:3

RUN apt-get update && \
    apt-get install ffmpeg -y && \

RUN mkdir /opt/fcsampler
WORKDIR /opt/fcsampler
COPY ./bot.py ./
COPY ./requirement.txt ./
COPY ./templates ./templates
COPY ./static ./static
COPY ./token.secret ./ressources/
COPY ./audio ./ressources/audio/

RUN pip install -r requirement.txt

ENV SOUND_PATH '/opt/fcsampler/ressources/audio'
ENV TOKEN_PATH '/opt/fcsampler/ressources/token.secret'
ENV TEMPLATES_PATH '/opt/fcsampler/templates/'
EXPOSE 5000
CMD python ./bot.py bot
