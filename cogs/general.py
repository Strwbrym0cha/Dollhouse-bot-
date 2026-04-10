from discord.ext import commands
from discord.ui import View, Select
import discord

await bot.load_extension("cogs.general")

# 💖 UNIVERSAL ROLE SELECT
class RoleSelect(Select):
    def __init__(self, placeholder, roles, emojis):
        options = [
            discord.SelectOption(label=r, emoji=e)
            for r, e in zip(roles, emojis)
        ]

        super().__init__(
            placeholder=placeholder,
            options=options,
            custom_id=placeholder
        )

        self.role_names = roles

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        role = discord.utils.get(interaction.guild.roles, name=selected)

        if not role:
            return await interaction.response.send_message("Role missing 💔", ephemeral=True)

        # remove old roles in category
        for r in interaction.guild.roles:
            if r.name in self.role_names:
                await interaction.user.remove_roles(r)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("💖 role updated", ephemeral=True)


# 🎂 AGE
class AgeView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(
            "🎂 Age",
            ["🔞 18–20","💖 21–25","👑 26+"],
            ["🔞","💖","👑"]
        ))


# 💅 GENDER
class GenderView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(
            "💅 Gender",
            ["💖 Girl","💙 Boy","🌸 Non-binary","🖤 Prefer not"],
            ["💖","💙","🌸","🖤"]
        ))


# 🌍 LOCATION
class LocationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(
            "🌍 Location",
            ["🇺🇸 USA","🇬🇧 UK","🌍 Other"],
            ["🇺🇸","🇬🇧","🌍"]
        ))


# 🏳️ PRONOUNS
class PronounView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(
            "🏳️ Pronouns",
            ["💗 She/Her","💙 He/Him","💜 They/Them","✨ Any Pronouns"],
            ["💗","💙","💜","✨"]
        ))


# 💖 SEXUALITY
class SexualityView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(
            "💖 Sexuality",
            ["🌈 LGBTQ+","💘 Straight","💫 Questioning","🖤 Prefer not"],
            ["🌈","💘","💫","🖤"]
        ))


# 🎮 EVENTS (TOGGLE BUTTONS)
class EventView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎮 Game Night", style=discord.ButtonStyle.primary, custom_id="game_ping")
    async def game(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="🎮 Game Night Ping")

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("🎮 removed 💔", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🎮 added 💖", ephemeral=True)

    @discord.ui.button(label="☕ Tea Time", style=discord.ButtonStyle.success, custom_id="tea_ping")
    async def tea(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="☕ Tea Time Ping")

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("☕ removed 💔", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("☕ added 💖", ephemeral=True)


# 👑 STAFF
class StaffView(View):
    def __init__(self):
        super().__init__(timeout=None)


# 💖 COMMANDS
class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rolespanel(self, ctx):
        # 🧹 clear old messages (optional but nice)
        await ctx.channel.purge(limit=10)

        await ctx.send("🎂 Age", view=AgeView())
        await ctx.send("💅 Gender", view=GenderView())
        await ctx.send("🌍 Location", view=LocationView())
        await ctx.send("🏳️ Pronouns", view=PronounView())
        await ctx.send("💖 Sexuality", view=SexualityView())
        await ctx.send("🎮 Events", view=EventView())
async def setup(bot):
    await bot.add_cog(General(bot))
