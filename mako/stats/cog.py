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

    @command()
    async def top(self, ctx, *_):
        """
        Meilleurs shitposteurs
        """
        self.redis.zincrby("XP", 1, "fabulon")
        self.redis.zincrby("XP", 1, "rap-tout")
        self.redis.zincrby("XP", 1, "rap-tout")
        self.redis.zincrby("XP", 1, "rap-tout")
        top = await self.redis.zrevrange("XP", 0, 10, withscores=True)
        message = ""
        for i, line in enumerate(top):
            message = message + "\n{}. {} : {}".format(i, line[0].decode('ascii'), line[1])
        return await ctx.send(message)
