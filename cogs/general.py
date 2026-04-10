from discord.ext import commands
from discord.ui import View, Select
import discord
import random


PINK = discord.Color.from_rgb(255, 182, 193)
VERIFIED_ROLE = "Verified Doll"
UNVERIFIED_ROLE = "Unverified Doll"


def doll_embed(title, description):
    e = discord.Embed(title=title, description=description, color=PINK)
    e.set_footer(text="💖 Dollhouse • stay soft & powerful")
    return e


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
            custom_id=placeholder,
        )

        self.role_names = roles

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        role = discord.utils.get(interaction.guild.roles, name=selected)

        if not role:
            return await interaction.response.send_message("Role missing 💔", ephemeral=True)

        for r in interaction.guild.roles:
            if r.name in self.role_names:
                await interaction.user.remove_roles(r)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("💖 role updated", ephemeral=True)


class AgeView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("🎂 Age", ["🔞 18–20", "💖 21–25", "👑 26+"], ["🔞", "💖", "👑"]))


class GenderView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("💅 Gender", ["💖 Girl", "💙 Boy", "🌸 Non-binary", "🖤 Prefer not"], ["💖", "💙", "🌸", "🖤"]))


class LocationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("🌍 Location", ["🇺🇸 USA", "🇬🇧 UK", "🌍 Other"], ["🇺🇸", "🇬🇧", "🌍"]))


class PronounView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            RoleSelect(
                "🏳️ Pronouns",
                ["💗 She/Her", "💙 He/Him", "💜 They/Them", "✨ Any Pronouns"],
                ["💗", "💙", "💜", "✨"],
            )
        )


class SexualityView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("💖 Sexuality", ["🌈 LGBTQ+", "💘 Straight", "💫 Questioning", "🖤 Prefer not"], ["🌈", "💘", "💫", "🖤"]))


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


class RulesVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Agree & Enter 💖", style=discord.ButtonStyle.success, custom_id="rules_verify")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        verified = discord.utils.get(guild.roles, name=VERIFIED_ROLE)
        unverified = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE)

        if verified:
            await user.add_roles(verified)

        if unverified and unverified in user.roles:
            await user.remove_roles(unverified)

        await interaction.response.send_message(f"💖 welcome {user.name}… you made it inside ✨", ephemeral=True)


class StaffView(View):
    def __init__(self):
        super().__init__(timeout=None)


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(EventView())
        bot.add_view(StaffView())
        bot.add_view(AgeView())
        bot.add_view(GenderView())
        bot.add_view(LocationView())
        bot.add_view(PronounView())
        bot.add_view(SexualityView())
        bot.add_view(RulesVerifyView())

    @commands.command()
    async def help(self, ctx):
        await ctx.send(
            embed=doll_embed(
                "💖 CORE",
                """
!help
!dashboard

🎀 **ROLES**
!rolespanel

🎟️ **SUPPORT**
!ticketpanel

💰 **ECONOMY**
!profile
!daily
!shop
!buy
!balance
!rich
!pay
!gamble

🎮 **ENGAGEMENT**
!rep
!rank

👑 **ADMIN**
!give
!setcoins
!resetuser
""",
            )
        )

    @commands.command()
    async def menu(self, ctx):
        await ctx.send(
            embed=doll_embed(
                "🎀 Dollhouse Menu",
                """
💖 **Doll Commands**
!doll — affirmation
!selfcare — self care tip

💎 **Progress**
!profile — your stats
!daily — daily reward
!leaderboard — top dolls
!level — level and xp
!rep — show rep

🎟️ **Support**
!ticketpanel — open ticket

🎀 **Access**
!rolespanel — pick roles
!rulespanel — verify panel

👩‍💻 **Staff**
!clear <amount> — delete messages
!addvip @user — VIP
!personality <mode>
""",
            )
        )

    @commands.command()
    async def doll(self, ctx):
        affirmations = [
            "💖 you are THAT doll. don’t forget it.",
            "✨ pretty, powerful, and unstoppable.",
            "💅 soft doesn’t mean weak.",
            "🎀 you deserve everything you dream of.",
            "💎 you’re the main character, always.",
        ]
        await ctx.send(embed=doll_embed("💖 Doll Affirmation", random.choice(affirmations)))

    @commands.command()
    async def selfcare(self, ctx):
        tips = [
            "🛁 take a warm shower & reset your energy",
            "📵 log off for a bit — protect your peace",
            "💤 rest is productive too",
            "🕯️ light a candle & breathe",
            "🎧 listen to music and just exist",
        ]
        await ctx.send(embed=doll_embed("🧸 Self Care Reminder", random.choice(tips)))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rolespanel(self, ctx):
        await ctx.send("🎂 Age", view=AgeView())
        await ctx.send("💅 Gender", view=GenderView())
        await ctx.send("🌍 Location", view=LocationView())
        await ctx.send("🏳️ Pronouns", view=PronounView())
        await ctx.send("💖 Sexuality", view=SexualityView())
        await ctx.send("🎮 Events", view=EventView())

    @commands.command()
    async def rulespanel(self, ctx):
        await ctx.send(
            embed=doll_embed(
                "💖 DOLLHOUSE RULES",
                """
🔞 **this is an 18+ server only**
by staying, you confirm you are 18 or older

━━━━━━━━━━━━━━━━━━━

💖 **1. be kind, always**
treat every doll with respect — no bullying or harassment

💖 **2. no hate or discrimination**
this is a safe and inclusive space for everyone

💖 **3. keep it cute**
light profanity is okay, but don’t use it to attack others

💖 **4. no spam or unwanted promo**
only promote in the correct channels

💖 **5. nsfw stays in nsfw channels**
must be verified to access

💖 **6. listen to staff**
our dollhouse team keeps everything safe and smooth

━━━━━━━━━━━━━━━━━━━

💖 click below to agree & enter ✨
""",
            ),
            view=RulesVerifyView(),
        )


async def setup(bot):
    await bot.add_cog(General(bot))
