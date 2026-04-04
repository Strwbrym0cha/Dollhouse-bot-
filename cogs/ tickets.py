import discord
from discord.ext import commands
from discord.ui import View, Button

CATEGORY_NAME = "🎟️ Tickets"
STAFF_ROLE = "✨ Fairy Assistant"

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎟️ Open Ticket", style=discord.ButtonStyle.purple)
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE)

        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name}")
        if existing:
            await interaction.response.send_message("💖 You already have a ticket!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(f"{staff_role.mention} 💖 New ticket from {user.mention}")
        await channel.send("🔒 Press below to close", view=CloseView())

        await interaction.response.send_message(f"🎀 Created {channel.mention}", ephemeral=True)

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketView())
        bot.add_view(CloseView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        embed = discord.Embed(
            title="🎟️ Dollhouse Support",
            description="Click to open a ticket 💖",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed, view=TicketView())
if not staff_role:
    await interaction.response.send_message("Staff role not found 💔", ephemeral=True)
    return
def setup(bot):
    bot.add_cog(Tickets(bot))
