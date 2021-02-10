FROM python:3.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Optional build-time argument for installing debuggers into the image
ARG BuildMode

# Install pip requirements and ffmpeg
RUN apt-get update && apt-get install -y ffmpeg
COPY requirements.txt .
# RUN if [ "$BuildMode" = "debug" ] ; \
#     then echo "debugpy" >> requirements.txt ; \
#     fi
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /usr/src/app
COPY . .

CMD ["python", "bot.py"]
