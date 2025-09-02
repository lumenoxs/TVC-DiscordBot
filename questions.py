from discord.ext import commands
import random
import requests
import os
import json
from dotenv import load_dotenv


load_dotenv("secrets.env")
questions_url = os.getenv("QUESTIONS")
trivia_questions_file = "trivia_questions.json"
trivia_questions = {}

def add_question(message_id, question, answer, letter):
    global trivia_questions
    trivia_questions[message_id] = {
        "question": question,
        "answer": answer,
        "letter": letter
    }
    with open(trivia_questions_file, "w") as f:
        json.dump(trivia_questions, f, indent=4)

def remove_question(message_id):
    global trivia_questions
    if message_id in trivia_questions:
        del trivia_questions[message_id]
    with open(trivia_questions_file, "w") as f:
        json.dump(trivia_questions, f, indent=4)
        
def load_questions():
    global trivia_questions
    try:
        with open(trivia_questions_file, "r") as f:
            trivia_questions = json.load(f)
    except FileNotFoundError:
        trivia_questions = {}


def updateTriviaQuestions():
    global trivia_questions
    trivia_questions = load_questions()
    

class QuestionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trivia(self, ctx, number: int = 1):
        try:
            response = requests.get(questions_url)
            response = json.loads(response.text)
            
            for i in range(number):
                question = random.choice(response)
                reply = await ctx.send(f"**Question:** {question['question']}\n**1**: {question['A']}\n**2**: {question['B']}\n**3**: {question['C']}\n**4**: {question['D']}\n*Directly reply (not just comment) with the correct letter (A, B, C, or D) or the full answer.*")
                add_question(reply.id, question['question'], question[question['answer']], question['answer'])
        except Exception as e:
            print(f"Error: {e}")
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        elif message.reference and message.reference.message_id in trivia_questions:
            if message.content.strip().upper() in ["A", "B", "C", "D"] and message.content.strip().upper() == trivia_questions[message.reference.message_id]["letter"]:
                await message.reply("Correct answer! 🎉")
                remove_question(message.reference.message_id)
            elif message.content.strip().upper() == trivia_questions[message.reference.message_id]["answer"]:
                await message.reply("Correct answer! 🎉")
                remove_question(message.reference.message_id)
            else:
                await message.reply(f"Wrong answer! The correct answer was: {trivia_questions[message.reference.message_id]['answer']} ({trivia_questions[message.reference.message_id]['letter']})")
                remove_question(message.reference.message_id)

async def setup(bot):
    await bot.add_cog(QuestionsCog(bot))