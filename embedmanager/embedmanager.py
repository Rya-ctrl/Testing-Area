import io
import json
from typing import Dict, Optional

import discord
from discord.ext import commands

from core import checks
from core.paginator import EmbedPaginatorSession
from core.models import PermissionLevel

from .converters import (
    MessageableChannel,
    BotMessage,
    StoredEmbedConverter,
    StringToEmbed,
)
from .utils import inline, human_join, paginate


class PlainMessage(commands.Cog, name="Plain Message"):
    """
    Have the bot send plain messages
    """
    
    _id = "config"
    default_config = {"embeds": {}}

    def __init__(self, bot):
        """
        Parameters
        ----------
        bot : bot.ModmailBot
            The Modmail bot.
        """
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)

    async def db_config(self) -> Dict:
        # No need to store in cache when initializing the plugin.
        # Only fetch from db when needed.
        config = await self.db.find_one({"_id": self._id})
        if config is None:
            config = {k: v for k, v in self.default_config.items()}
        return config

    async def update_db(self, data: dict):
        await self.db.find_one_and_update(
            {"_id": self._id},
            {"$set": data},
            upsert=True,
        )

    @staticmethod
    async def get_embed_from_message(message: discord.Message, index: int = 0):
        embeds = message.embeds
        if not embeds:
            raise commands.BadArgument("That message has no embeds.")
        index = max(min(index, len(embeds)), 0)
        embed = message.embeds[index]
        if embed.type == "rich":
            return embed
        raise commands.BadArgument("That is not a rich embed.")

    @staticmethod
    async def get_file_from_message(ctx: commands.Context, *, file_types=("json", "txt")) -> str:
        if not ctx.message.attachments:
            raise commands.BadArgument(
                f"Run `{ctx.bot.prefix}{ctx.command.qualified_name}` again, but this time attach an embed file."
            )
        attachment = ctx.message.attachments[0]
        if not any(attachment.filename.endswith("." + ft) for ft in file_types):
            raise commands.BadArgument(
                f"Invalid file type. The file name must end with one of {human_join([inline(ft) for ft in file_types])}."
            )

        content = await attachment.read()
        try:
            data = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise commands.BadArgument("Failed to read embed file contents.") from exc
        return data
    
    @commands.group(name="plain", usage="<option>", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def _plain(self, ctx: commands.Context):
        """
        Base command for Plain Message.
        """
        await ctx.send_help(ctx.command)
        
    @_plain.command(name="post")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def plain_post(
        self,
        ctx: commands.Context,
        channel: Optional[MessageableChannel],
        *,
        message,
    ):
        """
        Post a plain message.
        """
        channel = channel or ctx.channel
        await channel.send(message)

        
def setup(bot):
    bot.add_cog(PlainMessage(bot))
