import asyncio
import random
import re
import unidecode
import os
import numpy as np
import operator
import discord

class Question:

    def __init__(self, question, propositions, proposition_emojis, correct_idx, score):
        self.question = question
        self.propositions = propositions
        self.proposition_emojis = proposition_emojis
        assert len(self.propositions) == len(self.proposition_emojis)
        self.correct_idx = correct_idx
        self.score = score        
        
    @property
    def ask(self):
        question_text = "["+str(self.score)+" points]\n"
        question_text += self.question + '\n'
        for i in range(len(self.propositions)):
            question_text += self.proposition_emojis[i] + ' ' + self.propositions[i] + '\n'
        return question_text

class Carré(Question):
    def __init__(self, question, propositions, correct_idx, score):
        super().__init__(question, propositions, ['1️⃣', '2️⃣','3️⃣','4️⃣'], correct_idx, score)

class VraiFaux(Question):
    def __init__(self, question, answer, score):
        super().__init__(question, ['Vrai', 'Faux'], ['👍', '👎'], int(not answer), score)

class Cash(Question):
    def __init__(self, question, answer, score):
        super().__init__(question, [], [], None, score)
        self.answer = answer

class Quiz:
    
    def __init__(self, bot):

        self.questions = []
        self.current_question_idx = 0
        self.scores = {}
        self.messages = set()   
        self.bot = bot   
        self.players_answers = {}

    @property
    def current_question(self):
        return self.questions[self.current_question_idx]
    
    def load_questions(self, question_file):

        with open(question_file, encoding='utf-8',errors='replace') as qfile:
            lines = qfile.readlines()

        def reset_variables():
            return None, None, [], 10
        question, answer, propositions, score = reset_variables()
        
        for line in lines:
            if not line.strip().startswith('#'):
                if line.strip() == '': # ligne vide, alors on ajoute la question s'elle est complète, sinon on l'abandonne

                    if question is not None:
                        if type(answer)==int:
                            # Carré
                            q = Carré(question, propositions, answer, score)
                        elif type(answer)==bool:
                            # VraiFaux
                            q = VraiFaux(question, answer, score)
                        else:
                            # Cash
                            q = Cash(question, answer, score)
                        self.questions.append(q)
                        
                    question, answer, propositions, score = reset_variables()
                    
                if line.strip().lower().startswith('question'):
                    question = line.strip()[line.find(':') + 1:].strip()
                elif line.strip().lower().startswith('answer'):
                    answer = line.strip()[line.find(':') + 1:].strip()
                    if answer in ['0','1']:
                        answer = bool(int(answer))
                elif line.strip().lower().startswith('score'):
                    score = int(line.strip()[line.find(':') + 1:].strip())
                elif line.strip().lower().startswith('-'): # proposition
                    if line.strip().lower().startswith('->'): # correct
                        propositions.append(line.strip()[line.find(':') + 1:].strip()[2:])
                        answer = len(propositions)-1
                    else:
                        propositions.append(line.strip()[line.find(':') + 1:].strip()[1:])
    
    def start_round(self, round_name):
        for team in self.scores.keys():
            self.scores[team] = 0
        self.load_questions('./qualifs/'+round_name)
        self.current_question_idx = -1
        self.question_pending = False

    async def clear_messages(self):
        for message in self.messages:
            cache_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
            await cache_msg.delete()
        self.messages = set()

    async def skip_question(self, ctx):
        self.question_pending = False
        self.ask_next(ctx)

    async def ask_next(self, ctx):
        if not self.question_pending and self.current_question_idx < len(self.questions)-1:
            self.question_pending = True
            await self.clear_messages()
            self.current_question_idx += 1
            self.players_answers = {}
            current_question = self.questions[self.current_question_idx]
            message = '**Question '+str(self.current_question_idx+1)+'/'+str(len(self.questions))+'** '+current_question.ask
            current_question.message = await ctx.send(message)
            self.messages.add(current_question.message)
            for reaction in current_question.proposition_emojis:
                await current_question.message.add_reaction(reaction)

    async def conclude_question(self, ctx):

        self.scores_deltas = {team_role: 0 for team_role in self.scores.keys()}
        current_question = self.current_question

        for player in self.players_answers.keys():
            for team_role in self.scores_deltas.keys():
                if team_role in player.roles:
                    print(self.players_answers[player], current_question.proposition_emojis[current_question.correct_idx])
                    if self.players_answers[player] == current_question.proposition_emojis[current_question.correct_idx]: 
                        self.scores_deltas[team_role] += current_question.score
                        self.scores[team_role] += current_question.score

        if not isinstance(current_question, Cash):
            message = "La réponse était **"+current_question.proposition_emojis[current_question.correct_idx] + current_question.propositions[current_question.correct_idx] + '**'
        else:
            message = "La réponse était **"+ current_question.answer + '**'
        self.messages.add(await ctx.send(message))
        await self.show_scores(ctx, show_deltas=True)
        self.question_pending = False

            
    async def show_scores(self, ctx, show_deltas=False):
        message = "**Scores**\n"
        sorted_scores = sorted(self.scores.items(), key=operator.itemgetter(1), reverse=True)
        for team_score in sorted_scores:
            message += team_score[0].mention + ' : ' + str(team_score[1])
            if show_deltas:
                message += ' **(+' + str(self.scores_deltas[team_score[0]]) + ')**'
            message += '\n'
        self.messages.add(await ctx.send(message))
            
        
    

    
    
    
    
    
    
    
    
