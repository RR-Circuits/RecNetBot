import discord
from typing import Optional
from discord.ext import pages
from discord.ext.pages import Page, PaginatorButton
from resources import get_emoji
from recnetpy.dataclasses.account import Account
from recnetpy.dataclasses.room import Room
from recnetpy.dataclasses.event import Event
from embeds import event_embed, profile_embed, room_embed
from typing import List, Optional, Union
from discord.ext.bridge import BridgeContext
from discord.ext.commands import Context
        
class RNBPage(Page):
    def __init__(self, *args, **kwargs):
        self.data = args[0]
        self.index = kwargs.pop("index", 0)
        self.page_count = kwargs.pop("page_count", 0)
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Optional[discord.Interaction] = None):
        """
        Executes when the page is displayed
        """
    
        if isinstance(self.content, Account):
            await self.data.get_bio()
            await self.data.get_level()
            await self.data.get_subscriber_count()
            self.embeds = [profile_embed(self.data)]
            self.content = None
            
        elif isinstance(self.content, Room):
            room = await self.data.client.rooms.fetch(self.data.id, 78)
            self.embeds = [room_embed(room)]
            self.content = None
            
        elif isinstance(self.content, Event):
            self.embeds = [event_embed(self.data)]
            self.content = None
            
        self.embeds[-1].set_footer(text=f"{self.index}/{self.page_count}")


class RNBPaginator(pages.Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # For indicator
        for i, page in enumerate(self.pages, start=1):
            page.index, page.page_count = i, self.page_count + 1
        
        
    async def goto_page(
        self, page_number: int = 0, *, interaction: Optional[discord.Interaction] = None
    ) -> None:
        self.update_buttons()
        self.current_page = page_number
        if self.show_indicator:
            self.buttons["page_indicator"][
                "object"
            ].label = f"{self.current_page + 1}/{self.page_count + 1}"

        if self.trigger_on_display:
            await self.page_action(interaction=interaction)

        page = self.pages[page_number]
        page = self.get_page_content(page)

        if page.custom_view:
            self.update_custom_view(page.custom_view)

        files = page.update_files()

        if interaction:
            await interaction.response.defer()  # needed to force webhook message edit route for files kwarg support
            await interaction.followup.edit_message(
                message_id=self.message.id,
                content=page.content,
                embeds=page.embeds,
                attachments=[],
                files=files or [],
                view=self,
            )
        else:
            await self.message.edit(
                content=page.content,
                embeds=page.embeds,
                attachments=[],
                files=files or [],
                view=self,
            )
            
    async def respond(
        self,
        interaction: Union[discord.Interaction, BridgeContext],
        ephemeral: bool = False,
        target: Optional[discord.abc.Messageable] = None,
        target_message: str = "Paginator sent!",
    ) -> Union[discord.Message, discord.WebhookMessage]:
        if not isinstance(interaction, (discord.Interaction, BridgeContext)):
            raise TypeError(
                f"expected Interaction or BridgeContext, not {interaction.__class__!r}"
            )

        if target is not None and not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable not {target.__class__!r}")

        if ephemeral and (self.timeout >= 900 or self.timeout is None):
            raise ValueError(
                "paginator responses cannot be ephemeral if the paginator timeout is 15 minutes or greater"
            )

        self.update_buttons()

        if self.trigger_on_display:
            await self.page_action(interaction=interaction)

        page: Union[Page, str, discord.Embed, List[discord.Embed]] = self.pages[
            self.current_page
        ]
        page_content: Page = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        if isinstance(interaction, discord.Interaction):
            self.user = interaction.user

            if target:
                await interaction.response.send_message(
                    target_message, ephemeral=ephemeral
                )
                msg = await target.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
            elif interaction.response.is_done():
                msg = await interaction.followup.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                    ephemeral=ephemeral,
                )
                # convert from WebhookMessage to Message reference to bypass
                # 15min webhook token timeout (non-ephemeral messages only)
                if not ephemeral:
                    msg = await msg.channel.fetch_message(msg.id)
            else:
                msg = await interaction.response.send_message(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                    ephemeral=ephemeral,
                )
        else:
            ctx = interaction
            self.user = ctx.author
            if target:
                await ctx.respond(target_message, ephemeral=ephemeral)
                msg = await ctx.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
            else:
                msg = await ctx.respond(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
        if isinstance(msg, (discord.Message, discord.WebhookMessage)):
            self.message = msg
        elif isinstance(msg, discord.Interaction):
            self.message = await msg.original_response()

        return self.message
    
    
    async def edit(
        self,
        message: discord.Message,
        suppress: Optional[bool] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        delete_after: Optional[float] = None,
    ) -> Optional[discord.Message]:
        if not isinstance(message, discord.Message):
            raise TypeError(f"expected Message not {message.__class__!r}")

        self.update_buttons()

        if self.trigger_on_display:
            await self.page_action()

        page: Union[Page, str, discord.Embed, List[discord.Embed]] = self.pages[
            self.current_page
        ]
        page_content: Page = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = message.author

        try:
            self.message = await message.edit(
                content=page_content.content,
                embeds=page_content.embeds,
                files=page_content.files,
                attachments=[],
                view=self,
                suppress=suppress,
                allowed_mentions=allowed_mentions,
                delete_after=delete_after,
            )
        except (discord.NotFound, discord.Forbidden):
            pass

        return self.message
    
    
    async def send(
        self,
        ctx: Context,
        target: Optional[discord.abc.Messageable] = None,
        target_message: Optional[str] = None,
        reference: Optional[
            Union[discord.Message, discord.MessageReference, discord.PartialMessage]
        ] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        mention_author: Optional[bool] = None,
        delete_after: Optional[float] = None,
    ) -> discord.Message:
        if not isinstance(ctx, Context):
            raise TypeError(f"expected Context not {ctx.__class__!r}")

        if target is not None and not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable not {target.__class__!r}")

        if reference is not None and not isinstance(
            reference,
            (discord.Message, discord.MessageReference, discord.PartialMessage),
        ):
            raise TypeError(
                f"expected Message, MessageReference, or PartialMessage not {reference.__class__!r}"
            )

        if allowed_mentions is not None and not isinstance(
            allowed_mentions, discord.AllowedMentions
        ):
            raise TypeError(
                f"expected AllowedMentions not {allowed_mentions.__class__!r}"
            )

        if mention_author is not None and not isinstance(mention_author, bool):
            raise TypeError(f"expected bool not {mention_author.__class__!r}")

        self.update_buttons()
        
        if self.trigger_on_display:
            await self.page_action()
        
        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = ctx.author

        if target:
            if target_message:
                await ctx.send(
                    target_message,
                    reference=reference,
                    allowed_mentions=allowed_mentions,
                    mention_author=mention_author,
                )
            ctx = target

        self.message = await ctx.send(
            content=page_content.content,
            embeds=page_content.embeds,
            files=page_content.files,
            view=self,
            reference=reference,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            delete_after=delete_after,
        )

        return self.message

    
    
    @staticmethod
    def get_page_content(
        page: Union[Page, str, discord.Embed, List[discord.Embed]]
    ) -> Page:
        """Converts a page into a :class:`Page` object based on its content."""
        if isinstance(page, Page):
            return page
        elif isinstance(page, str):
            return Page(content=page, embeds=[], files=[])
        elif isinstance(page, discord.Embed):
            return Page(content=None, embeds=[page], files=[])
        elif isinstance(page, discord.File):
            return Page(content=None, embeds=[], files=[page])
        elif isinstance(page, List):
            if all(isinstance(x, discord.Embed) for x in page):
                return Page(content=None, embeds=page, files=[])
            if all(isinstance(x, discord.File) for x in page):
                return Page(content=None, embeds=[], files=page)
            else:
                raise TypeError("All list items must be embeds or files.")
        else:
            raise TypeError(
                "Page content must be a Page object, string, an embed, a list of embeds, a file, or a list of files."
            )
            
            
    def add_default_buttons(self):
        """Adds the full list of default buttons that can be used with the paginator.
        Includes ``first``, ``prev``, ``page_indicator``, ``next``, and ``last``.
        """
        default_buttons = [
            PaginatorButton(
                "first",
                emoji=get_emoji('first'),
                style=discord.ButtonStyle.blurple,
                row=self.default_button_row,
            ),
            PaginatorButton(
                "prev",
                emoji=get_emoji('prev'),
                style=discord.ButtonStyle.red,
                loop_label="↪",
                row=self.default_button_row,
            ),
            PaginatorButton(
                "page_indicator",
                style=discord.ButtonStyle.gray,
                disabled=True,
                row=self.default_button_row,
            ),
            PaginatorButton(
                "next",
                emoji=get_emoji('next'),
                style=discord.ButtonStyle.green,
                loop_label="↩",
                row=self.default_button_row,
            ),
            PaginatorButton(
                "last",
                emoji=get_emoji('last'),
                style=discord.ButtonStyle.blurple,
                row=self.default_button_row,
            ),
        ]
        for button in default_buttons:
            self.add_button(button)