from discord.ext import commands
import random
import requests
import os
import json
from dotenv import load_dotenv


load_dotenv("secrets.env")
questions_url = os.getenv("QUESTIONS")
trivia_questions_file = "trivia_questions.json"
        
def load_questions():
    try:
        with open(trivia_questions_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def add_question(message_id, question, answer, letter):
    trivia_questions = load_questions()
    trivia_questions[str(message_id)] = {
        "question": question,
        "answer": answer,
        "letter": letter
    }
    with open(trivia_questions_file, "w") as f:
        json.dump(trivia_questions, f, indent=4)

def remove_question(message_id):
    message_id = str(message_id)
    trivia_questions = load_questions()
    if message_id in trivia_questions:
        del trivia_questions[message_id]
    with open(trivia_questions_file, "w") as f:
        json.dump(trivia_questions, f, indent=4)

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
        trivia_questions = load_questions()
        if message.reference and str(message.reference.message_id) in trivia_questions.keys() and message.author.id != self.bot.user.id:
            if message.content.strip().upper() in ["A", "B", "C", "D"] and message.content.strip().upper() == trivia_questions[str(message.reference.message_id)]["letter"]:
                await message.reply("Correct answer! 🎉")
                remove_question(message.reference.message_id)
            elif message.content.strip().upper() in ["1", "2", "3", "4"] and message.content.strip().upper() == trivia_questions[str(message.reference.message_id)]["letter"].replace("A", "1").replace("B", "2").replace("C", "3").replace("D", "4"):
                await message.reply("Correct answer! 🎉")
                remove_question(message.reference.message_id)
            elif message.content.strip().upper() == trivia_questions[str(message.reference.message_id)]["answer"].upper():
                await message.reply("Correct answer! 🎉")
                remove_question(message.reference.message_id)
            else:
                await message.reply(f"Wrong answer! The correct answer was: {trivia_questions[str(message.reference.message_id)]['answer']} ({trivia_questions[str(message.reference.message_id)]['letter']})")
                remove_question(message.reference.message_id)

async def setup(bot):
    await bot.add_cog(QuestionsCog(bot))