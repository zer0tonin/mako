import asyncio
import logging

from discord.ext.commands import Cog, command
from discord.ext.tasks import loop


logger = logging.getLogger(__name__)


class Stats(Cog):
    """
    Statistiques d'activité
    """

    def __init__(self, bot, counter, cleaner, xp_aggregator):
        self.bot = bot
        self.counter = counter
        self.cleaner = cleaner
        self.xp_aggregator = xp_aggregator

        xp_loop = loop(seconds=5)(self.update_xp)
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

    # @Cog.listener()
    # async def on_message_delete(self, message):
    #    if message.guild is not None and hasattr(message.author, "id") and not message.author.bot:
    #        await self.redis.zincrby("XP:{}".format(message.guild.id), -1, message.author.id)

    @Cog.listener()
    async def on_reaction_add(self, reaction, _):
        if reaction.message.guild is not None:
            await self.counter.log_reaction(reaction)

    # @command()
    # async def top(self, ctx, *_):
    #    """
    #    Meilleurs shitposteurs
    #    """
    #    top = await self.redis.zrevrange("XP:{}".format(ctx.guild.id), 0, 10, withscores=True)
    #    message = "```"
    #    for i, line in enumerate(top):
    #        user = self.bot.get_user(int(line[0]))
    #        message = message + "\n{}. {} : {}".format(i, user.name, line[1])
    #    message = message + "\n```"
    #    return await ctx.send(message)

    @command()
    async def level(self, ctx, *_):
        result = await self.xp_aggregator.get_user_xp(ctx.author, ctx.guild)
        if result:
            await ctx.send(result)

    async def update_xp(self):
        logger.info("XP loop")
        await self.xp_aggregator.update_guilds_xp()
