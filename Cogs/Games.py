from discord.ext import commands

class Games(commands.Cog):
    '''
        Cog for DND and other tabletop features, including GREG'n it
    '''
    def __init__(self, bot):
        self.bot = bot        
    
    @commands.command(aliases=['class'])
    async def randomClass(self, ctx, game):
        picker = Classes()
        result = picker.random(game)
        await ctx.channel.send(result)
        
    @commands.command(aliases=['race'])
    async def randomRace(self, ctx, game):
        picker = Races()
        result = picker.random(game)
        await ctx.channel.send(result)
        
    @commands.command(aliases=['background'])
    async def randomClass(self, ctx, game):
        picker = Backgrounds()
        result = picker.random(game)
        await ctx.channel.send(result)
        
    @commands.command(aliases=['greg'])
    async def randomGREG(self, ctx, game):
        picker = Classes()
        class_result = picker.random(game)
        
        picker = Races()
        race_result = picker.random(game)
        
        picker = Backgrounds()
        background_result = picker.random(game)
        
        result = f'Class: {class_result}\nRace: {race_result}\nBackground: {background_result}'
        await ctx.channel.send(result)

     
class Classes():
    from random import choice
    options = {
        '5e': ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]
    }
    
    def __init__(self):
        pass
    
    def random(self, game:str):
        if game in self.options:
            return self.choice(self.options[game])
    
class Races():
    from random import choice
    options = {
        '5e': ["Dragonborn", 'Dwarf','Elf','Gnome','Half-Elf','Halfling','Half-Orc', 'Human','Tiefling']
    }
    
    def __init__(self):
        pass
    
    def random(self, game:str):
        if game in self.options:
            return self.choice(self.options[game])
        
class Backgrounds():
    from random import choice
    options = {
        '5e': ["Acolyte","Charlatan","Criminal", "Folk Hero","Guild Artisan","hermint","Outlander","Noble", "Sage","Sailor","Soldier","Urchin"]
    }
    
    def __init__(self):
        pass
    
    def random(self, game:str):
        if game in self.options:
            return self.choice(self.options[game])