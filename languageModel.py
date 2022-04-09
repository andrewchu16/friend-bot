import cohere


class Model:
    def __init__(self, api_key):
        self.co = cohere.Client(api_key)
        self.model = 'medium'
        self.num_tokens = 50
        self.temperature = 1.2
        self.top_p = 0.75
        self.freq_penalty = 0.1
        self.pres_penalty = 0.1
        self.stop_seq = "--"
        

    # converts a discord conversation to a cohere-styled prompt.
    @staticmethod
    def conversation_to_prompt(conversation: list[str]):
        pass

    # converts a file to a cohere-styled prompt.
    @staticmethod
    def file_to_prompt(file_name: str):
        pass

    # for friend bot idea
    def respond_to(self, prompt: str):
        response = "nothing yet"

        prediction = self.co.generate(
            model=self.model,
            prompt=prompt,
            max_tokens=self.num_tokens,
            temperature=self.temperature,
            k=0,
            p=self.top_p,
            frequency_penalty=self.freq_penalty
        )

        print(prediction)

        response = prediction.generations[0].text
        
        return response
