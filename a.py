import languageModel
import history

def run(api_key):
    languageModel.Model(api_key)
    histoire = history.History(420)
    running = True
    lang = languageModel.Model(api_key)
    while running:
        k = input().split(":")
        histoire.add(69, k[1])
        lang.create_prompt(69, histoire.export(69))
        response = lang.generate_response(69)
        histoire.add(69, response, True)
        print(response)
        
        
        
        
        