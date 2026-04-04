from discord.ext import commands
import discord
from discord.ui import View

class StaffView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👑 Owner", style=discord.ButtonStyle.primary, custom_id="owner_role")
    async def owner(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="👑 Dollhouse Owner")
        if role:
            await interaction.user.add_roles(role)
        await interaction.response.send_message("👑 role added 💖", ephemeral=True)

    @discord.ui.button(label="🎀 Designer", style=discord.ButtonStyle.secondary, custom_id="designer_role")
    async def designer(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="🎀 Head Designer")
        if role:
            await interaction.user.add_roles(role)
        await interaction.response.send_message("🎀 role added 💖", ephemeral=True)

    @discord.ui.button(label="💖 Stylist", style=discord.ButtonStyle.success, custom_id="stylist_role")
    async def stylist(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="💖 Doll Stylist")
        if role:
            await interaction.user.add_roles(role)
        await interaction.response.send_message("💖 role added 💅", ephemeral=True)

    @discord.ui.button(label="🧸 Keeper", style=discord.ButtonStyle.secondary, custom_id="keeper_role")
    async def keeper(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="🧸 Doll Keeper")
        if role:
            await interaction.user.add_roles(role)
        await interaction.response.send_message("🧸 role added 💖", ephemeral=True)

    @discord.ui.button(label="✨ Assistant", style=discord.ButtonStyle.primary, custom_id="assistant_role")
    async def assistant(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="✨ Fairy Assistant")
        if role:
            await interaction.user.add_roles(role)
        await interaction.response.send_message("✨ role added 💖", ephemeral=True)
    @commands.command()
    async def staffroles(self, ctx):
    embed = discord.Embed(
        title="👑 Dollhouse Staff Roles",
        description="Assign your staff role 💖",
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed, view=StaffView())    
class EventView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎮 Game Night",
        style=discord.ButtonStyle.primary,
        custom_id="game_ping"
    )
    async def game(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="🎮 Game Night Ping")

        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("🎮 role added 💖", ephemeral=True)

    @discord.ui.button(
        label="☕ Tea Time",
        style=discord.ButtonStyle.success,
        custom_id="tea_ping"
    )
    async def tea(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="☕ Tea Time Ping")

        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("☕ tea time role added 💖", ephemeral=True)
class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="💖 Dollhouse Commands",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🎮 General",
            value="!profile\n!leaderboard\n!daily",
            inline=False
        )

        embed.add_field(
            name="💰 Economy",
            value="!shop\n!buy",
            inline=False
        )

        embed.add_field(
            name="🎟️ Support",
            value="!ticketpanel",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
