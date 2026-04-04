import discord
from discord.ext import commands
from discord.ui import View, Button

CATEGORY_NAME = "🎟️ Tickets"
STAFF_ROLE = "✨ Fairy Assistant"


# 🎟️ OPEN TICKET VIEW
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)  # required for persistence

    @discord.ui.button(
        label="🎟️ Open Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="open_ticket_button"  # required for persistence
    )
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE)

        # create category if missing
        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        # prevent crash if role missing
        if not staff_role:
            await interaction.response.send_message(
                "Staff role not found 💔", ephemeral=True
            )
            return

        # prevent duplicate tickets
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name}")
        if existing:
            await interaction.response.send_message(
                "💖 You already have a ticket!", ephemeral=True
            )
            return

        # permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # create channel
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        # send messages
        await channel.send(f"{staff_role.mention} 💖 New ticket from {user.mention}")
        await channel.send(
            "🔒 Press below to close this ticket",
            view=CloseView()
        )

        await interaction.response.send_message(
            f"🎀 Ticket created: {channel.mention}",
            ephemeral=True
        )


# 🔒 CLOSE TICKET VIEW
class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()


# 🎀 COG
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # persistent views (VERY IMPORTANT)
        bot.add_view(TicketView())
        bot.add_view(CloseView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        embed = discord.Embed(
            title="🎟️ Dollhouse Support",
            description="Click the button below to open a ticket 💖",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=TicketView())


# 🔌 LOAD COG
async def setup(bot):
    await bot.add_cog(Tickets(bot))
