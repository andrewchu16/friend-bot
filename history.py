CONVO_LEN_MAX = 5

BASE_USER_MESSAGES = [
    "Hi, how was your day? Did you do anything exciting?",
    "Ouch, I bet that was quite a disappointment to you",
    "I was at school for the majority of the day. It was pretty stressful with all the new assignments",
    "All of them. I'm really going to have to pull some late nights in order to get them done",
    "All right, I will consider that when I finish it all. It will be likely too late by then though."
]
BASE_BOT_MESSAGES = [
    "My day was not the best. I thought that lunch would be exciting, but we got rained on.",
    "I know right! What about you? What did you do with your day?",
    "Really? What courses did you get a lot of homework on?",
    "make sure to get some sleep; otherwise, your productivity goes down the drain"
]

# The history a single user's conversations
class History:
    def __init__(self, user_name) -> None:
        self.user_history = []
        self.bot_history: list[tuple]  = []
        self.user_name = user_name

    # Export the history into a format that can be converted to a prompt
    def export(self) -> list:
        data = []

        # Export some base messages if user and bot convo history is too short
        for i in range(CONVO_LEN_MAX - len(self.user_history)):
            data.append((self.user_name, BASE_USER_MESSAGES[i]))
            data.append(("bot", BASE_BOT_MESSAGES[i]))

        for i in range(len(self.user_history)):
            data.append((self.user_name, self.user_history[i]))
            if i < len(self.bot_history):
                data.append(("bot", self.bot_history[i][0]))  

        return data

    def add(self, message: str, isBot = False, message_id = None):
        if isBot:
            self.bot_history.append((message, message_id))
            if len(self.bot_history) > CONVO_LEN_MAX:
                self.bot_history.pop(0)
        else:
            self.user_history.append(message)
            if len(self.user_history) > CONVO_LEN_MAX: 
                self.user_history.pop(0)

    def regenerate(self):
        # This is run when the bot edits its message, so the id is the same    
        if len(self.bot_history) > 0:
            message, message_id = self.bot_history.pop()
            return (message, message_id)
        else:
            return -1

    def reset(self):
        self.user_history.clear()
        self.bot_history.clear()