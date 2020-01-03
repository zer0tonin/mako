import asyncio
import logging

from discord.ext.commands import Cog, command


logger = logging.getLogger(__name__)


class Stats(Cog):
    """
    Statistiques d'activité
    """

    def __init__(self, bot, redis):
        self.bot = bot
        self.redis = redis

    async def parse_channel_history(self, channel, guild):
        async for message in channel.history(limit=None):
            if hasattr(message.author, "id") and not message.author.bot:
                await self.redis.zincrby("XP:{}".format(guild.id), 1, message.author.id)

    @Cog.listener()
    async def on_guild_available(self, guild):
        """
        Computes the stats from previous messages when connecting to a guild
        """
        logger.info("connected to {}".format(guild.name))
        await self.redis.delete("XP:{}".format(guild.id)) # reset the zset
        asyncio.gather(*[self.parse_channel_history(channel, guild) for channel in guild.channels if hasattr(channel, "history")])


    @Cog.listener()
    async def on_message(self, message):
        if hasattr(message.author, "id") and not message.author.bot:
            await self.redis.zincrby("XP:{}".format(message.guild.id), 1, message.author.id)

    @Cog.listener()
    async def on_message_delete(self, message):
        if hasattr(message.author, "id") and not message.author.bot:
            await self.redis.zincrby("XP:{}".format(message.guild.id), -1, message.author.id)

    @command()
    async def top(self, ctx, *_):
        """
        Meilleurs shitposteurs
        """
        top = await self.redis.zrevrange("XP:{}".format(ctx.guild.id), 0, 10, withscores=True)
        message = "```"
        for i, line in enumerate(top):
            user = self.bot.get_user(int(line[0].decode('ascii')))
            message = message + "\n{}. {} : {}".format(i, user.name, line[1])
        message = message + "\n```"
        return await ctx.send(message)
