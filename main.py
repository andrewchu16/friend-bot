import os

import friendbot


disc_token = os.environ['discord_token']
cohere_token = os.environ['cohere_token']

def main():
    bot = friendbot.FriendBot(cohere_token)
    bot.run(disc_token)
    # a.run(cohere_token) shouldnt we first test a.py
    

if __name__ == '__main__':
    main()
