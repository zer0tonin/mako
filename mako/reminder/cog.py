import asyncio
import logging

from datetime import datetime

import dateparser

from discord.ext.commands import Cog, command
from discord.ext.tasks import loop
from pytz import utc, timezone

from mako.reminder.notification import Notification

logger = logging.getLogger(__name__)


class Reminder(Cog):
    """
    Reminders
    """

    def __init__(self, bot, redis, config):
        self.bot = bot
        self.redis = redis
        self.spam_channel = config["spam_channel"]

        notify_loop = loop(seconds=config["delays"]["notify"])(self.notify_reminders)
        notify_loop.start()

    @command()
    async def remindme(self, ctx, *args):
        date = dateparser.parse(' '.join(args), languages=['en', 'fr'], settings={'TIMEZONE': 'Europe/Paris'})
        if date is None:
            await ctx.send("Je n'ai pas compris cette date")
            return
        date = timezone('Europe/Paris').localize(date)

        notification = Notification(ctx.guild.id, ctx.author.id, date).serialize()
        logger.debug("Writing in remind: {}".format(notification))
        await self.redis.lpush("remind", notification)

    def get_bot_channel(self, guild_id):
        guild = self.bot.get_guild(guild_id)
        for channel in guild.channels:
            if self.spam_channel in channel.name:
                return channel
        raise ValueError("No proper spam channel")

    async def get_notifications(self):
        result = []
        to_delete = []

        logger.debug("Reading remind list")
        for j in await self.redis.lrange("remind", 0, -1):
            notification = Notification.deserialize(j)
            logger.debug("Notification: {}".format(notification))
            logger.debug("Now: {}".format(datetime.now(utc)))
            if notification.date < datetime.now(utc):
                to_delete.append(j)
                result.append(notification)

        asyncio.gather(*[self.redis.lrem("remind", 0, n) for n in to_delete])

        return result

    async def notify_reminders(self):
        logger.info("Notify loop (Reminder)")

        notifications = await self.get_notifications()

        message_tasks = []
        for notification in notifications:
            channel = self.get_bot_channel(int(notification.guild_id))
            user = self.bot.get_user(int(notification.author_id))
            message_tasks.append(
                asyncio.create_task(channel.send("{} : {}".format(user.mention, "Bip boop c'est l'heure")))
            )

        asyncio.gather(*message_tasks)
