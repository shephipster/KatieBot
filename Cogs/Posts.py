import itertools
from random import randint
import re
import discord
from discord.ext import commands
# from .Notifications import ping_people #Caused import issues. Not ideal, but just copying the method
from Services import IQDBService
from Services.GelbooruService import getRandomSetWithTags as gelSet
from Services.DanbooruService import getRandomSetWithTags as danSet
from threading import Timer, Thread
from SQL import Database
import asyncio

# https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html#ext-commands-cogs

ROLL_LIMIT = 10
JOKE_MODE = False

class Posts(commands.Cog):
    '''
        Cog for fetching random posts from boorus, such as Gelbooru and/or Danbooru
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['randomimage','rollimage'])
    async def randomPost(self, ctx, *tags):
        # from SQL.Database import addLikedTag
        from SQL.Database import getBlacklist
        
        """Fetches a random post from multiple sites that contains the provided tag(s) and then displays it in a custom embed.

        Args:
            ctx (_type_): Context of the message, passed in automatically by discord.
        """
        orig_msg = await ctx.reply("Alright, gimme a second to find something for you...", mention_author=False)
        safe_exemptions = []
        nsfw_exemptions = []
        bannedTags = []
        bannedPorn = []
        
        cleaned_tags = []
        rolled_data_set = []
        combo_count = 1
        for tag in tags:
            multiplier = re.search(r'(x\d+|\d+x)', tag)
            if multiplier:
                combo_count = int(re.search(r'\d+', multiplier[0])[0])
            else:
                cleaned_tags.append(tag.replace('`', ''))
            
        
        if ctx.guild != None:   #originated from a guild, fetch the lists and exemptions
            guid = str(ctx.guild.id)
            cid = str(ctx.channel.id)
            
            data = {
                guid : {
                    'bannedExplicitTags' : ['loli', 'shota', 'bestiality', 'ugly_bastard'],   #TODO: Get guild banned porn tags
                    'bannedGeneralTags' : [''], #TODO: get guild banned tags
                    'channels':{
                        cid: {
                            'bannedTags' : [], #channel-specific blacklist
                            'bannedNSFWTags': [],
                            'safe_exemptions': [],
                            'nsfw_exemptions': [],
                        }
                    }
                }
            }
            # user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
            # if user == None or data == None:
            #     #there was an issue, break
            #     return -1   

            for tag in data[guid]['bannedExplicitTags']:
                bannedPorn.append(tag)
            for tag in data[guid]['bannedGeneralTags']:
                bannedTags.append(tag)
            for tag in data[guid]['channels'][cid]['bannedTags']:
                bannedTags.append(tag)
            for tag in data[guid]['channels'][cid]['bannedNSFWTags']:
                bannedPorn.append(tag)
                
            safe_exemptions = data[guid]['channels'][cid]['safe_exemptions']
            nsfw_exemptions = data[guid]['channels'][cid]['nsfw_exemptions']
            
            for tags in getBlacklist(user_id = ctx.author.id, guild_id=guid):
                bannedTags.append(tag)
        
            for i in range(combo_count):
                rolled_data = await self.getImageFromTags(banned_tags=bannedTags, banned_porn=bannedPorn, query_set=cleaned_tags,
                                                        safe_exemptions=safe_exemptions, nsfw_exemptions=nsfw_exemptions, channel_explicit=ctx.channel.is_nsfw() )
                rolled_data_set.append(rolled_data)
        else:   #from inside a dm. We'll assume they're fine with it
            for i in range(combo_count):
                rolled_data = await self.getImageFromTags(banned_tags=bannedTags, banned_porn=bannedPorn, query_set=cleaned_tags,
                                                    safe_exemptions=safe_exemptions, nsfw_exemptions=nsfw_exemptions, channel_explicit=True )
                rolled_data_set.append(rolled_data)

        if rolled_data_set == []:
            await ctx.reply("Sorry, couldn't find anything for you. Did you spell everything right?")
            return

        await orig_msg.delete()
        tasks = []
        for rolled_data in rolled_data_set:
            tasks.append(self.send_post(rolled_data, ctx))
        await asyncio.gather(*tasks) 
    
    async def send_post(self, rolled_data, ctx):
        sources = rolled_data['sources']
        image_url = rolled_data['image_url']
        tag_list = rolled_data['tag_list']
        is_explicit = rolled_data['is_explicit']
        title = rolled_data['title']
        
        if title != '' and title != None:
            description = 'Title: ' + title + '\n' + '\n'.join(sources)
        else:
            description = '\n'.join(sources)
        bot_image = self.bot.user.avatar.url
        

        #await ctx.channel.send("Alright, here's your random post. Don't blame me if it's cursed.")
        if image_url.endswith('.mp4'):
            embed_msg = await ctx.channel.send(image_url)

        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description=description,
            type="rich",
        )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
        embed_obj.set_image(url=image_url)

        
        embed_msg = await ctx.reply(embed=embed_obj)
        await embed_msg.add_reaction(str('♥'))

        await self.updateRolledImage(sources=sources, ctx=ctx, embed_msg=embed_msg, image_url=image_url, tag_list=tag_list, isExplicit=is_explicit, title=title, original_caller=ctx.message.author)        
        await asyncio.sleep(30)
        await self.delete_without_reactions(embed_msg)
        
        embed_msg = await embed_msg.fetch()
        
    
    async def delete_without_reactions(self, msg):
        embed_msg = await msg.fetch()
        delete = True
        for reaction in embed_msg.reactions:
            if reaction.count > 1 or not reaction.me:
                delete = False                
        if delete:
            await embed_msg.delete()
            
    #Blocking calls
    async def updateRolledImage(self, ctx, sources:list, embed_msg, image_url, tag_list, isExplicit, title=None, original_caller=None):
        extra_data = await IQDBService.getInfoUrl(image_url)
        bot_image = self.bot.user.avatar.url
        if extra_data != None:
            for url in extra_data['urls']:
                if url not in sources:
                    sources.append(url)
        
        if title in sources:
            sources.remove(title)
        for i in range(len(sources)):
            if re.match('https?://', sources[i]) == None and sources[1] != title:
                sources[i] = "https://" + sources[i]

        if title != '' and title != None:
            description = "Title: " + title + '\n' + '\n'.join(sources)
        else:
            # description = '\n'.join(sources)
            # was requested to make it tags instead
            description = ', '.join(f'`{tag}`' for tag in tag_list)

        #update embed

        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description=description,
            type="rich",
        )
        embed_obj.set_author(name="Katie Bot", icon_url=bot_image)
        embed_obj.set_image(url=image_url)
        if isExplicit and not ctx.channel.is_nsfw():
            pass
        else:
            embed_msg = await embed_msg.edit(embed=embed_obj)
        await ping_people(ctx, tag_list, exempt_user = original_caller)

        return embed_msg
    
    @commands.command(pass_context=True, aliases=['randomporn', 'randomexplicit', 'rollporn', 'nsfw'], nsfw=True)
    async def randomNsfw(self, ctx, *tags):
       if not ctx.channel.is_nsfw():
           await ctx.channel.send("Sorry, I can't roll NSFW in a channel that's not age-restricted. Try randomPost or randomSafe instead.")
           return
       await ctx.invoke(self.bot.get_command('randomPost'), 'rating:explicit', *tags)

    
    @commands.command(pass_context=True, aliases=['randomsafe', 'rollsafe', 'sfw'])
    async def randomSfw(self, ctx, *tags):
        await ctx.invoke(self.bot.get_command('randomPost'), 'rating:general', *tags)


    def mistakenTagSearcher(self, tags:list):
        search_set = []
        for p in itertools.product([True, False], repeat=len(tags)):
            search_term = []
            params = list(zip(tags, p))
            for entry in params:
                if entry[1] and len(entry[0].split('_') ) == 2:
                    spl = entry[0].split('_')
                    spl = spl[1] + '_' + spl[0]
                    search_term.append(spl)
                else:
                    search_term.append(entry[0])
            search_set = sorted(search_set)
            if search_term not in search_set:
                search_set.append(search_term)
                
        return search_set
    
    async def getImageFromTags(self, banned_tags:list, banned_porn:list, query_set:list, safe_exemptions:list, nsfw_exemptions:list, channel_explicit:bool):
        #TODO: overhaul the randompost to call this
        
        data = {
            'sources': [],
            'image_url': "",
            'tag_list': [],
            'is_explicit': False,
            'title': None
        }
        
        search_set = self.mistakenTagSearcher(query_set)
        for entry in search_set:
            randomDanSet = await danSet(entry)
            randomGelSet = await gelSet(entry)

            if 'post' in randomGelSet:
                randomGelSet = randomGelSet['post']
                
            if 'success' in randomDanSet and randomDanSet['success'] == False:
                randomDanSet = []
            
            full_set = []
            for entry in randomDanSet:
                full_set.append((entry, 'dan'))
            if '@attributes' not in randomGelSet or randomGelSet['@attributes']['count'] != 0:
                for entry in randomGelSet:
                    full_set.append((entry, 'gel'))
            
            if len(full_set) == 0:
                continue    #no results, move to next one

            for i in range(ROLL_LIMIT):

                rolled_number = randint(0, len(full_set) - 1)            
                random_item = full_set[rolled_number]

                try:
                    if random_item[1] == 'dan':
                        tag_list = random_item[0]['tag_string'].split()
                        if 'file_url' in random_item[0]:
                            image_url = random_item[0]['large_file_url'] 
                            data['title'] = random_item[0]['source'] if not isURL(random_item[0]['source']) else ''
                        else:
                            image_url = random_item[0]['source']
                        isExplicit = random_item[0]['rating'] == 'e'
                    elif random_item[1] == 'gel':
                        tag_list = random_item[0]['tags'].split()
                        image_url = random_item[0]['file_url']
                        isExplicit = random_item[0]['rating'] == 'explicit'
                except Exception as e:
                    print(randomDanSet)
                    print(random_item)
                    print(e)
                    
                marked_tags = []
                for tag in tag_list:
                    if tag in banned_tags:
                        if not any([tag, '*all*'] in exemption for exemption in safe_exemptions ):
                            marked_tags.append(tag)
                    if isExplicit and tag in banned_porn: 
                        if not any([tag, '*all*'] in exemption for exemption in nsfw_exemptions):               
                            marked_tags.append(tag)
                if marked_tags != []:
                    for tag in tag_list:
                        if marked_tags == []:
                            break   #reduce cost measure
                        else:    
                            for marked_tag in marked_tags:
                                test_pair = [tag, marked_tag]
                                if any(test_pair == exemption for exemption in safe_exemptions) and not isExplicit:
                                    marked_tags.remove(marked_tag)
                                if any(test_pair == exemption for exemption in nsfw_exemptions) and isExplicit:
                                    marked_tags.remove(marked_tag)
                
                if isExplicit and not channel_explicit:
                    continue
                            
                if marked_tags != []:
                    continue
                
                #if still here then the image has passed and can be returned

                sources = []

                if random_item[1] == 'gel':
                    post_id = random_item[0]['id']
                    sources.append(random_item[0]['source'])
                    sources.append(
                                f'https://gelbooru.com/index.php?page=post&s=view&id={ post_id }')
                    image_url = random_item[0]['file_url']
                elif random_item[1] == 'dan':
                    if 'id' in random_item[0]:
                        post_id = random_item[0]['id'] 
                        sources.append(f'https://danbooru.donmai.us/posts/{post_id}')
                        sources.append(random_item[0]['source']) if isURL(random_item[0]['source']) else ''
                    else:
                        continue                    
                    if 'file_url' in random_item[0]:
                        image_url = random_item[0]['file_url']
                    else:
                        continue
            
                for source in sources:
                    if source.strip() == '':
                        sources.remove(source)
                        
                data['image_url'] = image_url
                data['is_explicit'] = isExplicit
                data['sources'] = sources
                data['tag_list'] = tag_list
                return data
                
        return None
    
def isURL(query:str):
    isUrl = False
    isUrl = isUrl | (re.search("https?://", query) != None)
    isUrl = isUrl | (re.search(".com", query) != None)
    isUrl = isUrl | (re.search(".net", query) != None)
    isUrl = isUrl | (re.search(".org", query) != None)
    isUrl = isUrl | (re.search(".gov", query) != None)
    return isUrl

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

        if bool(set(tag_list) & set(blacklist)):
            #blacklisted tag, don't ping them
            continue
        
        for tag in tag_list:
            if tag in whitelist:
                matches.append(tag)
        # if tags match ping tags add set
        if len(matches):
            ping_string = f'<@{user.id}> for `' + '`,`'.join(matches) + '`'
            await message.channel.send(ping_string)
            
    return