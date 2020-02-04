import asyncio
import logging


logger = logging.getLogger(__name__)


class Cleaner:
    def __init__(self, redis):
        self.redis = redis

    async def clean_guild(self, guild):
        logger.info("Cleaning data for guild: {}#{}".format(guild.name, guild.id))
        users_set = "guilds:{}:users".format(guild.id)
        level_zset = "guilds:{}:levels".format(guild.id)
        xp_zset = "guilds:{}:xp".format(guild.id)
        notify_list = "guilds:{}:notify".format(guild.id)
        to_delete = [users_set, level_zset, xp_zset, notify_list]

        async for user in self.redis.isscan(users_set):
            activity_set = "{}:{}:activity".format(users_set, user)

            async for minute in self.redis.isscan(activity_set):
                minute_hash = "{}:{}".format(activity_set, minute)
                to_delete.append(minute_hash)

            to_delete.append(activity_set)

        asyncio.gather(*[self.redis.delete(key) for key in to_delete])
