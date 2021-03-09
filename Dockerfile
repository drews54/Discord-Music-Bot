FROM python:3

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg locales
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy locale files to the system folder
COPY locale/ /usr/share/locale

WORKDIR /usr/src/app
COPY cogs/ bot.py ./

CMD ["python", "bot.py"]
