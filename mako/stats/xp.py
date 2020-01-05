import asyncio
import logging


logger = logging.getLogger(__name__)


class XPAggregator:
    def __init__(self, redis):
        self.redis = redis

    async def user_level(self, user, guild):
        activity_set = "guilds:{}:users:{}:activity".format(guild.id, user.id)
        xp_count = 0

        logger.debug("Accessing {} for user: {}#{}".format(activity_set, user.name, user.id))
        async for activity in self.redis.isscan(activity_set):
            xp_count = xp_count + 1

            timeframe_hash = activity_set + ":{}".format(activity.decode('ascii'))
            logger.debug("Accessing {} for user: {}#{}".format(timeframe_hash, user.name, user.id))
            reactions = await self.redis.hget(timeframe_hash, "reactions")
            if reactions:
                xp_count = xp_count + int(reactions.decode('ascii'))

        return xp_count
