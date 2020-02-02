import logging


logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, redis):
        self.redis = redis

    async def notify_guilds(self):
        guilds_set = "guilds"
        logger.debug("Scanning {}".format(guilds_set))

        result = []
        async for guild_id in self.redis.isscan(guilds_set):
            result.extend(await self.notify_guild(guild_id))
        return result

    async def notify_guild(self, guild_id):
        notify_set = "guilds:{}:notify".format(guild_id)
        level_zset = "guilds:{}:levels".format(guild_id)

        result = []
        logger.debug("Scanning {} set".format(notify_set))
        async for user_id in self.redis.isscan(notify_set):
            logger.debug("Accessing {} zset for user: {}".format(level_zset, user_id))
            level = await self.redis.zscore(level_zset, user_id)
            result.append((guild_id, user_id, level))

        return result
