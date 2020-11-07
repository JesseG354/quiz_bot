import os
from dotenv import load_dotenv

import discord

from discord.ext import commands
from discord.utils import get

import random
import re


load_dotenv()

TOKEN = os.getenv('TOKEN') 

bot = commands.Bot(command_prefix="!")

@bot.command(name = "clear_server")
async def clear_server(ctx):

   def check(m):
      if m.content == 'No' or m.content == 'no':
         raise ValueError("Cancelling")
      return m.content == 'Yes' or m.content == 'yes' 


   sure_prompt = discord.Embed(
      title = "This will completely wipe out your server. This is irreversible. Are you sure you want to do this?",
      description = "Options are: Yes or No"
   )
   await ctx.send(embed=sure_prompt)

   try: 
      await bot.wait_for(
         "message",
         check = check
      )
   except ValueError:
      await ctx.send(
         f'Gotcha. Cancelling server wipe'
      )
      return

   for role in ctx.guild.roles:
      try:
         await role.delete()
         await ctx.send(
            f'Deleted {role}'
         )
      except:
         await ctx.send(
            f'Couldn\'t delete role {role}'
         )

   for channel in ctx.guild.channels:
        await channel.delete()

   for category in ctx.guild.categories:
      await category.delete()

   await ctx.guild.create_text_channel('general')


@bot.command(name="create_roles")
async def create_roles(ctx, num_teams: int):
   guild = ctx.guild
   bot_logs = discord.utils.get(guild.text_channels, name="bot_actions")

   
   for i in range(1, num_teams+1):
      guild = ctx.guild
      team_name = f'Team {i}'

      await guild.create_role(name = team_name, color = discord.Colour(random.randint(0, 0xffffff)))

      await bot_logs.send(
         f'Created Team {i}', 
      )

   for i in range (1, int((num_teams/2))+1):
         staff_name = f'Room {i} Staff'
         await guild.create_role(name = staff_name, color = discord.Colour(0xFFD700))
         await bot_logs.send(
            f'Created Room {i} Staff ',
         )

async def server_init(ctx, rooms, rounds, teams, sch):
   await create_roles(ctx, teams)
   await create_standard_rooms(ctx, teams)
   await create_tournament_rooms(ctx, rounds, rooms)
   await set_permissions(ctx, rooms, rounds, sch)

async def create_standard_rooms(ctx, num_teams):
   guild = ctx.guild
   bot_logs = discord.utils.get(guild.text_channels, name="bot_actions")


   text_permissions = {
         guild.default_role: discord.PermissionOverwrite(read_messages = False),
         guild.me: discord.PermissionOverwrite(read_messages = True)
   }
   voice_permissions = {
         guild.default_role: discord.PermissionOverwrite(view_channel = False),
         guild.me: discord.PermissionOverwrite(view_channel = True)
   }

   # create staff rooms
   await guild.create_category("staff-only")
   category = discord.utils.get(ctx.guild.categories, name="staff-only")
   await guild.create_text_channel("staff-chat", category=category, overwrites=text_permissions)
   await guild.create_voice_channel("staff-voice", category=category, overwrites=voice_permissions)

   text_channel = discord.utils.get(guild.text_channels, name = f'staff-chat')
   voice_channel = discord.utils.get(guild.voice_channels, name = f'staff-voice')

   for i in range (1, int((num_teams/2))+1):
      await text_channel.set_permissions(get(guild.roles, name = f'Room {i} Staff'), read_messages = True, send_messages = True)
      await voice_channel.set_permissions(get(guild.roles, name = f'Room {i} Staff'), view_channel = True, connect = True, speak = True)



   # create general rooms
   await guild.create_category("general-info")
   category = discord.utils.get(ctx.guild.categories, name="general-info")
   await guild.create_text_channel("annoucements", category=category, overwrites=text_permissions)
   await guild.create_text_channel("stats", category=category, overwrites=text_permissions)
   await guild.create_voice_channel("opening_meeting", category=category)



async def create_tournament_rooms(ctx, num_rounds: int, num_rooms: int):
   guild = ctx.guild
   bot_logs = discord.utils.get(guild.text_channels, name="bot_actions")


   text_permissions = {
         guild.default_role: discord.PermissionOverwrite(read_messages = False),
         guild.me: discord.PermissionOverwrite(read_messages = True)
   }
   voice_permissions = {
         guild.default_role: discord.PermissionOverwrite(view_channel = False),
         guild.me: discord.PermissionOverwrite(view_channel = True)
   }

   for i in range(1, num_rounds+1):
      category_name = f'round{i}'
      await guild.create_category(category_name)
   
      for j in range(1, num_rooms+1):
         category = discord.utils.get(ctx.guild.categories, name=category_name)
         channelname = f'round{i}_room{j}'
         await guild.create_text_channel(channelname, category=category, overwrites=text_permissions)   
         await guild.create_voice_channel(channelname, category=category, overwrites=voice_permissions)

         await bot_logs.send(
            f'Created {channelname}', 
         )

async def set_permissions(ctx, num_rooms:int, num_rounds:int, schedule):
   guild = ctx.guild
   bot_logs = discord.utils.get(guild.text_channels, name="bot_actions")

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
         
         await bot_logs.send (
            f'Set teams {int(schedule[match])} and {int(schedule[match+1])} to round{i}_room{j}',
            delete_after = 60.0
         ) 
         match += 2
   
   for i in range (1, num_rounds+1):
      for j in range (1, num_rooms+1):
         staff = get(guild.roles, name = f'Room {j} Staff')

         text_channel = discord.utils.get(guild.text_channels, name = f'round{i}_room{j}')
         voice_channel = discord.utils.get(guild.voice_channels, name = f'round{i}_room{j}')

         await text_channel.set_permissions(staff, read_messages = True, send_messages = True)
         await voice_channel.set_permissions(staff, view_channel = True, connect = True, speak = True)

         await bot_logs.send (
            f'Set Room {j} Staff to round{i}_room{j}',
            delete_after = 60.0
         )
   
@bot.command(name="create_server")
async def create_server(ctx):
   guild = ctx.guild

   def team_check(message):
      if not message.content.isdigit():
         print(
            "Please enter an integer"
         )
         return False
      if int(message.content) <= 0 or int(message.content) > 48:
         print(
            "Please enter a number between 0 and 48, inclusive"
         )
         return False
      return True
   
   def room_check(message):
      if not message.content.isdigit():
         print(
            "Please enter an integer"
         )
         return False
      if int(message.content) <= 0 or int(message.content) > 16:
         print(
            "Please enter a number between 0 and 16, inclusive"
         )
         return False
      return True

   def schedule_check(message):
      sched_str = message.content

      # clean up input
      sched_str = sched_str.replace("(", " ")
      sched_str = sched_str.replace(")", " ")
      sched_str = sched_str.replace(",", " ")
      sched_str = re.sub("\s+", ' ', sched_str)
      sched_str = sched_str.strip()
      schedule = sched_str.split(" ")
      
      if len(schedule) != (num_teams * num_rounds):
         print(
            f'Please double check your schedule. Your input has {len(schedule)} entries, when it \
            should have {num_teams * num_rounds}. Please note, you\'ve indicated {num_teams} teams \
            and {num_rounds} rounds, so your schedule should have {num_teams*num_rounds} entries.'
         )
         return False
      if not all(i.isdigit() for i in schedule):
         print(
            f'It appears you\'ve placed something that\'s not an integer in your schedule. Please double check your input.'
         )
         return False
      return True

   num_teams: int
   num_rounds: int 
   num_rooms: int

   text_permissions = {
         guild.default_role: discord.PermissionOverwrite(read_messages = False),
         guild.me: discord.PermissionOverwrite(read_messages = True)
   }
   voice_permissions = {
         guild.default_role: discord.PermissionOverwrite(view_channel = False),
         guild.me: discord.PermissionOverwrite(view_channel = True)
   }

   if discord.utils.get(guild.categories, name="bot") == None:
      await guild.create_category("bot")
      category = discord.utils.get(ctx.guild.categories, name="bot")
      await guild.create_text_channel("bot_commands", category=category, overwrites=text_permissions)
      await guild.create_text_channel("bot_actions", category=category, overwrites=text_permissions)

   bot_comm = discord.Embed(
      title = "Great! We're about to begin, please have the number of teams, number of rounds, and schedule of your tournament at hand.",
      description  = "After the creation of the server, all non !create_server commands will go \
      in the newly created #bot_commands channel. All bot actions are logged in, well, #bot actions."
   )
   await ctx.send(embed=bot_comm)

   team_prompt = discord.Embed(
      title = "How many teams are playing?",
      description = "Please enter an integer no greater than 48."
   )
   await ctx.send(embed=team_prompt)

   num_teams_msg = await bot.wait_for(
      "message",
      check = team_check
   )
   num_teams = int(num_teams_msg.content)

   room_prompt = discord.Embed(
      title = "How many non-playoff rounds will there be?",
      description = "Please enter an even integer no greater than 16."
   )
   await ctx.send(embed=room_prompt)

   num_rounds_msg = await bot.wait_for(
      "message",
      check = room_check
   )
   num_rounds = int(num_rounds_msg.content)
   num_rooms = int(num_teams/2)


   schedule_prompt = discord.Embed(
      title = "Please enter your tournament schedule.",
      description = "Enter only the team numbers in the order they will be playing. For example, \
         if the schedule is a round where team 1 plays 2 and 3 plays 4, followed by a round where \
         team 1 plays 3 and 2 plays 4, your input should be: \n \n \
         1 2 3 4 1 3 2 4"
   )
   await ctx.send(embed=schedule_prompt)

   schedule_msg = await bot.wait_for(
      "message",
      check = schedule_check
   )

   sched_str = schedule_msg.content

   # clean up input
   sched_str = sched_str.replace("(", " ")
   sched_str = sched_str.replace(")", " ")
   sched_str = sched_str.replace(",", " ")
   sched_str = re.sub("\s+", ' ', sched_str)
   sched_str = sched_str.strip()
   schedule = sched_str.split(" ")

   confirm = discord.Embed(
      title = "I've generated the following tournament. Please type Yes, if it is correct. Otherwise type No use \
      !create_server to try again",
      description =
      f'Number of teams = {num_teams}\n \
      Number of rounds = {num_rounds}\n \n \
      Schedule:'
   )
   await ctx.send(embed=confirm)


   num = 1

   for j in range(0, len(schedule), 2):
      if j % num_teams == 0:
         await ctx.send (
            f'Round {num}'
         )
         num += 1
      await ctx.send (
         f'Team {schedule[j]} v Team {schedule[j+1]}' 
      )

   def check(m):
      if m.content == "Yes" or m.content == "yes":
         return True
      if m.content == "No" or m.content == "no":
         raise ValueError
      return False

   try:
      await bot.wait_for(
         "message",
         check = check
      )
   except ValueError:
      return

   await server_init(ctx, rooms=num_rooms, rounds=num_rounds, teams=num_teams, sch=schedule)

bot.run(TOKEN)
   

   
