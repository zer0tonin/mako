# Mako: a small social discord bot

![Mako](image.gif)

Mako is a Discord bot initially made for the Furansu server.
It uses redis as a backend and provides gifs and levelling.

The project follows the [gazr](https://gazr.io) specs.

To launch it:
* make sure you have docker and docker-compose installed
* copy config/config.example.yml into config/config.yml and add your own bot token + customize the strings
* modify gifs.csv to add your own gifs
* just do `make run` or `docker-compose build mako && docker-compose up mako` to launch it
