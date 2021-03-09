FROM alpine AS localization
WORKDIR /root/
RUN apk --no-cache add gettext
COPY locale/ru/LC_MESSAGES/Discord-Music-Bot.po .
RUN msgfmt Discord-Music-Bot.po -o Discord-Music-Bot.mo

FROM python:3-slim
WORKDIR /usr/src/app/
COPY --from=localization /root/Discord-Music-Bot.mo ./locale/ru/LC_MESSAGES/

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN rm requirements.txt ./locale/ru/LC_MESSAGES/Discord-Music-Bot.po

CMD ["python", "bot.py"]
