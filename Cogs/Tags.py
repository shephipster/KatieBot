# Adds, Removes, and otherwise manages user tags
from discord.ext import commands
import discord
import SQL.Database
from Services import IQDBService
import re

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=['myTags','listTags','lists'])
    async def showAll(self, ctx):
        user = ctx.author
        
        message = f'{user}, your tags are: `'
        tags = SQL.Database.getTags(ctx.author.id, ctx.guild.id)
        tag_str = '`,`'.join(tags)
        message += tag_str
        message += '`'
        await ctx.channel.send(message)
        
        message = f'{user}, your blocked tags are: `'
        tags = SQL.Database.getBlacklist(ctx.author.id, ctx.guild.id)
        tag_str = '`,`'.join(tags)
        message += tag_str
        message += '`'
        await ctx.channel.send(message)
        return
    
    @commands.command()
    async def addTag(self, ctx, *tags:str):
        """ Adds the tag to your list """
        for tag in tags:
            SQL.Database.addTagToUser(tag, ctx)
            await ctx.message.channel.send(f'{tag} is now part of your liked tags')
            
    @commands.command()
    async def removeTag(self, ctx, *tags:str):
        for tag in tags:
            SQL.Database.removeTagFromUser(tag, ctx)
            await ctx.message.channel.send(f'{tag} is gone from your liked tags')
        
    @commands.command()
    async def blockTag(self, ctx, *tags:str):
        """ Add the tag to your blacklist """
        for tag in tags:
            SQL.Database.addBlacklistToUser(tag, ctx)
            SQL.Database.removeTagFromUser(tag, ctx)
            await ctx.message.channel.send(f'{tag} is now part of your blocked tags')
        
    @commands.command(aliases=['sauce', 'urls', 'sites'])
    async def source(self, ctx):
        if not ctx.message.attachments:
            await ctx.channel.send("You have to give me an image to look up you know.")
        else:
            await ctx.channel.send("Alright, lemme see if I can't find out where these are from...")
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                file_url = attachment.url
                file = file.fp
                data = await IQDBService.getInfoDiscordFile(file)
                if 'error' in data.keys():
                    await ctx.channel.send(f"Sorry, I had trouble finding that. You can try checking SauceNao here: {data['sauceNao_redirect']}")
                    return

                cleaned_urls = []
                for url in data['urls']:
                    if re.match('https?://', url) == None:
                        cleaned_urls.append('https://' + url)
                    else:
                        cleaned_urls.append(url)

                description = "Sources:\n" + '\n'.join(cleaned_urls)
                bot_avatar = self.bot.user.avatar
                bot_image = bot_avatar._url
                embed_obj = discord.Embed(
                    colour=discord.Colour(0x5f4396),
                    description=description,
                    type="rich",
                )
                embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
                embed_obj.set_image(url=file_url)

                # url_list = data['urls']
                # output = "Found that image at the following sites:\n "
                # for url in url_list:
                # 	output = output + "http://" + url + "\n"

                # await ctx.channel.send(output)
                await ctx.reply(embed=embed_obj)
                
    @commands.command(aliases=['showTags','tagsFor'])
    async def tags(self, ctx):
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                file = file.fp
                data = await IQDBService.getInfoDiscordFile(file)
                if data != None and not 'error' in data:
                    tag_list = list(data['tags'])
                    tag_list.sort()                    
                    description = ', '.join(f'`{tag}`' for tag in tag_list)
                else:
                    description = "I couldn't get any results from IQDB for that. What niche shit you giving me?"
                    if 'sauceNao_redirect' in data:
                        description += f"\nAt least see if this helps: {data['sauceNao_redirect']}"
                
                embed_obj = discord.Embed(
                        colour=discord.Colour(0x5f4396),
                        description=description,
                        type="rich",
                    )
                bot_image = self.bot.user.avatar.url
                embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
                embed_obj.set_image(url=attachment)
                await ctx.message.channel.send(embed=embed_obj)