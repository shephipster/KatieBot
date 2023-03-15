from discord.ext import commands
from discord import Embed, Interaction
import random

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def ping(self, ctx):
        message = "Pong"
        await ctx.channel.send(message)
        return
    
    @commands.command()
    async def dice(self, ctx, count:int, faces:int, iterations:int=1):
        for iter in range(0,iterations):
            message = f'Rolling {count}D{faces}'
            await ctx.channel.send(message)
            
            results = []
            total = 0
            message = "`Results:\n"
            for roll in range(0,count):
                results.append(str(random.randrange(1,faces+1)))
                total += int(results[roll])
                
            message += '|'.join(results) + '\n'
            message += f'Total: {total}`' 
            
            await ctx.channel.send(message)
            
        return
        
    @commands.command()
    async def random(self, ctx, *options:str):
        selection = random.randrange(0, len(options))
        message = 'Alright, I\'m gonna go with ' + options[selection]
        await ctx.channel.send(message)
        return
    
    @commands.command()
    async def randomMulti(self, ctx, choices:int, *options:str):
        selections = list()
        for i in range (0,choices):
            number = random.randrange(0, len(options))
            selections.append(options[number])
        message = 'Alright, I\'m gonna go with ' + ','.join(selections)
        await ctx.channel.send(message)