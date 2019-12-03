import logging

from discord.ext.commands import Cog, command


logger = logging.getLogger(__name__)


class Mako(Cog):
    def __init__(self, bot, redis):
        self.bot = bot
        self.redis = redis

    @Cog.listener()
    async def on_ready(self):
        logger.info("We have logged in as {0.user}".format(self.bot))
