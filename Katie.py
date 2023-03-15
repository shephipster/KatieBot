# General Imports
import html
import os
import re
import time
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
# from scipy.spatial import distance
import imagehash
import requests
import json

# Discord imports
import discord
from discord.ext import commands

# Cog Imports
from Cogs.Activities import Activities
from Cogs.Tags import Tags
from Cogs.Notifications import Notifications
from Cogs.Posts import Posts


# Web services
from Services import IQDBService, PybooruEmbedder, TwitterService

# Database
from SQL import Database

# Entities
from Entities import Post

# Define Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

load_dotenv()

# Bot secrets
TOKEN = os.getenv('KATIE_TOKEN')
DISCORD_API_KEY = os.getenv('KATIE_SECRET')

# General constants
postTTL = -1  # how long a post should be recorded before it is up for deletion. -1 for no time
repostDistance = 10  # how similar an image must be to be a repost. Smaller means more similar, account for Discord compression
EMBED_FIX_PREFIX = 'kira'
logFile = 'BotFiles/image_log.json'
logSizeLimit = 255

# Declare Bot
bot = commands.Bot(
    command_prefix='+',
    description="Katie is built to serve, no matter the request",
    intents=intents,
    case_insensitive=True
    )

# setup all pre-requirements for the bot


async def setup(bot):
    # Adding cogs
    await bot.add_cog(Activities(bot))
    await bot.add_cog(Tags(bot))
    await bot.add_cog(Posts(bot))
    Database.init()
    
    if not os.path.exists(logFile):
        with open(logFile, 'a') as file:
            file.write("{\n}")

	# if not os.path.exists(guildsFile):
	# 	with open(guildsFile, 'a') as file:
	# 		file.write("{\n}")


@bot.event
async def on_ready():
    activity = discord.Game(
        name="getting ready",
    )
    await bot.change_presence(activity=activity)
    await setup(bot)

    activity = discord.Game(
        name="Ready to serve"
    )
    await bot.change_presence(activity=activity)


@bot.event
async def on_message(message):
    channel = message.channel
    if message.author.bot == True:
        # This causes bot to by-pass the repost filter. Do we care? I don't, and who would notice
        return

    if "fuck you" in message.content.lower():
        if "kira" in message.content.lower():
            await channel.send("fuck me yourself, coward")
        else:
            await channel.send("fuck them yourself, coward")
    elif "fuck me" in message.content.lower():
        await channel.send("that's kinda gross dude")

    if not message.content or message.content[0] != '+':
        if message.attachments:
            for attachment in message.attachments:
                file = await attachment.to_file()
                file = file.fp
                data = await IQDBService.getInfoDiscordFile(file)
                if data != None and not 'error' in data:
                    tag_list = list(data['tags'])
                    tag_list.sort()
                    await Notifications.ping_people(message, tag_list, exempt_user=message.author)
                    # response = 'Tags for that are `' + '`,`'.join(tag_list) + '`'
                    # await channel.send(response)visua

                    if repostDetected(message.channel.guild, attachment.url):
                        await message.add_reaction(str('♻️'))
        elif message.embeds:
            for embed in message.embeds:
                imageLink = embed.url
                data = await IQDBService.getInfoUrl(imageLink)
                if data != None:
                    tag_list = data['tags']
                    await Notifications.ping_people(message, tag_list)
                    if repostDetected(message.channel.guild, imageLink):
                        await message.add_reaction(str('♻️'))

    await bot.process_commands(message)
    
@bot.event
async def on_message_edit(before, after):
    #If a message is edited from a standard Twitter link to a custom one, the bot will create an embed and post it in the channel. While not as pretty as vx/fx twitter, it doesn't rely on external websites
    #and everything is in-memory so it's not physically capable of spying on what you use it for. Other sites to come. Pixiv would be next but they don't have an api so...
    if re.search(f"https?://twitter.com/[a-zA-Z0-9]+/status/[0-9]+(\?[\S]+)*", before.content) != None and re.search(f"https?://{EMBED_FIX_PREFIX}twitter.com/[a-zA-Z0-9]+/status/[0-9]+(\?[\S]+)*", after.content) != None:
        parsed_text = re.search(
            f"(https?://twitter.com/[a-zA-Z0-9]+/status/[0-9]+)(\?[\S]+)*", before.content)
        parsed_text = parsed_text.group(1)
        tweet_meta = TwitterService.get_tweet_meta_from_link(parsed_text)
        embed_type = TwitterService.tweetType(tweet_meta['raw_data'])

        media = []
        media_urls = []
        is_gif = False
        is_video = False
        max_bitrate = 0
        max_bitrate_index = -1
        for entry in tweet_meta['raw_data']['includes']['media']:
            media.append(entry)
            if entry['type'] == 'animated_gif':
                is_gif = True
                for ind, url in enumerate(entry['variants']):
                    media_urls.append(url['url'])
                    if 'bit_rate' in url:
                        if max_bitrate > url['bit_rate']:
                            max_bitrate = url['bit_rate']
                            max_bitrate_index = ind
            elif entry['type'] == 'video':
                for ind, url in enumerate(entry['variants']):
                    media_urls.append(url['url'])
                    if 'bit_rate' in url:
                        if max_bitrate > url['bit_rate']:
                            max_bitrate = url['bit_rate']
                            max_bitrate_index = ind
                is_video = True
            else:
                media_urls.append(entry['url'])

        if not is_gif and not is_video:
            finalImage = TwitterService.genImageFromURL(media_urls)
            imgIo = BytesIO()
            finalImage = finalImage.convert("RGB")
            finalImage.save(imgIo, 'JPEG', quality=70)
            imgIo.seek(0)
            tempFile = discord.File(fp=imgIo, filename="image.jpeg")

            #create the custom embed
            #TODO: Replace avatar/image with the twitter poster's
            bot_avatar = bot.user.avatar_url
            bot_image = bot_avatar.BASE + bot_avatar._url

            #TODO: include more info if need be
            body = f"Original: {parsed_text} \n" + tweet_meta['raw_data']['data']['text'] + \
                f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + \
                            f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

            body = html.unescape(body)

            embed_obj = discord.Embed(
                colour=discord.Colour(0x5f4396),
                description=body,
                type="rich",
                url=parsed_text,
            )

            embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

            embed_obj.set_image(url="attachment://image.jpeg")
            await after.channel.send(file=tempFile, embed=embed_obj)
        elif is_gif:
            #Apparently Twitter hides gif urls, but not jpgs/pngs or videos
            #Gifs do include mp4 variants, so we'll use that
            bot_avatar = bot.user.avatar_url
            bot_image = bot_avatar.BASE + bot_avatar._url

            #TODO: include more info if need be
            body = f"Original: {parsed_text} \n" + tweet_meta['raw_data']['data']['text'] + \
                f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + \
                            f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

            embed_obj = discord.Embed(
                colour=discord.Colour(0x5f4396),
                description=body,
                type="rich",
                url=parsed_text,
            )
            embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

            embed_obj.set_image(url=media_urls[max_bitrate_index])
            await after.channel.send(embed=embed_obj)
            await after.channel.send(media_urls[max_bitrate_index])
        elif is_video:

            bot_avatar = bot.user.avatar_url
            bot_image = bot_avatar.BASE + bot_avatar._url

            #TODO: include more info if need be
            body = f"Original: {parsed_text} \n" + tweet_meta['raw_data']['data']['text'] + \
                f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + \
                            f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

            embed_obj = discord.Embed(
                colour=discord.Colour(0x5f4396),
                description=body,
                type="rich",
                url=parsed_text,
            )
            embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

            embed_obj.set_image(url=media_urls[max_bitrate_index])
            await after.channel.send(embed=embed_obj)
            await after.channel.send(media_urls[max_bitrate_index])

    elif after.content.startswith(EMBED_FIX_PREFIX + ':'):
        raw_content, meta_data = PybooruEmbedder.getFromUrl(before.content)
        bot_avatar = bot.user.avatar_url
        bot_image = bot_avatar.BASE + bot_avatar._url
        body = meta_data['title']
        embed_obj = discord.Embed(
                colour=discord.Colour(0x5f4396),
                description=body,
                type="rich",
                url=before.content,
            )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
        embed_url = before.content + "&is_embed=True"
        embed_obj.set_image(url=embed_url)
        await after.channel.send(embed=embed_obj)

def repostDetected(guild, file):
    #https://github.com/polachok/py-phash#:~:text=py-pHash%20Python%20bindings%20for%20libpHash%20%28http%3A%2F%2Fphash.org%2F%29%20A%20perceptual,file%20derived%20from%20various%20features%20from%20its%20content.

    image = Image.open(requests.get(file, stream=True).raw)
    hash = imagehash.phash(image)

    reposted = False
    latestPost = Post.Post(file, time.time(), str(hash), str(guild))

    f = open(logFile)
    data = json.load(f)
    f.close()

    #TODO: include embeds/urls

    for post in data:
        values = data[post]
        if postExpired(values['timePosted']):
            del data[post]
        elif values['guild'] == latestPost.guild:
            old_post_phash = values['phash']
            new_post_phash = latestPost.phash
            # dist = distance.hamming(old_post_phash, new_post_phash) * len(hash)
            dist = 0
            if old_post_phash != new_post_phash:
                # manually calculating hamming
                for ch1, ch2 in zip(old_post_phash, new_post_phash):
                    if ch1 != ch2:
                        dist += 1
                dist *= len(hash)
            if dist <= repostDistance:
                reposted = True
                break #already know it's a repost, don't need to keep checking

    if len(data) >= logSizeLimit:
        del data[0]

    data[len(data)] = latestPost

    with open(logFile, "w") as dataFile:
        json.dump(data, dataFile, indent=4, default=Post.Post.to_dict)
    return reposted

def postExpired(timePosted: float):
    if postTTL == -1:
        return False
    return time.time() - timePosted >= postTTL

bot.run(TOKEN)