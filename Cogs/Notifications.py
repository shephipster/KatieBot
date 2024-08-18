from discord.ext import commands, tasks
import discord
from datetime import datetime as dt
from datetime import timezone as tz
from datetime import time
from SQL import Database

class Notifications(commands.Cog):
    
    times = [
        time(hour=3, tzinfo=tz.utc)
    ]
    
    def __init__(self, bot):
        self.bot = bot
        self.check_event_helper.start()
        
    async def ping_people(message: discord.Message, tag_list, exempt_user=None):
        # go through each user in the current channel
        users = message.channel.members
        guild = message.channel.guild
        pingable_users = Database.getPingableUsers(guild = guild)
        pinged_users = []
        for user in pingable_users:
            if user == exempt_user:
                continue
            # fetch their tags
            blacklist = []
            whitelist = []
            matches = []
            user_tags = Database.getAllTags(user_id = user.id, guild_id = message.guild.id)
            for tag in user_tags:
                if tag[1]:
                    blacklist.append(tag[0])
                else:
                    whitelist.append(tag[0])
            # if tags match blacklist exempt them (continue)
            if not tag_list:
                return

            # Not the most efficient method, but given the small usage of the bot optimization can wait
            for tag in tag_list:
                if tag in blacklist:
                    continue
            
            for tag in tag_list:
                if tag in whitelist:
                    matches.append(tag)
            # if tags match ping tags add set
            if len(matches):
                ping_string = f'<@{user.id}> for `' + '`,`'.join(matches) + '`'
                pinged_users.append(user.id)
                await message.channel.send(ping_string)
        
        if pinged_users:
            Database.updatePingedUsers(pinged_users, guild=guild)
        return
    
    async def check_events(guild: discord.Guild):
        current_time = dt.now()
        scheduledEvents = await guild.fetch_scheduled_events()
        for event in scheduledEvents():
            event: discord.ScheduledEvent
            
            # generate and embedded message for image reasons
            #not really needed, but I want an excuse to use them again
            time_left = (event.start_time - current_time)
            time_range = 'day(s)' if time_left.days else 'hour(s)'
            time_amount = time_left.days if time_left.days else time_left.hours
            body = f'Only {time_amount} {time_range} remain until {event.name}'
            
            bot_avatar = Notifications.bot.user.avatar_url
            bot_image = bot_avatar.BASE + bot_avatar._url
            
            embed_obj = discord.Embed(
                colour=discord.Colour(0x5f4396),
                description=body,
                type="rich",
                url=event.url,
            )

            embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
            embed_obj.set_image(url=event.cover_image.url)
            await event.channel.send(embed=embed_obj)
        
    # @tasks.loop(time=times)
    @tasks.loop(seconds=5)
    async def check_event_helper():
        print('Running event checker')
        guilds = [guild async for guild in Notifications.bot.fetch_guilds()]
        for guild in guilds:
            await Notifications.check_events(guild)