import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
import variables
from uwufier import Uwuifier
from pytimeparse.timeparse import timeparse

uwu = Uwuifier()

def generate_discord_relative_timestamp(seconds):
    # Calculate the future Unix timestamp
    future_timestamp = int((datetime.now() + timedelta(seconds=seconds)).timestamp())

    # Format the relative timestamp in the Discord style
    formatted_timestamp = f"<t:{future_timestamp}:R>"

    return formatted_timestamp

class ModerateCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Moderate")
    async def moderate(self, inter: disnake.MessageCommandInteraction):
        # Store message
        message = inter.target
        
        # Send initial response message
        prompt = disnake.Embed(
            title="Moderate this message",
            description="Select a moderation option below. The message will be deleted when you select an option.",
            colour=disnake.Colour.orange()
        ).add_field("Message Content",f"`{message.content}`",inline=False).add_field("Message Author",f"{message.author.global_name} ({message.author.id})",inline=False)
        await inter.response.send_message(embed=prompt,view=ModActions(message),ephemeral=True)
        
# Defines a simple view of row buttons.
class ModActions(disnake.ui.View):
    def __init__(self, message: disnake.Message):
        self.responded = False
        self.message = message
        super().__init__(timeout=None)

    @disnake.ui.button(label="Delete (automatic)", style=disnake.ButtonStyle.green)
    async def delete(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.responded:
            self.responded = True
            await self.message.delete()
            conf = disnake.Embed(
                title="Message deleted",
                description=f"The message from {self.message.author.mention} was deleted. No further moderation actions have taken place. ",
                colour= disnake.Colour.red()
            )
            await inter.response.send_message(embed=conf,ephemeral=True)
        else:
            await inter.response.send_message("This has already been responded to before.",ephemeral=True)
    
    @disnake.ui.button(label="Warn", style=disnake.ButtonStyle.gray)
    async def warn(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.responded:
            self.responded = True
            await self.message.delete()
            await inter.response.send_modal(WarnModal(self.message))
        else:
            await inter.response.send_message("This has already been responded to before.",ephemeral=True)
    
    @disnake.ui.button(label="Mute", style=disnake.ButtonStyle.gray)
    async def mute(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.responded:
            self.responded = True
            await self.message.delete()
            await inter.response.send_modal(MuteModal(self.message))
        else:
            await inter.response.send_message("This has already been responded to before.",ephemeral=True)
    
    @disnake.ui.button(label="Ban", style=disnake.ButtonStyle.gray)
    async def ban(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not self.responded:
            self.responded = True
            await self.message.delete()
            await inter.response.send_modal(BanModal(self.message))
        else:
            await inter.response.send_message("This has already been responded to before.",ephemeral=True)
    
class WarnModal(disnake.ui.Modal):
    def __init__(self, message: disnake.Message) -> None:
        self.member = message.author
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Warn Message",
                placeholder="Don't do a silly like that.",
                custom_id="message",
                style=disnake.TextInputStyle.long
            )
        ]
        super().__init__(title="Warn User", custom_id="warn", components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        reason = uwu.uwuify_sentence(inter.text_values["message"]) if self.member.id == 711944262173982822 else inter.text_values["message"]
        try:
            await self.member.send(
                embed=disnake.Embed(
                    title="You have been warned.",
                    color=disnake.Color.orange(),
                    description=f"You have recieved a warning in Datapack Hub.",
                    timestamp=datetime.now(),
                )
                .add_field("Warn Message",reason,inline=False)
                .add_field("Infringing Message",f"`{self.message.clean_content}`",inline=False)
            )
        except disnake.errors.Forbidden:
            await inter.response.send_message(
                f"I could not warn {self.member.mention} because either they have not enabled DMs from this server, or they have blocked the bot. Either way, they are a skibidi rizzler.",
                ephemeral=True,
            )
        except Exception as e:
            await inter.response.send_message(
                f"Failed to warn user {self.member.mention}: `{' '.join(e.args)}`",
                ephemeral=True,
            )
        else:
            conf = disnake.Embed(
                title="User Warned",
                description=f"Successfully deleted the message from and warned user {self.member.mention} for reason:```\n{reason}```",
                colour= disnake.Colour.red()
            )
            await inter.response.send_message(embed=conf,ephemeral=True)
            
            await inter.guild.get_channel(variables.modlogs).send(
                embed=disnake.Embed(
                    title="User Warned",
                    description=f"{self.member.name} (UID {self.member.id}) was warned.",
                    color=disnake.Color.red(),
                )
                .set_author(name=inter.author.global_name, icon_url=inter.author.avatar.url)
                .add_field("Warn Message", reason, inline=False)
                .add_field("Infringing Message", f"`{self.message.clean_content}`", inline=False)
            )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message("Oops, something went wrong.", ephemeral=True)
        
class MuteModal(disnake.ui.Modal):
    def __init__(self, message: disnake.Message) -> None:
        self.member = message.author
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Mute Message",
                placeholder="Don't do a silly like that.",
                custom_id="message",
                style=disnake.TextInputStyle.long
            ),
            disnake.ui.TextInput(
                label="Mute Length (max two weeks)",
                placeholder="4h",
                custom_id="length",
                style=disnake.TextInputStyle.short
            )
        ]
        super().__init__(title="Mute User", custom_id="mute", components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        reason = uwu.uwuify_sentence(inter.text_values["message"]) if self.member.id == 711944262173982822 else inter.text_values["message"]
        length = inter.text_values["length"]
        seconds = timeparse(length)
        
        try:
            await self.member.timeout(duration=seconds, reason=reason)
        except disnake.errors.Forbidden:
            await inter.response.send_message(f"Failed to mute user {self.member.mention}: I don't have permission to do this.",ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"Failed to mute user {self.member.mention}: `{' '.join(e.args)}`",ephemeral=True)
        else:
            conf = disnake.Embed(
                title="User Muted",
                description=f"Successfully deleted the message from and muted user {self.member.mention} for reason:```\n{reason}```",
                colour= disnake.Colour.red()
            )
            await inter.response.send_message(embed=conf,ephemeral=True)
            
            await self.member.send(
                embed=disnake.Embed(
                    title=f"You were muted in Datapack Hub for {length}.",
                    color=disnake.Color.red(),
                    description=f"You were banned in Datapack Hub.",
                    timestamp=datetime.now(),
                )
                .add_field("Reason",reason,inline=False)
                .add_field("You'll be unmuted:",generate_discord_relative_timestamp(seconds),inline=False)
                .add_field("Infringing Message",f"`{self.message.clean_content}`",inline=False)
            )
            
            
            
            await inter.guild.get_channel(variables.modlogs).send(embed=disnake.Embed(
                title="User Muted",
                description=f"{self.member.name} (UID {self.member.id}) was muted.",
                color=disnake.Color.red(),
            )
            .set_author(name=inter.author.global_name, icon_url=inter.author.avatar.url)
            .add_field("Reason", reason, inline=False)
            .add_field("Expires",generate_discord_relative_timestamp(seconds),inline=False)
            .add_field("Length",length,inline=False)
            .add_field("Infringing Message", f"`{self.message.clean_content}`", inline=False)
            )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message("Oops, something went wrong.", ephemeral=True)
        
class BanModal(disnake.ui.Modal):
    def __init__(self, message: disnake.Message) -> None:
        self.member = message.author
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Ban Message",
                placeholder="Don't do a silly like that.",
                custom_id="message",
                style=disnake.TextInputStyle.long
            ),
            disnake.ui.TextInput(
                label="Delete Messages?",
                placeholder="Leave blank for yes, or enter anything for no",
                custom_id="delete",
                style=disnake.TextInputStyle.short
            )
        ]
        super().__init__(title="Ban User", custom_id="ban", components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        reason = uwu.uwuify_sentence(inter.text_values["message"]) if self.member.id == 711944262173982822 else inter.text_values["message"]
        delete = not bool(inter.text_values["message"].strip())
        
        await self.member.send(
            embed=disnake.Embed(
                title="You were banned",
                color=disnake.Color.red(),
                description=f"You were banned in Datapack Hub.",
                timestamp=datetime.now(),
            )
            .add_field("Reason",reason,inline=False)
            .add_field("Infringing Message",f"`{self.message.clean_content}`",inline=False)
        )
        
        try:
            if delete:
                await self.member.ban()
            else:
                await self.member.ban(clean_history_duration=0)
        except disnake.errors.Forbidden:
            await inter.response.send_message(f"Failed to ban user {self.member.mention}: I don't have permission to do this.",ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"Failed to ban user {self.member.mention}: `{' '.join(e.args)}`",ephemeral=True)
        else:
            conf = disnake.Embed(
                title="User Banned",
                description=f"Successfully deleted the message from and banned user {self.member.mention} for reason:```\n{reason}```",
                colour= disnake.Colour.red()
            )
            await inter.response.send_message(embed=conf,ephemeral=True)
            
            await inter.guild.get_channel(variables.modlogs).send(embed=disnake.Embed(
                title="User Banned",
                description=f"{self.member.name} (UID {self.member.id}) was banned.",
                color=disnake.Color.red(),
            )
            .set_author(name=inter.author.global_name, icon_url=inter.author.avatar.url)
            .add_field("Reason", reason, inline=False)
            .add_field("Infringing Message", f"`{self.message.clean_content}`", inline=False)
            )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message("Oops, something went wrong.", ephemeral=True)