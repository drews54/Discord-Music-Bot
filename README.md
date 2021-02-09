# Discord-Music-Bot

Originally created and named **"Letov"** by @piunov1998  
Docker integration implemented by me, @duha54rus

## Simple deployment

To download and run the latest build of the bot from [Docker Hub](https://hub.docker.com/r/drews54/discord-music-bot), execute:
```shell
    docker run -d -v music:/usr/src/app/music -e DISCORD_TOKEN=INSERT_YOUR_TOKEN_HERE -e DISCORD_PREFIXES=TYPE_PREFIXES_HERE --rm drews54/discord-music-bot
```
## Build and deploy

If you want to build the container yourself:
1. Download the .zip of `Docker` branch and extract it
2. Run `docker build -t discord-music-bot .` in the extracted directory
3. Create a text file in the same directory, populate it with your discord bot token and chat prefixes as shown below:  
```env
DISCORD_TOKEN=***********************************************************
DISCORD_PREFIXES=separate prefixes with spaces
```
4. Run `docker run -d -v music:/usr/src/app/music --env-file filename_from_item_3 --rm discord-music-bot`
