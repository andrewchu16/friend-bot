import discord
import datetime
import languageModel


# Class for the Discord Bot
class FriendBot(discord.Client):
    # Initialization method
    def __init__(self) -> None:
        super().__init__(intents = discord.Intents.all(), status = discord.Status.idle)
        self.who = None
        self.msgCount = {}
        
        self.model = languageModel.Model('{api_key}')
    
    # Runs when the bot is fully connected to Discord
    async def on_ready(self) -> None:
        activity = discord.Game(
            name = "Getting coded!",
            start = datetime.datetime.now()
            )
        await self.change_presence(status = discord.Status.online, activity = activity)
        print("Bot is online")

    # Runs when a new message is sent
    async def on_message(self, message) -> None:
        # Prevent bot from responding to itself
        if message.author == self.user:
            return
        # Alerts the console that a message has been sent
        print("New message!: " + message.content)
                
        if message.author in self.msgCount.keys():
            self.msgCount[message.author] += 1
        else:
            self.msgCount[message.author] = 0

        if "message count" in message.content:
            if message.mentions[0] not in self.msgCount:
                await message.channel.send(f"{message.mentions[0].mention} has sent 0 messages since my last boot up!")
            else:
                await message.channel.send(f"{message.mentions[0].mention} has sent {(self.msgCount[message.mentions[0]])} messages since my last boot up")
            
        if "message history" in message.content:
            if message.content.split(" ")[-1].isdigit():
                num = int(message.content.split(" ")[-1])
            else:
                num = 100
            async with message.channel.typing():
                count = 0
                if len(message.mentions) == 0:
                    person = message.author
                else:
                    person = message.mentions[0]
                async for m in message.channel.history(limit = num):
                    if m.author == person:
                        count += 1

            await message.channel.send(f"in the past {num} messages, {person.mention} has sent {count} messages")
            #does ctx work
         
           

