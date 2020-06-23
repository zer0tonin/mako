import asyncio
import logging

logger = logging.getLogger(__name__)


def compute_user_level(user_xp):
    power = 1
    while user_xp >= 2 ** power:
        power = power + 1
    return power


class XPAggregator:
    def __init__(self, redis, levels):
        self.redis = redis
        self.levels = levels

    async def get_rank(self, guild):
        xp_zset = "guilds:{}:xp".format(guild.id)
        top_xp = await self.redis.zrevrange(xp_zset, 0, 9, withscores=True)

        level_tasks = []
        for line in top_xp:
            level_tasks.append(asyncio.create_task(self.get_user_level(line[0], guild)))
        await asyncio.gather(*level_tasks)

        result = []
        for i, level_task in enumerate(level_tasks):
            level = level_task.result()
            result.append((top_xp[i][0], top_xp[i][1], level[0], level[1]))

        return result

    async def get_user_xp(self, user_id, guild):
        """
        Returns the user xp from the guilds:{}:xp zset
        """
        xp_zset = "guilds:{}:xp".format(guild.id)
        return await self.redis.zscore(xp_zset, user_id)

    async def get_user_level(self, user_id, guild):
        """
        Returns a tuple with level and level name based on the guilds:{}:levels zset and config
        """
        level_zset = "guilds:{}:levels".format(guild.id)
        level = await self.redis.zscore(level_zset, user_id)
        if level is None:
            return (1, self.levels[1])
        return (level, self.levels[level])

    async def compute_user_xp(self, user_id, guild_id):
        """
        Uses the activity timeframe stored in guilds:{}:users:{}:activity to compute XP for a single user
        """
        activity_set = "guilds:{}:users:{}:activity".format(guild_id, user_id)
        react_value = "guilds:{}:users:{}:reactions".format(guild_id, user_id)
        activity, reacts = await asyncio.gather(
            self.redis.scard(activity_set),
            self.redis.get(react_value),
        )
        return activity + int(reacts) if reacts is not None else activity

    async def update_guild_xp(self, guild_id):
        """
        Stores the XP in the guilds:{}:xp zset
        """
        users_set = "guilds:{}:users".format(guild_id)

        logger.debug("Accessing {}".format(users_set))
        async for user_id in self.redis.isscan(users_set):
            user_xp = await self.compute_user_xp(user_id, guild_id)

            xp_zset = "guilds:{}:xp".format(guild_id)
            logger.debug(
                "Writing {} for user: {} by {}".format(xp_zset, user_id, user_xp)
            )
            await self.redis.zadd(xp_zset, user_xp, user_id)

    async def update_guilds_level(self, guild_id):
        """
        Stores the user levels in a guilds:{}:levels zset
        """
        users_set = "guilds:{}:users".format(guild_id)

        logger.debug("Accessing {}".format(users_set))
        async for user_id in self.redis.isscan(users_set):
            xp_zset = "guilds:{}:xp".format(guild_id)
            logger.debug("Accessing {} for user: {}".format(xp_zset, user_id))
            user_xp = await self.redis.zscore(xp_zset, user_id)

            if not user_xp:
                continue

            level = compute_user_level(user_xp)
            level_zset = "guilds:{}:levels".format(guild_id)
            notify_list = "guilds:{}:notify".format(guild_id)

            logger.debug("Accessing {} for user: {}".format(level_zset, user_id))
            previous_level = await self.redis.zscore(level_zset, user_id)

            if not previous_level:
                await self.set_level(level_zset, user_id, level)
            elif level > previous_level:
                asyncio.gather(
                    self.set_level(level_zset, user_id, level),
                    self.redis.lpush(notify_list, user_id),
                )

    async def set_level(self, level_zset, user_id, level):
        logger.debug("User {} is level {}".format(user_id, level))
        logger.debug(
            "Writing {} and for user: {} with value {}".format(
                level_zset, user_id, level
            )
        )
        await self.redis.zadd(level_zset, level, user_id)

    async def update_guilds(self):
        logger.info("Accessing guilds")
        async for guild in self.redis.isscan("guilds"):
            await self.update_guild_xp(guild)
            await self.update_guilds_level(guild)
