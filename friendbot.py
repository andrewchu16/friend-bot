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
            consented_list = json.load(cf)
        print(consented_list)
        
    
    # Runs when the bot is fully connected to Discord
    async def on_ready(self) -> None:
        activity = discord.Game(
            name = "Making friends!",
            start = datetime.datetime.now()
        )
        await self.change_presence(
            status = discord.Status.online,
            activity = activity
        )
        print("Bot is online @ " + str(datetime.datetime.now()))

    # Runs when a new message is sent
    async def on_message(self, message) -> None:
        user = message.author
        text = message.content
        ctx = message.channel

        # Prevent bot from responding to itself and other bots
        if user.bot:
            return
        

        if text.startswith("!help"):
            embed = discord.Embed(title = "Helping out a friend!", type = "rich", description = "**!help** - A bit of help for when you're in need!\n\n**!consent** - Consent to use the bot. Some messages are stored and used in prompts to Cohere, which we wanted the users to know.\n\n**!conversation** - Start a conversation with the bot.\n\n**!end** - End a conversation with the bot.\n\n**!reset** - Resets the user's conversation cache.\n\n**!regenerate** - Regenerate the bot's last response with same cache. Maybe you're not happy with what the bot said, or you want a different storyline.\n", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.blue())
            embed.set_footer(text="Learning about commands", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed=embed)
            
        # Ignore banned users
        elif self.get_strikes(str(user.id)) > STRIKES_MAX: 
            if (text.startswith("!reset") or text.startswith("!consent") or text.startswith("!end") or text.startswith("!conversation")) and random.randint(1,CHANCE_OF_REACTION) == 1:
                await ctx.send(f"{user.mention}, I'm ignoring rude ppl smh 🙄")
            return
        
        
        if text.startswith("!consent"):
            # Ask for user's consent
            if not (self.is_consented(user.id)):
                embed = discord.Embed(title = "Consent to using Friend Bot", type = "rich", description = "I only make friends with people who consent to my terms and services! They're pretty simple though.\n\n**1.** You consent to having your messages saved and sent to Discord, Cohere, and me (the bot) \n\n**2.** Your behaviour follows the guidelines of both [Discord](https://discord.com/terms) and [Cohere](https://cohere.ai/terms-of-use).\n\n**3.** You will have fun with this bot!", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.gold())
                embed.set_thumbnail(url = self.user.avatar_url)
                embed.set_footer(text = "React with ✅ to consent!", icon_url = self.user.avatar_url)
                consentmessage = await ctx.send(user.mention, embed = embed)
                self.consentmessages[consentmessage.id] = user.id
                await consentmessage.add_reaction('✅')
            else:
                embed = discord.Embed(type = "rich", description = "You've already consented! Start a conversation using **`!conversation`**", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
                embed.set_footer(text = "Start chatting to me :)", icon_url = self.user.avatar_url)
                await ctx.send(user.mention, embed = embed)
        # Checks if the user has consented to the usage of the bot yet or if the user has been banned
        if (text.startswith("!conversation") or text.startswith("!reset") or text.startswith("!regenerate") or text.startswith("!end")) and not self.is_consented(user.id):
            embed = discord.Embed(title = "Not Consented", type = "rich", description = "Sorry, you need to consent in order to use this bot, please type **`!consent`** to read and consent to the rules!", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return

        if user in self.is_messaging:
            # Reset the conversation history
            if text.startswith("!reset"):
                self.history[user.id].reset()
                await ctx.send("Successfully reset your cache")
                return
            elif text.startswith("!regenerate"):
                new_msg = self.history[user.id].regenerate()
                if new_msg == -1:
                    await ctx.send("The bot hasn't said anything yet ...")
                else:
                    await message.delete()
                    async with ctx.typing():
                        self.model.create_prompt(user.id, self.history[user.id].export()) 

                        # appropriate means message is appropriate
                        response, appropriate = self.model.generate_response(user.id)

                    bot_message = await ctx.fetch_message(new_msg[1])
                    await bot_message.edit(content=user.mention + ", " + response)
                    self.history[user.id].add(response.strip(), True, bot_message.id)

                    if not appropriate:
                        self.add_strike(user.id) 
            
                    self.last_command = time.time()
                return
            elif text.startswith("!conversation"):
                await ctx.send("I'm already conversing with you, try saying something that isn't a command.")
                return
            elif text.startswith("!end"):
                self.is_messaging.remove(user)
                embed = discord.Embed(title = "Bye!", type = "rich", description = f"Ending conversation with {user.mention}", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.gold())
                embed.set_footer(text = "Hope to chat with you again! 👋", icon_url = self.user.avatar_url)
                await ctx.send(user.mention, embed = embed)
                return
        elif text.startswith("!conversation"):
            self.is_messaging.add(user)
            self.history[user.id] = history.History(user.name)
            embed = discord.Embed(title = "Hello!", type = "rich", description = f"Starting conversation with {user.mention} 😊", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.green())
            embed.set_footer(text = "Enjoy!", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return
        else:
            return


        if not (user in self.is_messaging):
            return


            
        # Ignore empty messages
        if len(text) <= 0:
            embed = discord.Embed(title = "Invalid Message", type = "rich", description = "Not responding to this message, I can only read text, your message has none 😡", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(text = "You probably sent an image or a video, we can't read those!", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
        # Ignore messages above MESSAGE_LEN_MAX length (too long for our budget)
        if len(text) > MESSAGE_LEN_MAX:
            embed = discord.Embed(title = "Invalid Message", type = "rich", description = "The message was too long, so we decided to ignore you (we don't have infinite $$$ you know ...)\nTry sending something shorter than a Twitter post", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(text = f"Please send a text below {MESSAGE_LEN_MAX} characters", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return
        elif time.time() - self.last_command < MESSAGE_WAIT:
            # later update it so that messages sent during the two second duration is compressed into one
            embed = discord.Embed(title = "Too fast!", type = "rich", description = f"Please wait {MESSAGE_WAIT} seconds between messages", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(text = "Slow down!", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
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
                    embed = discord.Embed(title = "Checkmark!", type = "rich", description = user.mention + ", you've consented to be my friend! 😀", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.green())
                    embed.set_footer(text = "Start your first conversation with !conversation", icon_url = self.user.avatar_url)
                    await reaction.message.channel.send(user.mention, embed = embed)

                    
    # Returns true or false depending on whether the function writes successfully
    def write_consented(self, user_id: int = -1) -> bool:
        if user_id != -1:
            with open(CONSENT_FILE, "r") as file:
                consented_list = json.load(file)
            if str(user_id) not in consented_list:
                consented_list[str(user_id)] = {
                    "strikes": 0,
                    "last_strike": None
                }
            try:
                with open(CONSENT_FILE, "w") as file:
                    json.dump(consented_list, file, indent=4)
                return True
            except Exception:
                return False
        return False
    
    def is_consented(self, user_id: int) -> bool:
        with open(CONSENT_FILE, "r") as cf:
            consented_list = json.load(cf)
            if str(user_id) in consented_list:
                return True
        return False

    def add_strike(self, user_id: int) -> None:
        with open(CONSENT_FILE, "r") as file:
            consented_list = json.load(file)
        # to be able to converse with the bot, one has to already be in consented_list
        consented_list[str(user_id)]["strikes"] += 1
        with open(CONSENT_FILE, "w") as file:
            json.dump(consented_list, file, indent=4)        
            
    # just returns the number of strikes that they have
    def get_strikes(self, user_id: int) -> int:
        with open(CONSENT_FILE, "r") as file:
            consented_list = json.load(file)
        if str(user_id) in consented_list:
            return int(consented_list[str(user_id)]["strikes"])
        else:
            return 0
