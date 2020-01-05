import asyncio
import logging

logger = logging.getLogger(__name__)

class Counter:
    def __init__(self, redis):
        self.redis = redis

    async def add_guild(self, guild):
        logger.debug("Creating guilds set for: {}#{}".format(guild.name, guild.id))
        await self.redis.sadd("guilds", guild.id)

    async def add_user(self, user):
        guild_set = "guilds:{}:users".format(user.guild.id)
        logger.debug("Creating {} set for: {}#{}".format(guild_set, user.name, user.id))
        await self.redis.sadd(guild_set, user.id)

    async def add_activity(self, message):
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        user_set = "guilds:{}:users:{}:activity".format(message.guild.id, message.author.id)
        logger.debug("Creating {} set for: {}".format(user_set, creation_minute))
        await self.redis.sadd(user_set, creation_minute)

    async def increment_message(self, message):
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        minute_hash = "guilds:{}:users:{}:activity:{}".format(message.guild.id, message.author.id, creation_minute)
        logger.debug("Incrementing {} hash for messages".format(minute_hash))
        await self.redis.hincrby(minute_hash, "messages", 1)

    async def increment_reaction(self, message, count=1):
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        minute_hash = "guilds:{}:users:{}:activity:{}".format(message.guild.id, message.author.id, creation_minute)
        logger.debug("Incrementing {} hash for reactions by {}".format(minute_hash, count))
        await self.redis.hincrby(minute_hash, "reactions", count)

    async def log_message(self, message):
        if hasattr(message.author, "id") and not message.author.bot:
            asyncio.gather(self.add_user(message.author), self.add_activity(message), self.increment_message(message))

    async def log_reaction(self, reaction):
        message = reaction.message
        if hasattr(message.author, "id") and not message.author.bot:
            asyncio.gather(self.add_user(message.author), self.add_activity(message), self.increment_reaction(message))

    async def log_full_message(self, message):
        if hasattr(message.author, "id") and not message.author.bot:
            asyncio.gather(self.add_user(message.author), self.add_activity(message), self.increment_message(message), self.increment_reaction(message, len(message.reactions)))

    async def parse_channel_history(self, channel):
        async for message in channel.history(limit=None):
            await self.log_full_message(message)
