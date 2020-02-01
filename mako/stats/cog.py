import asyncio
import logging

from discord.ext.commands import Cog, command
from discord.ext.tasks import loop


logger = logging.getLogger(__name__)


class Stats(Cog):
    """
    Statistiques d'activité
    """

    def __init__(self, bot, counter, cleaner, xp_aggregator, delay):
        self.bot = bot
        self.counter = counter
        self.cleaner = cleaner
        self.xp_aggregator = xp_aggregator

        xp_loop = loop(seconds=delay)(self.update_xp)
        xp_loop.start()

    @Cog.listener()
    async def on_guild_available(self, guild):
        """
        Computes the stats from previous messages when connecting to a guild
        """
        logger.info("connected to {}".format(guild.name))
        await self.cleaner.clean_guild(guild)
        await self.counter.add_guild(guild)
        asyncio.gather(
            *[
                self.counter.parse_channel_history(channel)
                for channel in guild.channels
                if hasattr(channel, "history")
            ]
        )

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
            message = message + "\n{}. {}: Level {} : {} : {} XP".format(i + 1, user.name, line[2], line[3], line[1])
        message = message + "\n```"
        return await ctx.send(message)

    @command()
    async def level(self, ctx, *_):
        """
        Level & XP
        """
        level_task = asyncio.create_task(self.xp_aggregator.get_user_level(ctx.author.id, ctx.guild))
        xp_task = asyncio.create_task(self.xp_aggregator.get_user_xp(ctx.author, ctx.guild))

        await asyncio.gather(level_task, xp_task)
        level = level_task.result()
        user_xp = xp_task.result()

        await ctx.send("```Level {}: {} ({} XP)```".format(level[0], level[1], user_xp))

    async def update_xp(self):
        logger.info("XP loop")
        await self.xp_aggregator.update_guilds()
