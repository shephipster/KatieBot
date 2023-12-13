from discord.ext import commands
import discord
from SQL import Database

class Notifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def ping_people(message: discord.Message, tag_list, exempt_user=None):
        # go through each user in the current channel
        users = message.channel.members
        for user in users:
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
                await message.channel.send(ping_string)
                
        return