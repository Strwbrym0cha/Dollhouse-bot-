from discord.ext import commands
from discord.ui import View, Select
import discord


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

        for r in interaction.guild.roles:
            if r.name in self.role_names:
                await interaction.user.remove_roles(r)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("💖 role updated", ephemeral=True)


class AgeView(View):
    def __init__(self):
        super().__init__(timeout=None)


class GenderView(View):
    def __init__(self):
        super().__init__(timeout=None)


class LocationView(View):
    def __init__(self):
        super().__init__(timeout=None)


class PronounView(View):
    def __init__(self):
        super().__init__(timeout=None)


class SexualityView(View):
    def __init__(self):
        super().__init__(timeout=None)
