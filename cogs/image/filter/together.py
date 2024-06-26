import discord
from discord.commands import slash_command
from discord.ext.bridge import BridgeOption as Option
from exceptions import Disabled

@slash_command(
    name="together",
    description="Find posts where specified players are featured in."
)
async def together(
    self, 
    ctx: discord.ApplicationContext,
    together: Option(str, name="together", description="Filter by which RR users are featured in a post (separate by spaces)", required=False, default=None),
    exclude: Option(str, name="exclude", description="Filter by which RR users SHOULDN'T be featured in a post (separate by spaces)", required=False, default=None)
):
    # Broken command
    raise Disabled

    if not together and not exclude:
        await ctx.interaction.response.send_message("Fill in `together` or `exclude`!", ephemeral=True)
        return
    
    group = discord.utils.get(self.__cog_commands__, name='filter')
    command = discord.utils.get(group.walk_commands(), name='custom')
    await command(ctx, together=together, exclude_together=exclude)

    
    

        

        
