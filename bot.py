import discord
from discord.ext import commands
import sys
import re
from typing import Union, List

import quiz

bot = commands.Bot(command_prefix = '!', description = '')
VERBOSE = False

def has_role(ctx, role_name, user:discord.Member=None):
    if user is None:
        user = ctx.message.author
    for role in user.roles:
        if role.name == role_name:
            return True
    return False

def create_quiz(channel):
    bot.quizzes[channel] = quiz.Quiz(bot)

@bot.command()
async def reset(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        create_quiz(ctx.message.channel)

@bot.command()
async def delete_roles(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        for role in ctx.guild.roles:
            if role.name not in ['Présentation', '@everyone','Bot Cogni\'Quiz']:
                await role.delete()
        # bot.delete_role()

@bot.command()
async def start(ctx, round_name):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        if ctx.message.channel not in bot.quizzes.keys():
            create_quiz(ctx.message.channel)
        bot.quizzes[ctx.message.channel].start_round(round_name)

@bot.command()
async def team(ctx, *args):#*team_name:str, *players:discord.Member):
    if not VERBOSE:
        await ctx.message.delete()
        
    if has_role(ctx, "Présentation"):
        team_name = []
        players = []
        for arg in args:
            if arg[:3] == '<@!':
                players.append(await ctx.guild.fetch_member(arg[3:-1]))
            else:
                team_name.append(arg)
        perms = discord.Permissions(add_reactions=True)
        team_role = await ctx.guild.create_role(name=' '.join(team_name), permissions=perms)
        for player in players:
            await player.add_roles(team_role)
        if ctx.message.channel not in bot.quizzes.keys():
            create_quiz(ctx.message.channel)
        bot.quizzes[ctx.message.channel].scores[team_role] = 0
        print(bot.quizzes[ctx.message.channel].scores)

@bot.command()
async def scores(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        await bot.quizzes[ctx.message.channel].show_scores(ctx)

@bot.event
async def on_reaction_add(reaction, user):
    print(reaction.message.id == bot.quizzes[reaction.message.channel].current_question.message.id)
    if reaction.message.id == bot.quizzes[reaction.message.channel].current_question.message.id:
        bot.quizzes[reaction.message.channel].players_answers[user] = reaction.emoji

@bot.command()
async def edit_score(ctx, team_role:discord.Role, new_score):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        old_score = bot.quizzes[ctx.message.channel].scores[team_role]
        if new_score[0]=='+':
            new_score = old_score + int(new_score[1:])
        elif new_score[0]=='-':
            new_score = old_score - int(new_score[1:])
        else:
            new_score = int(new_score)
        print(old_score, new_score)
        bot.quizzes[ctx.message.channel].scores[team_role] = int(new_score)



@bot.command()
async def conclude(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        await bot.quizzes[ctx.message.channel].conclude_question(ctx)

@bot.command()
async def clear(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        await bot.quizzes[ctx.message.channel].clear_messages()

@bot.command()
async def next(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        await bot.quizzes[ctx.message.channel].ask_next(ctx)

@bot.command()
async def skip(ctx):
    if not VERBOSE:
        await ctx.message.delete()
    if has_role(ctx, "Présentation"):
        await bot.quizzes[ctx.message.channel].skip_question(ctx)




#run the program!
if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print('Usage: python bot.py APP_BOT_USER_TOKEN')
        exit()
        
    # logs into channel    
    try:
        bot.quizzes = dict({})
        bot.run(sys.argv[1])
        

    except:        
        bot.close()