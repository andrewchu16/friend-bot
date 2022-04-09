# Friend-bot

## Introduction

Have you ever been up on Discord at night, feeling lonely? ~~This is a common issue that has beening affecting our developers. :)~~

Look no further, for `Friend Bot`! Friend bot is discord bot AI meant to talk like a normal person and respond to your messages! 
With Friend Bot, you will always have a companion to talk to, and you'll never be lonely again!

![The power of friendship!](https://cdn.discordapp.com/attachments/817583958861807632/962411330613157918/Screen_Shot_2022-04-09_at_1.58.55_PM.png)


## Commands

The prefix for Friend Bot is `!`

| Command | Description |
| --- | --- |
| `consent` | Consent to use the bot. Some messages are stored and used in prompts to Cohere, which we wanted the users to know. |
| `conversation` | Start a conversation with the bot. |
| `regenerate` | Regenerate the bot's last response with same cache. Maybe you're not happy with what the bot said, or you want a different storyline. |
| `reset` | Resets the user's conversation cache. |
| `end` | End a conversation with the bot. |

Messages for more nefarious purposes are frowned upon by the bot, and it may *just decide to ignore the sender :)*

---

## Technologies

| Technology | How it was used |
| --- | --- |
| Replit | Replit was the primary way we collaborated on the project. It allowed simulatenous edits, meaning that we could see what everyone was doing in real time. |
| Github | We used git and Github to store our project online. |
| Python | Python was the main language for this project. |
| discord.py | We used discord.py in order to create our discord bot. |
| Cohere API | The Cohere API was used to generate text from prompts. We configured the settings and structured the prompts such that the returned results were what we were looking for. |

## Challenges we ran into

- Because we wanted to balance financial viability and functionality, we didn't use Cohere's larger language models.
- There were a myriad of implementation barriers that we ran into while planning for our final product. For example, we didn't have access to finetuning, meaning that we had to deviate a little from our original vision.
- Using machine learning was new to us, so the journey of creating this bot was full of learning how to structure the prompts so that the output would be something useful.

## What we learned

**THE MAGIC OF FRIENDSHIP**

We learned about machine learning through the process of making this bot. Prior to this project, none of us had ever touched anything related to it. Sure, we heard things about it, but using it was another story. 

In addition, we learned how to better manage our time and plan ahead. Our project for the last YRHacks was a disaster because we bit off more than we could chew and ultimately ran out of time to implement many aspects of the tower defense game we envisioned. We didn't leave enough time to do the pitch, and consequently it didn't turn out the best.

We improved on our collaboration skills, and divided up the tasks so that more could be done. For example, some people were working on the bot while others were learning more about Cohere.

In conclusion, our experience participating in this hackathon was extremely fruitful and truly inspiring.
