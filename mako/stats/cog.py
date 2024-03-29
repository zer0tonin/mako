import asyncio
import logging

from discord.ext.commands import Cog, command
from discord.ext.tasks import loop

from mako.util import mention_to_id


logger = logging.getLogger(__name__)


class Stats(Cog):
    """
    Statistiques d'activité
    """

    def __init__(self, bot, counter, xp_aggregator, notifier, config):
        self.bot = bot
        self.counter = counter
        self.xp_aggregator = xp_aggregator
        self.notifier = notifier
        self.spam_channel = config["spam_channel"]

        xp_loop = loop(seconds=config["delays"]["xp"])(self.update_xp)
        xp_loop.start()

        notify_loop = loop(seconds=config["delays"]["notify"])(self.notify_levels)
        notify_loop.start()

    @Cog.listener()
    async def on_guild_available(self, guild):
        """
        Computes the stats from previous messages when connecting to a guild
        """
        logger.info("connected to {}".format(guild.name))
        await self.counter.add_guild(guild)

    @Cog.listener()
    async def on_message(self, message):
        if message.guild is not None:
            await self.counter.log_message(message)

    @Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is not None:
            await self.counter.remove_message(message)

    @Cog.listener()
    async def on_reaction_add(self, reaction, _):
        if reaction.message.guild is not None:
            await self.counter.log_reaction(reaction)

    @Cog.listener()
    async def on_reaction_remove(self, reaction, _):
        if reaction.message.guild is not None:
            await self.counter.remove_reaction(reaction)

    @command()
    async def rank(self, ctx, *_):
        """
        Top 10 shitposters
        """
        top = await self.xp_aggregator.get_rank(ctx.guild)
        message = "```"
        for i, line in enumerate(top):
            user = self.bot.get_user(int(line[0]))
            if user is not None:
                message = message + "\n{}. {}: Level {} : {} : {} XP".format(
                    i + 1, user.name, line[2], line[3], line[1]
                )
        message = message + "\n```"
        return await ctx.send(message)

    async def user_level(self, ctx, user_id):
        level_task = asyncio.create_task(
            self.xp_aggregator.get_user_level(user_id, ctx.guild)
        )
        xp_task = asyncio.create_task(
            self.xp_aggregator.get_user_xp(user_id, ctx.guild)
        )

        await asyncio.gather(level_task, xp_task)
        level = level_task.result()
        user_xp = xp_task.result()

        await ctx.send("```Level {}: {} ({} XP)```".format(level[0], level[1], user_xp))

    @command()
    async def level(self, ctx, *args):
        """
        Level & XP
        """
        if args:
            user_ids = {mention_to_id(arg) for arg in args}
        else:
            user_ids = {ctx.author.id}

        tasks = [
            asyncio.create_task(self.user_level(ctx, user_id)) for user_id in user_ids
        ]
        asyncio.gather(*tasks)

    async def update_xp(self):
        logger.info("XP loop")
        await self.xp_aggregator.update_guilds()

    def get_bot_channel(self, guild_id):
        guild = self.bot.get_guild(guild_id)
        for channel in guild.channels:
            if self.spam_channel in channel.name:
                return channel
        raise ValueError("No proper spam channel")

    async def notify_levels(self):
        logger.info("Notify loop (Stats)")
        notifications = await self.notifier.notify_guilds()

        message_tasks = []
        for notification in notifications:
            try:
                channel = self.get_bot_channel(int(notification[0]))
                user = self.bot.get_user(int(notification[1]))
                if user is not None:
                    message_tasks.append(
                        asyncio.create_task(
                            channel.send("{} level up!".format(user.name))
                        )
                    )
            except AttributeError:
                logger.info("Bad notification encountered")

        asyncio.gather(*message_tasks)
