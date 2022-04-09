import os
import friendbot

# The Discord bot token
disc_token = os.environ['discord_token']
# The Cohere API token
cohere_token = os.environ['cohere_token']

def main():
    bot = friendbot.FriendBot(cohere_token)
    bot.run(disc_token)

if __name__ == '__main__':
    main()
