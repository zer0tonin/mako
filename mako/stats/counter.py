import asyncio
import logging

logger = logging.getLogger(__name__)


class Counter:
    def __init__(self, redis):
        self.redis = redis

    async def add_guild(self, guild):
        """
        Adds a guild to the guilds set
        """
        logger.debug("Creating guilds set for: {}#{}".format(guild.name, guild.id))
        await self.redis.sadd("guilds", guild.id)

    async def add_user(self, user):
        """
        Adds an user to the guilds:{}:users set
        """
        guild_set = "guilds:{}:users".format(user.guild.id)
        logger.debug("Creating {} set for: {}#{}".format(guild_set, user.name, user.id))
        await self.redis.sadd(guild_set, user.id)

    async def add_activity(self, message):
        """
        Adds an activity timeframe to the guilds:{}:users:{}:activity
        """
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        user_set = "guilds:{}:users:{}:activity".format(
            message.guild.id, message.author.id
        )
        logger.debug("Creating {} set for: {}".format(user_set, creation_minute))
        await self.redis.sadd(user_set, creation_minute)

    async def increment_message(self, message):
        """
        Increments the message count in an activity timeframe in the hash guilds:{}:users:{}:activity
        """
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        minute_hash = "guilds:{}:users:{}:activity:{}".format(
            message.guild.id, message.author.id, creation_minute
        )
        logger.debug("Incrementing {} hash for messages".format(minute_hash))
        await self.redis.hincrby(minute_hash, "messages", 1)

    async def increment_reaction(self, message, count=1):
        """
        Increments the reaction count in an activity timeframe in the hash guilds:{}:users:{}:activity:{}
        """
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        minute_hash = "guilds:{}:users:{}:activity:{}".format(
            message.guild.id, message.author.id, creation_minute
        )
        logger.debug(
            "Incrementing {} hash for reactions by {}".format(minute_hash, count)
        )
        await self.redis.hincrby(minute_hash, "reactions", count)

    async def decrement_reaction(self, message, count=1):
        """
        Decrements a reaction counter from an activity timeframe if it exists
        """
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        activity_set = "guilds:{}:users:{}:activity".format(message.guild.id, message.author.id)
        minute_hash = "guilds:{}:users:{}:activity:{}".format(
            message.guild.id, message.author.id, creation_minute
        )
        logger.debug(
            "Checking {} set for activity {}".format(activity_set, count)
        )
        if await self.redis.sismember(activity_set, creation_minute) and await self.redis.hget(minute_hash, "reactions") != "0":
            logger.debug(
                "Decrementing {} hash for reactions".format(minute_hash)
            )
            await self.redis.hincrby(minute_hash, "reactions", -1)

    async def decrement_message(self, message, count=1):
        """
        Decrements a message counter from an activity timeframe if it exists
        """
        creation_minute = message.created_at.strftime("%Y-%m-%dT%H:%M")
        activity_set = "guilds:{}:users:{}:activity".format(message.guild.id, message.author.id)
        minute_hash = "guilds:{}:users:{}:activity:{}".format(
            message.guild.id, message.author.id, creation_minute
        )
        logger.debug(
            "Checking {} set for activity {}".format(activity_set, count)
        )
        if await self.redis.sismember(activity_set, creation_minute) and await self.redis.hget(minute_hash, "messages") != "0":
            logger.debug(
                "Decrementing {} hash for messages".format(minute_hash)
            )
            await self.redis.hincrby(minute_hash, "messages", -1)

    async def log_message(self, message):
        """
        Adds a new message to a guild, creating a new user and activity timeframe if needed
        """
        if hasattr(message.author, "id") and not message.author.bot:
            asyncio.gather(
                self.add_user(message.author),
                self.add_activity(message),
                self.increment_message(message),
            )

    async def remove_message(self, message):
        """
        Removes a message from a guild, assuming the user and activity timeframe already exists
        TODO: need to handle the reaction associated with it
        """
        if hasattr(message.author, "id") and not message.author.bot:
            await self.decrement_message(message)

    async def log_reaction(self, reaction):
        """
        Adds a new reaction to a guild, creating a new user and activity timeframe if needed
        """
        message = reaction.message
        if hasattr(message.author, "id") and not message.author.bot:
            asyncio.gather(
                self.add_user(message.author),
                self.add_activity(message),
                self.increment_reaction(message),
            )

    async def remove_reaction(self, reaction):
        """
        Removes a message from a guild, assuming the user and activity timeframe already exists
        """
        message = reaction.message
        if hasattr(message.author, "id") and not message.author.bot:
            await self.decrement_reaction(message)

    async def log_full_message(self, message):
        """
        Adds a new message with reactions to the guild, creating a new uer and activity timeframe if needed
        """
        if hasattr(message.author, "id") and not message.author.bot:
            asyncio.gather(
                self.add_user(message.author),
                self.add_activity(message),
                self.increment_message(message),
                self.increment_reaction(message, len(message.reactions)),
            )

    async def parse_channel_history(self, channel):
        async for message in channel.history(limit=None):
            await self.log_full_message(message)
