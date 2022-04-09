import discord
import datetime
import time
import json

import history
import languageModel



MESSAGE_LEN_MAX = 280
MESSAGE_WAIT = 2
CONSENT_FILE = "consented.txt"

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
        self.is_messaging = dict()
        self.consentmessages = dict()
        
        
    
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

        if text.startswith("!consent"):
            if not (self.is_consented(user.id)):
                consentmessage = await ctx.send(user.mention + " react to consent")
                self.consentmessages[consentmessage.id] = user.id
                await consentmessage.add_reaction('✅')
            else:
                await ctx.send("You've already consented! Start a conversation using `!conversation`")

        # Checks if the user has consented to the usage of the bot yet
        if (text.startswith("!conversation") or text.startswith("!reset") or text.startswith("!regenerate") or text.startswith("!end")) and not self.is_consented(user.id):
            await ctx.send("Sorry, you need to consent in order to use this bot, please type `!consent` to read and consent to the rules!")
            return

        if user in self.is_messaging:
            # reset the convo
            if text.startswith("!reset"):
                self.history[user.id].reset(user.id)
                await ctx.send("Successfully reset")
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
            self.is_messaging[user] = True
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
            response = self.model.generate_response(user.id)
        bot_message = await ctx.send(user.mention + ", " + response)
        self.history[user.id].add(response.strip(), True, bot_message.id)
        self.last_command = time.time()

    # When a reaction is added to a message
    async def on_reaction_add(self, reaction, user) -> None: 
        if reaction.message.id in self.consentmessages:
            if self.consentmessages[reaction.message.id] == user.id:
                print(reaction.emoji)
                if reaction.emoji == '✅':
                    print("reaction")
                    self.write_consented(user.id)
                    await reaction.message.channel.send(user.mention + " checkmark!")

    # Returns true or false depending on whether the function writes successfully
    def write_consented(self, user_id: int) -> bool:
        with open(CONSENT_FILE, "r") as cf:
            if str(user_id) not in cf.read():
                file = open(CONSENT_FILE, "a")
                file.write("\n"+ str(user_id))
                file.close()
                return True
            else:
                return False
            
    def is_consented(self, user_id: int) -> bool:
        with open(CONSENT_FILE, "r") as cf:
            if str(user_id) in cf.read():
                return True
            else:
                return False

    