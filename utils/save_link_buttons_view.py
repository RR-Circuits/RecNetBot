import discord


class SaveLinkBtnsView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def on_timeout(self):
        # Method override to exempt link buttons from being disabled on timeout.
        if not self.disable_on_timeout: return
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.style == discord.ButtonStyle.link:
                continue
            item.disabled = True
        message = self._message or self.parent
        if message:
            m = await message.edit(view=self)
            if m: self._message = m