import discord
from discord.ext import commands
from discord.ui import View, Button

CATEGORY = "🎟️ Tickets"
STAFF = "✨ Fairy Assistant"

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎟️ Open Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="open_ticket"
    )
    async def open(self, interaction: discord.Interaction, button: Button):
        g = interaction.guild
        u = interaction.user

        staff = discord.utils.get(g.roles, name=STAFF)
        cat = discord.utils.get(g.categories, name=CATEGORY)

        if not cat:
            cat = await g.create_category(CATEGORY)

        if not staff:
            return await interaction.response.send_message("Staff role missing 💔", ephemeral=True)

        if discord.utils.get(g.text_channels, name=f"ticket-{u.id}"):
            return await interaction.response.send_message("You already have a ticket 💖", ephemeral=True)

        overwrites = {
            g.default_role: discord.PermissionOverwrite(view_channel=False),
            u: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        ch = await g.create_text_channel(
            name=f"ticket-{u.id}",
            category=cat,
            overwrites=overwrites
        )

        await ch.send(f"{staff.mention} 💖 assisting {u.mention}", view=CloseView())

        await interaction.response.send_message(f"🎀 {ch.mention} created", ephemeral=True)


class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket"
    )
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketView())
        bot.add_view(CloseView())

    @commands.command()
    async def ticketpanel(self, ctx):
        embed = discord.Embed(
            title="🎟️ Support",
            description="Click to open a ticket 💖",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=TicketView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))
