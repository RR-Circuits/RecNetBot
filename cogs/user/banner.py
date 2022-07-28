from base_commands.base_posts import base_posts
from utility import load_cfg, respond
from discord.commands import slash_command, Option # Importing the decorator that makes slash commands.
from base_commands.base_profile import base_profile

cfg = load_cfg()

@slash_command(
    debug_guilds=cfg['test_guild_ids'],
    name="banner",
    description="Get a user's RecNet banner picture."
)
async def banner(
    self, 
    ctx, 
    username: Option(str, "Enter user's username", required=True)
):
    await ctx.interaction.response.defer()
    embed, view = await base_profile(self.bot.rec_net, ctx, username, "banner")
    await respond(ctx, embed=embed, view=view)