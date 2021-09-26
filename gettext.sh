#!/bin/sh
pygettext3 bot.py cogs/music.py
msgmerge -U locale/en/LC_MESSAGES/Discord-Music-Bot.po messages.pot
msgfmt locale/en/LC_MESSAGES/Discord-Music-Bot.po -o locale/en/LC_MESSAGES/Discord-Music-Bot.mo
msgmerge -U locale/ru/LC_MESSAGES/Discord-Music-Bot.po messages.pot
msgfmt locale/ru/LC_MESSAGES/Discord-Music-Bot.po -o locale/ru/LC_MESSAGES/Discord-Music-Bot.mo
