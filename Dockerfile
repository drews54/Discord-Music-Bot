FROM alpine AS localization
WORKDIR /root/
RUN apk --no-cache add gettext
COPY locale/ locale/
RUN msgfmt -o locale/ru/LC_MESSAGES/Discord-Music-Bot.mo locale/ru/LC_MESSAGES/Discord-Music-Bot.po \
 && rm locale/ru/LC_MESSAGES/Discord-Music-Bot.po
RUN msgfmt -o locale/en/LC_MESSAGES/Discord-Music-Bot.mo locale/en/LC_MESSAGES/Discord-Music-Bot.po \
 && rm locale/en/LC_MESSAGES/Discord-Music-Bot.po

FROM python:3.8.0a3-slim
WORKDIR /usr/src/app/
COPY --from=localization /root/locale/ locale/

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

COPY cogs/ cogs/
COPY bot.py .

CMD ["python","bot.py"]
