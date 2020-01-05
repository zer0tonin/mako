import asyncio
import logging
import yaml

from aioredis import create_redis_pool
from discord.ext.commands import Bot

from mako.gifs.database import GifsDatabase
from mako.gifs.cog import GifsReact

from mako.stats.cog import Stats
from mako.stats.cleaner import Cleaner
from mako.stats.counter import Counter
from mako.stats.xp import XPAggregator

logger = logging.getLogger(__name__)


async def start_bot(config):
    logger.info("Running the client")
    redis = await create_redis_pool(
        "redis://{}:{}".format(config["redis"]["host"], config["redis"]["port"])
    )
    gifs_database = GifsDatabase()

    bot = Bot(command_prefix="!", description="Bip Boop")
    bot.add_cog(GifsReact(bot, gifs_database))
    bot.add_cog(Stats(bot, Counter(redis), Cleaner(redis), XPAggregator(redis)))
    await bot.start(config["token"])


def run():
    with open("config/config.yml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
            logging.basicConfig(level=config["logging_level"])
            asyncio.run(start_bot(config))

        except yaml.YAMLError:
            logger.exception("Failed to parse config")
            exit(1)
