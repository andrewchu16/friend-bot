import discord
import datetime
import time
import json
import random

import history
import languageModel

# The largest amount of characters a user can send when having a conversation with the bot
MESSAGE_LEN_MAX = 280
# The delay between user messages during a conversation with the bot
MESSAGE_WAIT = 2
# How many strikes you can receive for violating the bot rules until you are banned
STRIKES_MAX = 3
# File that keeps track of users who have consented to using the voice
CONSENT_FILE = "consented.json"
# When trying to start a conversation as a banned user, there is a 1 in x chance of the bot telling you that you're banned
CHANCE_OF_REACTION = 3

# Class for the Discord Bot, interacts with Cohere and the console
class FriendBot(discord.Client):
    # Initialization method
    def __init__(self, cohere_token: str) -> None:
        super().__init__(
            intents = discord.Intents.all(), 
            # Set status to idle
            status = discord.Status.idle
        )
        # The language model used to communicate with Cohere
        self.model = languageModel.Model(cohere_token)
        # Stores user conversation history
        self.history = dict() 
        # The last time a message was sent in a conversation, used to keep track of message cooldowns
        self.last_command = 0
        # List of users the bot is currently having a conversation with
        self.is_messaging = set()
        # List of active consent messages
        self.consentmessages = dict()
        # Open and print out the list of consented users and their strikes 
        with open(CONSENT_FILE, "r") as cf:
            consented_list = json.load(cf)
        print(consented_list)
    
    # Runs when the bot is finished connecting to Discord
    async def on_ready(self) -> None:
        # Set a friendly status :)
        activity = discord.Game(
            name = "Making friends!",
            start = datetime.datetime.now()
        )
        # Switch to online mode
        await self.change_presence(
            status = discord.Status.online,
            activity = activity
        )
        # Let the console know that the bot has connected
        print(f"{self.user.name} is online @ {str(datetime.datetime.now())}")

    # Runs when a new message is sent
    async def on_message(self, message: discord.Message) -> None:
        # References the user who sent the message
        user = message.author
        # The text contents of the message
        text = message.content
        # References the channel the message was sent in
        ctx = message.channel

        # Prevent bot from responding to itself and other bots
        if user.bot:
            return

        # Help message
        if text.startswith("!help"):
            embed = discord.Embed(title = "Helping out a friend!", type = "rich", description = "**`!help`** - A bit of help for when you're in need!\n\n**!consent** - Consent to use the bot. Some messages are stored and used in prompts to Cohere, which we wanted the users to know.\n\n**!conversation** - Start a conversation with the bot.\n\n**!end** - End a conversation with the bot.\n\n**!reset** - Resets the user's conversation cache.\n\n**!regenerate** - Regenerate the bot's last response with same cache. Maybe you're not happy with what the bot said, or you want a different storyline.", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.blue())
            embed.set_footer(text="Learning about commands", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return
            
        # Ignore banned users
        elif self.get_strikes(str(user.id)) > STRIKES_MAX:
            # Check if a banned user is trying to send a command
            if (text.startswith("!reset") or text.startswith("!consent") or text.startswith("!end") or text.startswith("!conversation")) and random.randint(1, CHANCE_OF_REACTION) == 1:
                embed = discord.Embed(title = "Ignored 🙄", type = "rich", description = f"You've violated our rules {STRIKES_MAX} times, so I've decided to ignore you from now on.", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
                embed.set_footer(text = "shoo youre banned", icon_url = self.user.avatar_url)
                await ctx.send(user.mention, embed = embed)
            return
        
        # Consent message to use the bot
        if text.startswith("!consent"):
            # Make sure the user isn't already consented
            if not (self.is_consented(user.id)):
                embed = discord.Embed(title = "Consent to using Friend Bot", type = "rich", description = "I only make friends with people who consent to my terms and services! They're pretty simple though.\n\n**1.** You consent to having your messages saved and sent to Discord, Cohere, and me (the bot) \n\n**2.** Your behaviour follows the guidelines of both [Discord](https://discord.com/terms) and [Cohere](https://cohere.ai/terms-of-use).\n\n**3.** You will have fun with this bot!", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.gold())
                embed.set_thumbnail(url = self.user.avatar_url)
                embed.set_footer(text = "React with ✅ to consent!", icon_url = self.user.avatar_url)
                consentmessage = await ctx.send(user.mention, embed = embed)
                # Add the message to the dict of active consent messages
                self.consentmessages[consentmessage.id] = user.id
                # React to the message to allow the user to consent
                await consentmessage.add_reaction('✅')
            # If the user has already consented to the bot
            else:
                embed = discord.Embed(type = "rich", description = "You've already consented! Start a conversation using **`!conversation`**", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
                embed.set_footer(text = "Start chatting to me :)", icon_url = self.user.avatar_url)
                await ctx.send(user.mention, embed = embed)

        # If the user tries to run a conversation command but isn't consented to the bot
        if (text.startswith("!conversation") or text.startswith("!reset") or text.startswith("!regenerate") or text.startswith("!end")) and not self.is_consented(user.id):
            embed = discord.Embed(title = "Not Consented", type = "rich", description = "Sorry, you need to consent in order to use this bot, please type **`!consent`** to read and consent to the rules!", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return

        # Make sure the user is having a conversation with the bot
        if user in self.is_messaging:
            # Reset the conversation history
            if text.startswith("!reset"):
                self.history[user.id].reset()
                await ctx.send("Successfully reset your cache")
                return
            # Regenerate the most recent bot response
            elif text.startswith("!regenerate"):
                new_msg = self.history[user.id].regenerate()
                # Check if you are trying to regenerate before the conversation has started
                if new_msg == -1:
                    embed = discord.Embed(title = "What?", type = "rich", description = "I haven't said anything yet, what would I regenerate?", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
                    embed.set_footer(text = "Say something to me, then I'll respond", icon_url = self.user.avatar_url)
                    await ctx.send(user.mention, embed = embed)
                    return
                else:
                    # Delete the command message
                    await message.delete()
                    # The bot types while it tries to generate a new response
                    async with ctx.typing():
                        self.model.create_prompt(user.id, self.history[user.id].export()) 
                        # Generate the response and whether the message was appropriate
                        response, appropriate = self.model.generate_response(user.id)
                    # Fetch the message to be regenerated
                    bot_message = await ctx.fetch_message(new_msg[1])
                    # Edit the message
                    await bot_message.edit(content=user.mention + ", " + response)
                    # Edit the message history with the newly generated response
                    self.history[user.id].add(response.strip(), True, bot_message.id)
                    # If Cohere flags the message as inappropriate, add a strike to the user
                    if not appropriate:
                        self.add_strike(user.id) 
                    # Reset the conversation cooldown
                    self.last_command = time.time()
                return
            # When the user tries to start a conversation but is already talking to the bot
            elif text.startswith("!conversation"):
                await ctx.send("I'm already conversing with you, try saying something that isn't a command.")
                return
            # The user wants to end the conversation
            elif text.startswith("!end"):
                # Remove the user from the list of conversating users
                self.is_messaging.remove(user)
                embed = discord.Embed(title = "Bye!", type = "rich", description = f"Ending conversation with {user.mention}", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.gold())
                embed.set_footer(text = "Hope to chat with you again! 👋", icon_url = self.user.avatar_url)
                await ctx.send(user.mention, embed = embed)
                return
        # The user starts a conversation with the bot
        elif text.startswith("!conversation"):
            # Add the user to the list of conversating users 
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
        # Ignore messages above MESSAGE_LEN_MAX length
        if len(text) > MESSAGE_LEN_MAX:
            embed = discord.Embed(title = "Invalid Message", type = "rich", description = "The message was too long, so we decided to ignore you (we don't have infinite $$$ you know ...)\nTry sending something shorter than a Twitter post", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(text = f"Please send a text below {MESSAGE_LEN_MAX} characters", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return
        # If the user is sending messages too fast
        elif time.time() - self.last_command < MESSAGE_WAIT:
            # TODO: update it so that messages sent during the two second duration are compressed into one
            embed = discord.Embed(title = "Too fast!", type = "rich", description = f"Please wait {MESSAGE_WAIT} seconds between messages", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.red())
            embed.set_footer(text = "Slow down!", icon_url = self.user.avatar_url)
            await ctx.send(user.mention, embed = embed)
            return
        # Type while Cohere generates a response
        async with ctx.typing():
            # Alerts the console that a message has been sent
            self.history[user.id].add(text)
            self.model.create_prompt(user.id, self.history[user.id].export()) 
            # Generate the response and determine whether the message is appropriate
            response, appropriate = self.model.generate_response(user.id)
        # Send the message 
        bot_message = await ctx.send(user.mention + ", " + response)
        # Add the message to conversation history
        self.history[user.id].add(response.strip(), True, bot_message.id)
        # If the message was flagged by Cohere as inappropriate
        if not appropriate:
            # Add a strike to the user's record
            self.add_strike(user.id) 
        # Update the conversation cooldown
        self.last_command = time.time()
        
    # When a reaction is added to a message
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None: 
        # Check if the message is a consent message
        if reaction.message.id in self.consentmessages:
            # Make sure that the user who is reacting is the target of the consent message
            if self.consentmessages[reaction.message.id] == user.id:
                # Check if the reaction is a checkmark
                if reaction.emoji == '✅':
                    # Tell the console a new user has consented
                    print(f"{user.name} has just consented to the bot rules!")
                    # Add the new user to the consented list
                    self.write_consented(user.id)
                    embed = discord.Embed(title = "Checkmark!", type = "rich", description = user.mention + ", you've consented to be my friend! 😀", url = "https://github.com/Previouslynamedjeff/friend-bot", timestamp = datetime.datetime.now(), colour = discord.Colour.green())
                    embed.set_footer(text = "Start your first conversation with !conversation", icon_url = self.user.avatar_url)
                    await reaction.message.channel.send(user.mention, embed = embed)

                    
    # Returns true or false depending on whether the function writes successfully
    def write_consented(self, user_id: int = -1) -> bool:
        # Invalid user id
        if user_id != -1:
            with open(CONSENT_FILE, "r") as file:
                consented_list = json.load(file)
            if str(user_id) not in consented_list:
                # Add the user to the consented list
                consented_list[str(user_id)] = {
                    "strikes": 0,
                    "last_strike": None
                }
            try:
                # Write the dictionary to the consented users file
                with open(CONSENT_FILE, "w") as file:
                    json.dump(consented_list, file, indent=4)
                return True
            except Exception:
                return False
        return False

    # Check whether a user is consented to the bot's rules
    def is_consented(self, user_id: int) -> bool:
        with open(CONSENT_FILE, "r") as cf:
            consented_list = json.load(cf)
            if str(user_id) in consented_list:
                return True
        return False

    # Add a strike to a user after they've broken the rules
    def add_strike(self, user_id: int) -> None:
        with open(CONSENT_FILE, "r") as file:
            consented_list = json.load(file)
        # To be able to converse with the bot, one has to already be in consented_list
        consented_list[str(user_id)]["strikes"] += 1
        with open(CONSENT_FILE, "w") as file:
            json.dump(consented_list, file, indent=4)        
            
    # Returns the number of strikes that the user has
    def get_strikes(self, user_id: int) -> int:
        with open(CONSENT_FILE, "r") as file:
            consented_list = json.load(file)
        if str(user_id) in consented_list:
            return int(consented_list[str(user_id)]["strikes"])
        else:
            # The user is an upstanding citizen!
            return 0
