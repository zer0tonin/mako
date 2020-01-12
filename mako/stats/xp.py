import asyncio
import logging

logger = logging.getLogger(__name__)


class XPAggregator:
    def __init__(self, redis):
        self.redis = redis

    async def get_user_xp(self, user, guild):
        xp_zset = "guilds:{}:xp".format(guild.id)
        return await self.redis.zscore(xp_zset, user.id)

    async def compute_user_xp(self, user_id, guild_id):
        activity_set = "guilds:{}:users:{}:activity".format(guild_id, user_id)
        xp_count = 0

        logger.debug("Accessing {} for user: {}".format(activity_set, user_id))
        async for activity in self.redis.isscan(activity_set):
            timeframe_hash = activity_set + ":{}".format(activity)
            logger.debug("Accessing {} for user: {}".format(timeframe_hash, user_id))

            visited = await self.redis.hget(timeframe_hash, "xp_visited")
            if not visited:
                xp_count = xp_count + 1

                reactions = await self.redis.hget(timeframe_hash, "reactions")
                if reactions:
                    logger.debug("Reaction count: {}".format(int(reactions)))
                    xp_count = xp_count + int(reactions)

                await self.redis.hset(timeframe_hash, "xp_visited", "1")

        return xp_count

    async def update_guild_xp(self, guild_id):
        users_set = "guilds:{}:users".format(guild_id)

        logger.debug("Accessing {} for guild: {}".format(users_set, guild_id))
        async for user_id in self.redis.isscan(users_set):
            user_xp = await self.compute_user_xp(user_id, guild_id)

            xp_zset = "guilds:{}:xp".format(guild_id)
            logger.debug(
                "Writing {} for user: {} by {}".format(xp_zset, user_id, user_xp)
            )
            await self.redis.zincrby(xp_zset, user_xp, user_id)

    async def update_guilds_xp(self):
        logger.info("Accessing guilds")
        async for guild in self.redis.isscan("guilds"):
            await self.update_guild_xp(guild)
