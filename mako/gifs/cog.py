import logging

from discord.ext.commands import Cog, command


logger = logging.getLogger(__name__)


class GifsReact(Cog):
    """
    Gifs disponibles
    """

    def __init__(self, bot, gifs_database):
        self.bot = bot
        self.gifs_database = gifs_database

    @Cog.listener()
    async def on_ready(self):
        logger.info("We have logged in as {0.user}".format(self.bot))

    async def send_gif(self, ctx, category):
        gif = self.gifs_database.get_random(category)
        await ctx.send(gif)

    @command()
    async def punch(self, ctx, *_):
        await self.send_gif(ctx, "punch")

    @command()
    async def smirk(self, ctx, *_):
        await self.send_gif(ctx, "smirk")

    @command()
    async def nanithefuck(self, ctx, *_):
        await self.send_gif(ctx, "nanithefuck")

    @command()
    async def lewd(self, ctx, *_):
        await self.send_gif(ctx, "lewd")

    @command()
    async def angry(self, ctx, *_):
        await self.send_gif(ctx, "angry")

    @command()
    async def smoll(self, ctx, *_):
        await self.send_gif(ctx, "smoll")

    @command()
    async def rekt(self, ctx, *_):
        await self.send_gif(ctx, "rekt")

    @command()
    async def lick(self, ctx, *_):
        await self.send_gif(ctx, "lick")

    @command()
    async def bite(self, ctx, *_):
        await self.send_gif(ctx, "bite")

    @command()
    async def pantsu(self, ctx, *_):
        await self.send_gif(ctx, "pantsu")

    @command()
    async def slap(self, ctx, *_):
        await self.send_gif(ctx, "slap")
