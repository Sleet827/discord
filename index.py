import disnake
from disnake.ext import commands, tasks
from bottoken import TOKEN
import variables
import time
from datetime import datetime, timedelta, timezone

# Events
from cogs.events.thread_create import OnThreadCreate
from cogs.events.button_click import OnButtonClick
from cogs.events.message import OnMessage
from cogs.events.on_member_join import OnMemberJoin
from cogs.events.logs import Logs

# Message Commands
from cogs.message_commands.redirect import RedirectCommand
from cogs.message_commands.remind import RemindCommand
from cogs.message_commands.view import ViewFileCommand
from cogs.message_commands.moderate import ModerateCommand
from cogs.message_commands.report import ReportCommand

# Slash Commands
from cogs.commands.resolve import ResolveCommand
from cogs.commands.summon import SummonCommand
from cogs.commands.stats import StatsCommand
from cogs.commands.members import MembersCommand
from cogs.commands.site import SiteCommand
from cogs.commands.mod import ModCommand
from cogs.commands.top import TopCommand

# Setup bot
intents = disnake.Intents.all()

bot = commands.Bot(
    command_prefix="nerds",
    activity=disnake.Activity(
        name="Datapack Jam",
        url="https://datapackhub.net",
        type=disnake.ActivityType.competing,
    ),
    test_guilds=[variables.guild],
    intents=disnake.Intents.all(),
)

# Events
bot.add_cog(OnThreadCreate(bot))
bot.add_cog(OnButtonClick(bot))
bot.add_cog(OnMemberJoin(bot))
bot.add_cog(OnMessage(bot))
bot.add_cog(Logs(bot))

# Slash Commands
bot.add_cog(ModCommand(bot))
bot.add_cog(ResolveCommand(bot))
bot.add_cog(StatsCommand(bot))
bot.add_cog(SummonCommand(bot))
bot.add_cog(SiteCommand(bot))
bot.add_cog(TopCommand(bot))
bot.add_cog(MembersCommand(bot))

# Message Commands
bot.add_cog(RedirectCommand(bot))
bot.add_cog(RemindCommand(bot))
bot.add_cog(ModerateCommand(bot))
bot.add_cog(ViewFileCommand(bot))
bot.add_cog(ReportCommand(bot))

# Loops
@tasks.loop(minutes=10)
async def ten():
    channel_asked = bot.get_channel(variables.stats_asked)
    total_threads = 0
    for i in variables.help_channels:
        questions = bot.get_channel(i).threads.__len__()
        archived_qns = await bot.get_channel(i).archived_threads(limit=None).flatten()
        for _ in bot.get_channel(i).threads:
            total_threads += 1
        questions = questions + archived_qns.__len__()

        for thread in archived_qns:
            creation_unix = time.mktime(thread.create_timestamp.timetuple())
            if creation_unix >= 1674615000:
                total_threads += 1

    await channel_asked.edit(name=f"Questions Asked: {total_threads}")

@tasks.loop(hours=12)
async def day():
    for i in variables.help_channels:
        for thread in bot.get_channel(i).threads:
            last = await thread.history(limit=1).flatten()
            last = last[0]
            if last:
                diff = datetime.now(timezone.utc) - last.created_at
                if diff > timedelta(days=2):
                    await thread.send(
                        embed=disnake.Embed(
                            title="🗑️ Recycling Thread",
                            description="This thread has been inactive for some time, so I'm going to archive it.\n\nIf you're still using the thread, just send a message and it'll pop back on the thread list.",
                            color=disnake.Color.dark_gray(),
                        )
                    )
                    await thread.edit(archived=True)

                    # Logging
                    embed = disnake.Embed(
                        color=disnake.Colour.orange(),
                        title=("Recycled Thread"),
                        description=(
                            f"[{thread.name}]({thread.jump_url}) was archived for 2+ day inactivity."
                        ),
                    )
                    channel = bot.get_channel(variables.logs)
                    await channel.send(embed=embed)


@bot.event
async def on_ready():
    print("Bot has started!")
    day.start()
    ten.start()


bot.run(TOKEN)

# oldest resolved thread timestamp 1674615000
