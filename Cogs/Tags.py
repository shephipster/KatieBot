# Adds, Removes, and otherwise manages user tags
from discord.ext import commands
import SQL.Database

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def showAll(self, ctx):
        user = ctx.author
        
        message = f'{user}, your tags are: `'
        tags = SQL.Database.getTags(ctx.author.id, ctx.guild.id)
        tag_str = '`,`'.join(tags)
        message += tag_str
        message += '`'
        await ctx.channel.send(message)
        return
    
    @commands.command()
    async def addTag(self, ctx, tag:str):
        """ Adds the tag to your list """
        SQL.Database.addTagToUser(tag, ctx)
        
    @commands.command()
    async def blockTag(self, ctx, tag:str):
        """ Add the tag to your blacklist """
        SQL.Database.addBlacklistToUser(tag, ctx)