import os
from dotenv import load_dotenv

import discord
import asyncio

from discord.ext import commands
from discord.utils import get

import random
import re


load_dotenv()

TOKEN = os.getenv('TOKEN') 

intents = discord.Intents().all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def create_server(ctx, num_teams:int, num_rounds:int, num_rooms:int, schedule:list):
   s = Server(ctx=ctx, num_rooms=num_rooms, num_rounds=num_rounds, schedule=schedule, num_teams=num_teams)
   await s._create_server_elements(ctx=ctx, num_rooms=num_rooms, num_rounds=num_rounds, schedule=schedule, num_teams=num_teams)
   return s
class Server:
   def __init__(self, ctx, num_teams:int, num_rounds:int, num_rooms:int, schedule:list):
      self._schedule = schedule
      self._ctx = ctx
      self._num_teams = num_teams
      self._num_rounds = num_rounds
      self._num_rooms = num_rooms

   async def _create_server_elements(self, ctx, num_teams:int, num_rounds:int, num_rooms:int, schedule:list):
      await self.create_roles(ctx=ctx, num_teams=num_teams)
      await self.create_standard_rooms(ctx=ctx, num_rooms=num_rooms)
      await self.create_game_rooms(ctx=ctx, num_rooms=num_rooms, num_rounds=num_rounds)
      await self.set_permissions(ctx=ctx, num_rooms=num_rooms, num_rounds=num_rounds, schedule=schedule)
   
   async def create_roles(self, ctx, num_teams: int):
      guild = ctx.guild

      await ensure_presence_of_bot_channels(ctx)
      bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')
      bot_actions = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-actions')

      for i in range(1, num_teams+1):
         team_name = f'Team {i}'

         await guild.create_role(name = team_name, color = discord.Colour(random.randint(0, 0xffffff)))

         await bot_actions.send(
            f'Created role Team {i}', 
         )

      for i in range (1, int((num_teams/2))+1):
            staff_name = f'Room {i} Staff'
            await guild.create_role(name = staff_name, color = discord.Colour(0xFFD700))
            await bot_actions.send(
               f'Created role Room {i} Staff ',
            )

   async def create_standard_rooms(self, ctx, num_rooms: int):
      guild = ctx.guild

      await ensure_presence_of_bot_channels(ctx)
      bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')
      bot_actions = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-actions')

      # default no-read permissions
      def_text_permissions = {
            guild.default_role: discord.PermissionOverwrite(read_messages = False),
            guild.me: discord.PermissionOverwrite(read_messages = True)
      }
      def_voice_permissions = {
            guild.default_role: discord.PermissionOverwrite(view_channel = False),
            guild.me: discord.PermissionOverwrite(view_channel = True)
      }

      # read-only permissions
      read_text_permissions = {
            guild.default_role: discord.PermissionOverwrite(read_messages = True, send_messages = False),
      }
   
      # create staff rooms
      await guild.create_category("staff-only")
      category = discord.utils.get(ctx.guild.categories, name="staff-only")
      await guild.create_text_channel("staff-chat", category=category, overwrites=def_text_permissions)
      await guild.create_voice_channel("staff-voice", category=category, overwrites=def_voice_permissions)

      text_channel = discord.utils.get(guild.text_channels, name = f'staff-chat')
      voice_channel = discord.utils.get(guild.voice_channels, name = f'staff-voice')

      # assign all staff roles to staff rooms
      for i in range (1, num_rooms+1):
         await text_channel.set_permissions(get(guild.roles, name = f'Room {i} Staff'), read_messages = True, send_messages = True)
         await voice_channel.set_permissions(get(guild.roles, name = f'Room {i} Staff'), view_channel = True, connect = True, speak = True)

      # create general rooms
      await guild.create_category("general-info")
      category = discord.utils.get(ctx.guild.categories, name="general-info")
      await guild.create_text_channel("annoucements", category=category, overwrites=read_text_permissions)
      await guild.create_text_channel("stats", category=category, overwrites=read_text_permissions)
      await guild.create_voice_channel("opening_meeting", category=category)


   async def create_game_rooms(self, ctx, num_rounds: int, num_rooms: int):
      guild = ctx.guild

      await ensure_presence_of_bot_channels(ctx)
      bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')
      bot_actions = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-actions')

      def_text_permissions = {
            guild.default_role: discord.PermissionOverwrite(read_messages = False),
            guild.me: discord.PermissionOverwrite(read_messages = True)
      }
      def_voice_permissions = {
            guild.default_role: discord.PermissionOverwrite(view_channel = False),
            guild.me: discord.PermissionOverwrite(view_channel = True)
      }

      for i in range(1, num_rounds+1):
         category_name = f'round{i}'
         await guild.create_category(category_name)
      
         for j in range(1, num_rooms+1):
            category = discord.utils.get(ctx.guild.categories, name=category_name)
            channelname = f'round{i}_room{j}'
            await guild.create_text_channel(channelname, category=category, overwrites=def_text_permissions)   
            await guild.create_voice_channel(channelname, category=category, overwrites=def_voice_permissions)

            await bot_actions.send(
               f'Created {channelname}', 
            )

   async def set_permissions(self, ctx, num_rooms: int, num_rounds: int, schedule: list):
      guild = ctx.guild

      await ensure_presence_of_bot_channels(ctx)
      bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')
      bot_actions = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-actions')

      match = 0

      for i in range (1, num_rounds+1):
         for j in range (1, num_rooms+1):
            team1 = get(guild.roles, name = f'Team {int(schedule[match])}')
            team2 = get(guild.roles, name = f'Team {int(schedule[match+1])}')

            text_channel = discord.utils.get(guild.text_channels, name = f'round{i}_room{j}')
            voice_channel = discord.utils.get(guild.voice_channels, name = f'round{i}_room{j}')

            await text_channel.set_permissions(team1, read_messages = True, send_messages = True)
            await text_channel.set_permissions(team2, read_messages = True, send_messages = True)

            await voice_channel.set_permissions(team1, view_channel = True, connect = True, speak = True)
            await voice_channel.set_permissions(team2, view_channel = True, connect = True, speak = True)
            
            await bot_actions.send (
               f'Assigned teams {int(schedule[match])} and {int(schedule[match+1])} to round{i}_room{j}',
            ) 
            match += 2
      
      for i in range (1, num_rounds+1):
         for j in range (1, num_rooms+1):
            staff = get(guild.roles, name = f'Room {j} Staff')

            text_channel = discord.utils.get(guild.text_channels, name = f'round{i}_room{j}')
            voice_channel = discord.utils.get(guild.voice_channels, name = f'round{i}_room{j}')

            await text_channel.set_permissions(staff, read_messages = True, send_messages = True)
            await voice_channel.set_permissions(staff, view_channel = True, connect = True, speak = True)

            await bot_actions.send (
               f'Set Room {j} Staff to round{i}_room{j}',
            )
   
async def ensure_presence_of_bot_channels(ctx):
   bot_actions = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-actions')
   bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')

   if bot_actions is None or bot_commands is None:
      await create_bot_channels(guild=ctx.guild, actions=bot_actions, commands=bot_commands)

async def create_bot_channels(guild, actions, commands):
   text_permissions = {
         guild.default_role: discord.PermissionOverwrite(read_messages = False),
         guild.owner: discord.PermissionOverwrite(read_messages = True),
   }

   # create channels only if they do not exist
   if actions is None:
      await guild.create_text_channel("quiz_bot-actions", overwrites=text_permissions)
   if commands is None:
      await guild.create_text_channel("quiz_bot-commands", overwrites=text_permissions)

   bot_actions = discord.utils.get(guild.text_channels, name="quiz_bot-actions")

   await bot_actions.send("All bot commands will need to go through the newly created\
   commands channel. Whenever quizbowl performs an action, it will be logged in the actions\
   channel. Currently, only the server owner can see these channels. Please do not delete\
   these channels.")   

@bot.event
async def on_guild_join(guild):
   await ensure_presence_of_bot_channels(guild, None, None)


@bot.command(name="create_server")
async def get_tournament_params(ctx):
   guild = ctx.guild
   bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')

   # the command must come either from the command channel or from the server owner
   if not ctx.channel == bot_commands and not ctx.message.author == ctx.guild.owner:
      await ctx.reply("You do not have permission to invoke this command")

   # make sure bot channels exist and get their references
   await ensure_presence_of_bot_channels(ctx)
   bot_commands = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-commands')
   bot_actions = discord.utils.get(ctx.guild.text_channels, name = f'quiz_bot-actions')

   text_permissions = {
         guild.default_role: discord.PermissionOverwrite(read_messages = False),
         guild.me: discord.PermissionOverwrite(read_messages = True)
   }
   voice_permissions = {
         guild.default_role: discord.PermissionOverwrite(view_channel = False),
         guild.me: discord.PermissionOverwrite(view_channel = True)
   }

   # confirm that the user has given valid input
   def schedule_check(message):
      schedule = message.content.split(" ")
      
      if not all(i.isdigit() for i in schedule):
         return commands.CheckFailure("Non-integer input")
      return True
   
   def react_check(reaction, user):
      if user == ctx.message.author and str(reaction.emoji) == '👍':
         return True 
      raise commands.CheckFailure("Non 👍 emoji recieved.")

   schedule_prompt = discord.Embed(
      title = "Please enter your tournament schedule. Remember the first elemet of your input should be the number of rounds.",
      description = "If you're not currently in the bot_commands channel, please go there now to continue.\
      If you're not sure how to enter the tournament's schedule, please see the README on the bot's github page @"
   )
   await ctx.send(embed=schedule_prompt)

   try:
      schedule = await bot.wait_for(
         "message",
         check = schedule_check
      )
   except commands.CheckFailure:
      await bot_actions.send(
         f'It appears you\'ve placed something that\'s not an integer in your schedule. Please double check your input and try again.'
      )
      return

   schedule = schedule.content.split(" ")

   num_rounds = int(schedule.pop(0))
   num_teams = int((len(schedule) / num_rounds))
   num_rooms = int(num_teams/2)

   confirm = discord.Embed(
      title = "I've generated the following tournament. React with the 👍 emoji to approve.",
      description =
      f"Number of teams = {num_teams}\n \n\
      Number of rounds = {num_rounds}\n \n\
      Reacting with the 👎 or waiting 60 seconds will cancel the create_server command."
   )
   await bot_commands.send(embed=confirm)

   # create schedule table here

   # check for user reaction confirming that they'd like to continue, return from function if check fails 
   try:
      reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=react_check)
   except asyncio.TimeoutError:
      await bot_commands.send("!create_server command timed out.")
      return
   except commands.CheckFailure:
      await bot_commands.send("Understood. !create_server command cancelled.")
      return  

   server = await create_server(ctx=ctx, num_rooms=num_rooms, num_rounds=num_rounds, schedule=schedule, num_teams=num_teams)


@bot.command(name = "clear_server")
async def clear_server(ctx):
   if not ctx.guild.owner == ctx.message.author:
      await ctx.reply("You do not have permission to invoke this command")
      return

   def react_check(reaction, user):
      if user == ctx.message.author and str(reaction.emoji) == '👍':
         return True 
      raise commands.CheckFailure("Non 👍 emoji recieved.")

   def author_check(author):
      def message_check(message):
         if author == message.author and message.content == "Confirm Delete":
            return True
         raise commands.CheckFailure("Wrong server name provided.")
      return message_check

   embed = discord.Embed(
      title = "This is a dangerous command. Are you sure you want to continue? React with the 👍 emoji to approve.",
      description  = "Reacting with the 👎 or waiting 60 seconds will cancel the command."
   )

   await ctx.send(embed=embed)

   # check for user reaction confirming that they'd like to continue, return from function if check fails 
   try:
      reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=react_check)
   except asyncio.TimeoutError:
      await ctx.send("Command timed out. Quiz_bot did not delete anything.")
      return
   except commands.CheckFailure:
      await ctx.send("Understood. Quiz_bot did not delete anything.")


   embed = discord.Embed(
      title = "This will completely wipe out your server. This is irreversible. Are you sure you want to do this?\
      Write ''Confirm Delete'' in the chat to confirm.",
      description  = "Typing anything else or waiting 60 seconds will cancel the command."
   )

   await ctx.send(embed=embed)

   # check for user message confirming deletion, return from function if check fails 
   try:
      message = await bot.wait_for("message", timeout=60.0, check=author_check(ctx.author))
   except asyncio.TimeoutError:
      await ctx.send("Command timed out. Quiz_bot did not delete anything.")
      return
   except commands.CheckFailure:
      await ctx.send("Understood. Quiz_bot did not delete anything.")
      return

   # once all the confirms are passed, loop through and deleted each role, channel, and category
   for guild in bot.guilds:
      for role in ctx.guild.roles:
         try:
            await role.delete()
         except:
            continue
   
   for channel in ctx.guild.channels:
        await channel.delete()

   for category in ctx.guild.categories:
      await category.delete()
   

@bot.command(name="leave_all_servers_except_current")
async def leave(ctx):
   if not (await bot.is_owner(ctx.message.author)):
      await ctx.send("You do not have permission to invoke this command")
      return

   msg = ""

   for guild in bot.guilds:
      if not guild == ctx.guild:
         msg += guild.name + "\n"

   embed = discord.Embed(
      title = "This will cause quiz_bot to leave: \n \n" + msg + "\nReact with the 👍 emoji to approve.",
      description  = "Reacting with the 👎 or waiting 30 seconds will cancel the command."
   )

   def check(reaction, user):
      if user == ctx.message.author and str(reaction.emoji) == '👍':
         return True 
      raise commands.CheckFailure("Non 👍 emoji recieved")

   await ctx.send(embed=embed)

   try:
      reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
   except asyncio.TimeoutError:
      await ctx.send("Command timed out. Quiz_bot did not leave any channels.")
      return
   except commands.CheckFailure:
      await ctx.send("Understood. Quiz_bot did not leave any channels.")
      return
   
   # double check that we're only deleting in case of affirmative response
   if str(reaction.emoji) == '👍':
      for guild in bot.guilds:
         if not guild == ctx.guild:
            await ctx.send(f"Leaving {guild.name}")
            await guild.leave()

bot.run(TOKEN)