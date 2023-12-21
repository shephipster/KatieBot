import aiohttp
import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()

GELBOORU_URL = "http://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&id={0}{1}"
GELBOORU_MD5_URL = "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=md5%3a{0}{1}"

#Don't think the key is needed for GET
GELBOORU_KEY = os.getenv('GELBOORU_API_KEY')

def getTagsFromId(id):
    #finalString = GELBOORU_URL.format(GELBOORU_KEY, id)
    finalString = GELBOORU_URL.format(id, '')
    resp = requests.get(finalString)
    respJson = resp.json()
    tagStr = ""

    if 'post' in respJson:
        items = respJson['post'][0].items()
        for i in items:
            if('tags' in i):
                tagStr = i[1]

    tags = set()

    #Gelbooru returns the results as an array since you can technically look up multiple things at once. This is to future-proof
    #things and prevent duplicate tags while getting them all, just in case this Service allows multiple concurrent lookups
    tagList = str.split(tagStr)
    for tag in tagList:
        tags.add(tag)

    return tags

async def getTagsFromMD5(md5):
    finalString = GELBOORU_MD5_URL.format(md5, '')
    async with aiohttp.ClientSession() as session:
        async with session.get(finalString, ssl=False) as r:
            respJson = await r.json()

    tagStr = ""
    if 'post' in respJson:
        items = respJson['post']
        for i in items:
            if('tags' in i):
                tagStr = i['tags']

    tags = set()

    #Gelbooru returns the results as an array since you can technically look up multiple things at once. This is to future-proof
    #things and prevent duplicate tags while getting them all, just in case this Service allows multiple concurrent lookups
    tagList = str.split(tagStr)
    for tag in tagList:
        tags.add(tag)

    return tags

def getTagsFromMD5Sync(md5):
    finalString = GELBOORU_MD5_URL.format(md5, '')
    respJson = requests.get(finalString).json()

    tagStr = ""
    if 'post' in respJson:
        items = respJson['post']
        for i in items:
            if('tags' in i):
                tagStr = i['tags']

    tags = set()

    #Gelbooru returns the results as an array since you can technically look up multiple things at once. This is to future-proof
    #things and prevent duplicate tags while getting them all, just in case this Service allows multiple concurrent lookups
    tagList = str.split(tagStr)
    for tag in tagList:
        tags.add(tag)

    return tags

def checkMD5(md5):
    finalString = GELBOORU_MD5_URL.format(md5, '')
    resp = requests.get(finalString)
    respJson = resp.json()
    if 'post' in respJson:
        return md5

async def getRandomSetWithTags(*tags):
    return await getSetWithTags('random', *tags)

async def getSetWithTags(order='random', *tags):
    from re import search
    limit = 500
    tag_list = []
    for tag in tags[0]:
        if search('limit:\d+', tag):
            limit = int(search(r'\d+', tag)[0])
        else:
            tag_list.append(tag)
    
    tagList = '%20'.join(tag_list)
    url = f"http://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit={limit}&tags=" + tagList + "&" + order
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as r:
            return await r.json()

async def getRandomPostWithTags(*tags):
    respJson = await getRandomSetWithTags(*tags)
    if 'post' in respJson.keys():
        randPost = random.randint(0, len(respJson['post']) - 1)
        post = respJson['post'][randPost]
        return post
    else:
        print("Tag not found")
        return None
