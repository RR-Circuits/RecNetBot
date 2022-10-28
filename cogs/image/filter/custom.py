import discord
from discord.commands import slash_command, Option
from utils.converters import FetchAccount
from exceptions import ConnectionNotFound, ImagesNotFound
from utils.paginator import RNBPaginator, RNBPage
from embeds import get_default_embed

@slash_command(
    name="custom",
    description="Combine all filters together to find specific RecNet posts."
)
async def custom(
    self, 
    ctx: discord.ApplicationContext,
    taken_by: Option(FetchAccount, name="taken_by", description="Enter the RR username who took the photos (not required if you used together)", default=None, required=False) = None,
    _sort: Option(str, name="sort", description="Choose what to sort by", required=False, choices=[
        "Oldest to Newest", 
        "Cheers: Highest to Lowest",
        "Comments: Highest to Lowest",
        "Tags: Highest to Lowest",
    ], default=None) = None,
    together: Option(str, name="together", description="Filter by which RR users are featured in a post (separate by spaces)", required=False, default=None) = None,
    exclude_together: Option(str, name="exclude_together", description="Filter by which RR users SHOULDN'T be featured in a post (separate by spaces)", required=False, default=None) = None,
    rooms: Option(str, name="rooms", description="Filter by which RR rooms can be featured (separate by spaces)", required=False, default=None) = None,
    exclude_rooms: Option(str, name="exclude_rooms", description="Filter by which RR rooms SHOULDN'T be featured (separate by spaces)", required=False, default=None) = None,
    min_cheers: Option(int, name="minimum_cheers", description="Filter out posts that don't have at least this many cheers", default=0, required=False, min_value=0) = None,
    max_cheers: Option(int, name="maximum_cheers", description="Filter out posts that exceed this many cheers", default=10**10, required=False, min_value=0) = None,
    min_comments: Option(int, name="minimum_comments", description="Filter out posts that don't have at least this many comments", default=0, required=False, min_value=0) = None,
    max_comments: Option(int, name="maximum_comments", description="Filter out posts that exceed this many comments", default=10**10, required=False, min_value=0) = None,
    min_tags: Option(int, name="minimum_tags", description="Filter out posts that don't have at least this many tags", default=0, required=False, min_value=0) = None,
    max_tags: Option(int, name="maximum_tags", description="Filter out posts that exceed this many tags", default=10**10, required=False, min_value=0) = None,
):
    await ctx.interaction.response.defer(invisible=True)
    posts = []

    if taken_by:  # Check for a linked RR account
        posts: list = await taken_by.get_images(take=1_000_000)
    elif together:
        # Fetch the first user from together
        # Since the user is required to be in the post, this will work
        first_user = together.split(" ")[0]
        first_user = await self.bot.RecNet.accounts.get(first_user)
        if first_user:
            posts: list = await first_user.get_feed(take=1_000_000)
        
    # Filter by rooms
    if rooms:
        i_rooms = await self.bot.RecNet.rooms.get_many(rooms.split(" "))
        
        if i_rooms:
            posts = list(filter(lambda image: all(room.id == image.room_id for room in i_rooms), posts))
        
    # Exclude by rooms
    if exclude_rooms:
        e_rooms = await self.bot.RecNet.rooms.get_many(exclude_rooms.split(" "))
        
        if e_rooms:
            posts = list(filter(lambda image: all(room.id != image.room_id for room in e_rooms), posts))
        
    # Filter by together
    if together:
        t_users = await self.bot.RecNet.accounts.get_many(together.split(" "))
        
        if t_users:
            posts = list(filter(lambda image: all(user.id in image.tagged_player_ids for user in t_users), posts))
    
    # Exclude by together
    if exclude_together:
        e_t_users = await self.bot.RecNet.accounts.get_many(exclude_together.split(" "))
        
        if e_t_users:
            posts = list(filter(lambda image: all(user.id not in image.tagged_player_ids for user in e_t_users), posts))
    
    # Min max filters
    posts = list(filter(lambda image:
         image.cheer_count >= min_cheers and image.cheer_count <= max_cheers and  # Cheers
         image.comment_count >= min_comments and image.comment_count <= max_comments and  # Comments
         len(image.tagged_player_ids) >= min_tags and len(image.tagged_player_ids) <= max_tags,  # Tags
         posts 
    ))
    
    # Sort photos
    match _sort:
        case "Oldest to Newest":
            posts.reverse()
        case "Cheers: Highest to Lowest":
            posts.sort(reverse=True, key=lambda image: image.cheer_count)
        case "Comments: Highest to Lowest":
            posts.sort(reverse=True, key=lambda image: image.comment_count)
        case "Tags: Highest to Lowest":
            posts.sort(reverse=True, key=lambda image: len(image.tagged_player_ids))
        case _:  # Don't sort
            ...
    
    if posts:
        pages = list(map(lambda ele: RNBPage(ele), posts))
        paginator = RNBPaginator(pages=pages, trigger_on_display=True, show_indicator=False, author_check=True)
        await paginator.respond(ctx.interaction)
    else:
        em = get_default_embed()
        em.title = "No posts found!"
        em.description = "If you set any filters, make sure they don't contradict with each other."
        await ctx.respond(embed=em)
    

        

        
