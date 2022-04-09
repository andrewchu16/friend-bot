import discord
import datetime
import time
import json
import random

import history
import languageModel


MESSAGE_LEN_MAX = 280
MESSAGE_WAIT = 2
STRIKES_MAX = 3
CONSENT_FILE = "consented.json"
CHANCE_OF_REACTION = 3

# Class for the Discord Bot
class FriendBot(discord.Client):
    # Initialization method
    def __init__(self, cohere_token) -> None:
        super().__init__(
            intents = discord.Intents.all(), 
            status = discord.Status.idle
        )
        
        #self.who = None
        self.model = languageModel.Model(cohere_token)
        self.history = dict()  # self.history[user.id] = History(user.name)
        self.last_command = 0
        self.is_messaging = set()
        self.consentmessages = dict()

        with open(CONSENT_FILE, "r") as cf:
            self.consented_list = json.load(cf)
        print(self.consented_list)
        
    
    # Runs when the bot is fully connected to Discord
    async def on_ready(self) -> None:
        activity = discord.Game(
            name = "Getting coded!",
            start = datetime.datetime.now()
        )
        await self.change_presence(
            status = discord.Status.online,
            activity = activity
        )
        print("Bot is online")

    # Runs when a new message is sent
    async def on_message(self, message) -> None:
        user = message.author
        text = message.content
        ctx = message.channel

        # Prevent bot from responding to itself and other bots
        if user.bot:
            return
        elif self.user_strikes(str(user.id)) > STRIKES_MAX: 
            # ignores anyone banned
            if (text.startswith("!reset") or text.startswith("!consent") or text.startswith("!end") or text.startswith("!conversation")) and random.randint(1,CHANCE_OF_REACTION) == 1:
                await ctx.send(f"{user.mention}, I'm ignoring rude ppl smh 🙄")
            return

        if text.startswith("!consent"):
            if not (self.is_consented(user.id)):
                embed = discord.Embed(title = "Consent to using Friend Bot", type = "rich", description = "I only make friends with people who consent to my terms and services! They're pretty simple though.\n\n**1.** You consent to having your messages saved and sent to Discord, Cohere, and me (the bot) \n\n**2.** Your behaviour follows the guidelines of both [Discord](https://discord.com/terms) and [Cohere](https://cohere.ai/terms-of-use).\n\n**3.** You will have fun with this bot!", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.gold())
                embed.set_thumbnail(url = self.user.avatar_url)
                embed.set_footer(text = "React with ✅ to consent!", icon_url = self.user.avatar_url)
                consentmessage = await ctx.send(user.mention, embed = embed)
                self.consentmessages[consentmessage.id] = user.id
                await consentmessage.add_reaction('✅')
            else:
                embed = discord.Embed(type = "rich", description = "You've already consented! Start a conversation using **`!conversation`**", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
                embed.set_footer(icon_url = self.user.avatar_url)
                await ctx.send(user.mention, embed = embed)
        # Checks if the user has consented to the usage of the bot yet or if the user has been banned
        if (text.startswith("!conversation") or text.startswith("!reset") or text.startswith("!regenerate") or text.startswith("!end")) and not self.is_consented(user.id):
            embed = discord.Embed(title = "Not Consented", type = "rich", description = "Sorry, you need to consent in order to use this bot, please type **`!consent`** to read and consent to the rules!", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return

        if user in self.is_messaging:
            # reset the convo
            if text.startswith("!reset"):
                self.history[user.id].reset()
                await ctx.send("Successfully reset your cache")
                return
            elif text.startswith("!regenerate"):
                self.history[user.id].regenerate()
                await ctx.send("Successfully regenerated")
                return
            elif text.startswith("!conversation"):
                await ctx.send("I'm already conversing with you, try saying something that isn't a command.")
                return
            elif text.startswith("!end"):
                self.is_messaging.pop(user)
                await ctx.send(f"Ending conversation with {user.name}")
                return
        elif text.startswith("!conversation"):
            self.is_messaging.add(user)
            self.history[user.id] = history.History(user.name)
            await ctx.send(f"Beginning conversation with {user.name}")
            return
        else:
            return


        if not (user in self.is_messaging):
            return


            
        # Ignore empty messages
        if len(text) <= 0:
            await ctx.send("Not responding to this message, I can only read text, your message has none 😡")
        # Ignore messages above MESSAGE_LEN_MAX length (too long for our budget)
        if len(text) > MESSAGE_LEN_MAX:
            await ctx.send(f"The message was too long, so we decided to ignore you (we don't have infinite $$$ you know ...). Please send a text below {MESSAGE_LEN_MAX} characters (tweet length)")
            return
        elif time.time() - self.last_command < MESSAGE_WAIT:
            # later update it so that messages sent during the two second duration is compressed into one
            await ctx.send(f"Please wait {MESSAGE_WAIT} seconds between messages")
            return
        

        async with ctx.typing():
            # Alerts the console that a message has been sent
            self.history[user.id].add(text)
            self.model.create_prompt(user.id, self.history[user.id].export()) 

            # appropriate means message is appropriate
            response, appropriate = self.model.generate_response(user.id)
            
        bot_message = await ctx.send(user.mention + ", " + response)
        self.history[user.id].add(response.strip(), True, bot_message.id)

        if not appropriate:
            # add a strike
            self.add_strike(user.id) 
            
        self.last_command = time.time()

    # When a reaction is added to a message
    async def on_reaction_add(self, reaction, user) -> None: 
        if reaction.message.id in self.consentmessages:
            if self.consentmessages[reaction.message.id] == user.id:
                print(reaction.emoji)
                if reaction.emoji == '✅':
                    print("reaction")
                    self.write_consented(user.id)
                    embed = discord.Embed(title = "Checkmark!", type = "rich", description = user.mention + ", you've consented to be my friend! 😀")
                    await reaction.message.channel.send(user.mention + " checkmark!")

                    
    # Returns true or false depending on whether the function writes successfully
    def write_consented(self, user_id: int = -1) -> bool:
        if user_id != -1:
            if str(user_id) not in self.consented_list.keys():
                self.consented_list[str(user_id)] = {
                    "strikes": 0,
                    "last_strike": None
                }
        try:
            with open(CONSENT_FILE, "w") as file:
                json.dump(self.consented_list, file, indent=4)
            return True
        except Exception:
            return False
        

    
    def is_consented(self, user_id: int) -> bool:
        with open(CONSENT_FILE, "r") as cf:
            consented_list = json.load(cf)
            if str(user_id) in consented_list:
                return True
        return False

    def add_strike(self, user_id: int) -> None:
        # to be able to converse with the bot, one has to already be in consented_list
        self.consented_list[str(user_id)]["strikes"] += 1
        #self.consented_list[str(user_id)]["last_strike"] = datetime.datetime.now()
        self.write_consented()
            
    # just returns the number of strikes that they have
    def user_strikes(self, user_id: int) -> int:
        if str(user_id) in self.consented_list.keys():
            return int(self.consented_list[str(user_id)]["strikes"])
        else:
            return 0
