FROM alpine AS localization
RUN apk add --no-cache gettext
COPY locale/ locale/

WORKDIR /locale/en/LC_MESSAGES/
RUN msgfmt --check --output-file Discord-Music-Bot.mo Discord-Music-Bot.po && rm Discord-Music-Bot.po

WORKDIR /locale/ru/LC_MESSAGES/
RUN msgfmt --check --output-file Discord-Music-Bot.mo Discord-Music-Bot.po && rm Discord-Music-Bot.po

FROM python:3
WORKDIR /opt/bot/

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements and ffmpeg
RUN apt-get --quiet update && apt-get install --quiet --assume-yes --no-install-recommends ffmpeg
COPY requirements.txt ./
RUN pip install --quiet --no-cache-dir -r requirements.txt && rm requirements.txt

COPY --from=localization locale/ locale/
COPY cogs/ cogs/
COPY bot.py ./

CMD ["python","bot.py"]
