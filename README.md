# Discord-Music-Bot

Originally created and named **"Letov"** by @piunov1998  
Docker integration implemented by me, @duha54rus

## Simple deployment

To download and run the latest build of the bot from [Docker Hub](https://hub.docker.com/r/drews54/discord-music-bot), replace placeholders with your token and prefix of choice and execute:

```shell
docker run --volume music:/usr/src/app/music \
-e DISCORD_TOKEN=INSERT_YOUR_TOKEN_HERE \
-e DISCORD_PREFIX=TYPE_YOUR_PREFIX_HERE \
--rm -d drews54/discord-music-bot
```

## Build and run

If you want to build the container yourself:

1. Download the .zip of this branch and extract it
2. Run `docker build -t discord-music-bot .` in the extracted directory
3. Create a text file (for example, name it `.env`) in the same directory, populate it with your discord bot token and chat prefix as shown below:

    ```env
    DISCORD_TOKEN=***********************************************************
    DISCORD_PREFIX="any sequence of symbols"
    LANG=RU or EN
    ```

4. Run `docker run --volume music:/usr/src/app/music --env-file .env --rm -d discord-music-bot`

## Building localization files

To run the bot directly on your system (without Docker), you will have to prebuild .mo files for localization to work (currently only works on Linux):

```shell
msgfmt -o locale/ru/LC_MESSAGES/Discord-Music-Bot.mo locale/ru/LC_MESSAGES/Discord-Music-Bot.po
msgfmt -o locale/en/LC_MESSAGES/Discord-Music-Bot.mo locale/en/LC_MESSAGES/Discord-Music-Bot.po
```
