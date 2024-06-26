import discord
import time
from embeds import announcement_embed
from discord.commands import slash_command
from utils import unix_timestamp, load_config
from database import Announcement, AnnouncementManager

config = load_config(is_production=True)

@slash_command(
    name="announcement_stats"
)
async def announcement_stats(
    self, 
    ctx: discord.ApplicationContext
):
    # dev check
    if not ctx.author.id in config.get("developers", []):
        return await ctx.respond("nuh uh!")

    acm: AnnouncementManager = self.bot.acm
    
    announcement: Announcement = await acm.get_latest_announcement()
    if not announcement:
        return await ctx.respond("No announcements published!")

    em = announcement_embed(announcement)
    amount_read = await acm.get_how_many_read_latest()
    
    info = [
        f"ID: {announcement.id}",
        f"Seen by: {amount_read}",
        f"Is event set to expire: {bool(announcement.expiration_timestamp)}",
        f"Event expiration date: {unix_timestamp(announcement.expiration_timestamp, 'F') if announcement.expiration_timestamp else None}",
        f"Is event expired: {bool(announcement.expiration_timestamp and announcement.expiration_timestamp < time.time())}",
    ]

    await ctx.respond("\n".join(info), embed=em) 

    
    

        

        
