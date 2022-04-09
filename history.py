CONVO_LEN_MAX = 5

# The history a single user's conversations
class History():
    def __init__(self, user_name) -> None:
        self.user_history = []
        self.bot_history: list[tuple]  = []
        self.user_name = user_name

    def export(self) -> list:
        base_user_messages = [
            "Hi, how was your day? Did you do anything exciting?",
            "Ouch, I bet that was quite a disappointment to you",
            "I was at school for the majority of the day. It was pretty stressful with all the new assignments",
            "All of them. I'm really going to have to pull some late nights in order to get them done",
            "All right, I will consider that when I finish it all. It will be likely too late by then though."
        ]
        base_bot_messages = [
            "My day was not the best. I thought that lunch would be exciting, but we got rained on.",
            "I know right! What about you? What did you do with your day?",
            "Really? What courses did you get a lot of homework on?",
            "make sure to get some sleep; otherwise, your productivity goes down the drain"
        ]

        data = []

        # add in base messages of data is too short
        for i in range(CONVO_LEN_MAX - len(self.user_history)):
            data.append((self.user_name, base_user_messages[i]))
            data.append(("bot", base_bot_messages[i]))

        for i in range(len(self.user_history)):
            data.append((self.user_name, self.user_history[i]))
            if i < len(self.bot_history):
                data.append(("bot", self.bot_history[i][0]))  
            # self.bot_history is list[tuple[msg, msg_id]]

        return data

    # ok so basically the data for the user is just going to be by message and then we add the name in for formatting
        # but the data for the bot is going to be a tuple (message, id) which stores the message id and we need to store the message id so that we know where the message is so we can edit it when we are regenerating 
    def add(self, message: str, isBot = False, message_id = None):
        if isBot: # If it's a bot 
            self.bot_history.append((message, message_id))
            if len(self.bot_history) > CONVO_LEN_MAX:
                self.bot_history.pop(0)
        else: # If it's a user
            self.user_history.append(message)
            if len(self.user_history) > CONVO_LEN_MAX: 
                self.user_history.pop(0)

    def regenerate(self):
        # This is run when the bot edits its message, so the id is the same
        message, message_id = self.bot_history[-1]
        self.bot_history[-1] = (message, message_id)

    def reset(self):
        self.user_history.clear()
        self.bot_history.clear()
        # self.last_message.pop(user)