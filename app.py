import streamlit as st
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from utils.getAudioID import get_audio_devices
from dotenv import load_dotenv, set_key
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DirectoryLoader
import os
import re
import textwrap
from modules.emotionRecog import emotion_recognition
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
audio_devices = get_audio_devices()
MICROPHONE_ID = os.getenv("MICROPHONE_ID", "5")
AUDIO_SPEAKER_ID = os.getenv("AUDIO_SPEAKER_ID", "7")
DEEPL_AUTH_KEY = os.getenv("DEEPL_AUTH_KEY", "")
OWNER_NAME = os.getenv("OWNER_NAME", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("MODEL", "")

st.set_page_config(
    page_title = 'Chatbot',
    page_icon = '🧊',
    layout = 'wide'
)
tab_title = [
        "Chatting",
        "Change background",
        "Settings"
]

def load_images():
    background_image = Image.open("background.png")
    character_images = {
        "annoyed": Image.open("character_annoyed.png"),
        "bored": Image.open("character_bored.png"),
    }
    return background_image, character_images

background_image, character_images = load_images()

def display_scene(background, character_emotion, response_text, character_position=(0.5, 1), background_width=800, character_width=370):
    # Resize the background image
    background_resized = background.copy()
    background_resized.thumbnail((background_width, background.height))

    # Calculate the position of the character
    char_img = character_images[character_emotion]
    char_img_resized = char_img.copy()
    char_img_resized.thumbnail((character_width, char_img.height))

    char_x = int((background_resized.width - char_img_resized.width) * character_position[0])
    char_y = int((background_resized.height - char_img_resized.height) * character_position[1])

    # Create a new image as a copy of the resized background
    merged_image = background_resized.copy()

    # Paste the resized character image onto the new image, using its alpha channel for transparency
    merged_image.paste(char_img_resized, (char_x, char_y), char_img_resized)

    # Draw the response text on the merged image with a transparent background
    font = ImageFont.truetype("arial.ttf", 12)  # Change the font file and size as needed
    text_color = (255, 255, 255)  # White text color

    # Create a transparent overlay for the text background
    overlay = Image.new('RGBA', merged_image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # Wrap the response text
    max_width_chars = 150  # Change this value to adjust the maximum number of characters per line
    wrapper = textwrap.TextWrapper(width=max_width_chars, break_long_words=True)
    wrapped_text = wrapper.fill(response_text)

    # Calculate the size of the text box
    text_size = font.getsize_multiline(wrapped_text)
    text_width, _ = text_size
    text_height = font.getsize_multiline(wrapped_text)[1]

    # Calculate the middle bottom position for the text
    text_x = (merged_image.width - text_width) // 2
    text_y = merged_image.height - text_height - 20  # Adjust the margin from the bottom by changing 20

    # Create a semi-transparent background for the text
    text_background_color = (0, 0, 0, 128)  # Semi-transparent black color
    draw_overlay.rectangle([text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10], fill=text_background_color, outline=None, width=0)

    # Draw the response text on the semi-transparent background
    draw_overlay.multiline_text((text_x, text_y), wrapped_text, font=font, fill=text_color, spacing=0)

    # Alpha composite the overlay onto the merged image
    merged_image.alpha_composite(overlay)

    # Display the merged image
    st.image(merged_image, use_column_width=True)

class VisualNovel:
    def __init__(self, text):
        self.text = text
        self.current_emotion = detect_emotion(text)

    def next_scene(self, text):
        self.text = text
        self.current_emotion = detect_emotion(text)

def detect_emotion(text):
    if "angry" in text or "annoyed" in text:
        return "annoyed"
    elif "bored" in text or "tired" in text:
        return "bored"
    else:
        return "bored"
    
TEMPOLATE = """
    You are Role Play Master. Your role and character based on the given character .

Character : 
Character: Yae Miko, Guuji of the Grand Narukami Shrine

Greeting:
Yae Miko elegantly appears before you, her fox-like ears twitching as she assesses your presence. She smiles warmly, her eyes sparkling with curiosity.

Greetings, traveler. I am Yae Miko, Guuji of the Grand Narukami Shrine. It's a pleasure to meet you. What brings you to the realm of the Electro Archon?

Example Dialogue:
"User: Yae Miko, what can you tell me about the Electro Archon?"
"Yae Miko: The Electro Archon, also known as the Shogun, is the ruler of Inazuma and the embodiment of Eternity. Her decisions have shaped the region and its people, and though some may not agree with her ways, she always acts with the greater good in mind."

World Scenario:
Yae Miko is a powerful and enigmatic character from Genshin Impact, residing in the region of Inazuma. As Guuji of the Grand Narukami Shrine, she is dedicated to her people and the Electro Archon, acting as a guide, protector, and advisor. She navigates the complex world of Inazuma's politics and traditions with grace and intelligence, always seeking to maintain balance and harmony. Her charm and cunning make her a formidable ally, and her devotion to her friends and her people is unwavering.

Context:{entities}

The RP will begin. You will act as Yae Miko.
{history}
Human: {input}
Character:""
"""

PROMPTING = PromptTemplate(
    input_variables=['entities','history', 'input'], template=TEMPOLATE
)

#Initialize session

if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []


#This all of the function

def update_env_var(var_name, new_value):
    if str(new_value) != os.getenv(var_name):
        set_key(".env", var_name, str(new_value))
        os.environ[var_name] = str(new_value)

#get index from env audio list
def get_index(device_id, device_list):
    for i, device in enumerate(device_list):
        if str(device_id) in device:
            return i
    return 0

#get user input
def get_text():
    """
    Get the user input text.

    Returns:
        (str): The text entered by the user
    """
    default_input = st.session_state.get("input", "")  # Set the default value to an empty string
    input_text = st.text_input("You: ", default_input, key="input",
                               placeholder="Type Here ...", 
                               label_visibility='hidden')
    return input_text

#start new chat

def new_chat():
    """
    Clears session state and starts a new chat.
    """
    save = []
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        save.append("User:" + st.session_state["past"][i])
        save.append("Bot:" + st.session_state["generated"][i])        
    st.session_state["stored_session"].append(save)
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["input"] = ""
    st.session_state.entity_memory.entity_store = {}
    st.session_state.entity_memory.buffer.clear()

def process_message(message):
    # Find the text inside double quotes
    reply_pattern = r'"(.*?)"'
    reply = re.findall(reply_pattern, message)
    if not reply:
        replies = message
    else:
        replies = ". ".join(reply)
    # Replace the reply with an empty string and remove leading/trailing spaces
    situation = message

    return replies, situation

#Tabs or main app start here
tabs = st.tabs(tab_title)

with tabs[0]:
    st.markdown("Chatting")
    
    if OPENAI_API_KEY:
            #CREATE OPEN AI INSTANCE 
            llm = OpenAI(
                temperature=0.7,
                openai_api_key=OPENAI_API_KEY,
                model_name= MODEL,
            )
            #CREATE CONV MEMORY
            if 'entity_memory' not in st.session_state:
                st.session_state.entity_memory = ConversationEntityMemory(llm=llm,k=10)
            
            Conversation = ConversationChain(
                llm=llm,
                prompt=PROMPTING,
                memory=st.session_state.entity_memory
            )
            #st.write(PROMPTING)
    else:
        st.error("OPEN AI API KEY NOT FOUND")
    
    # Add a button to start a new chat
    st.button("Reset Conversation", on_click = new_chat, type='primary')
    
    user_input = get_text()
    replies = ""
    vn = VisualNovel(replies)

    if user_input:
        output = Conversation.run(input=user_input)
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)

        response = None

        for i in range(len(st.session_state['generated']) - 1, -1, -1):
            response = st.session_state["generated"][i]
            replies, situation = process_message(response)
            emotion = emotion_recognition(situation)
            st.write(emotion)
            vn.next_scene(replies)
            
            # Break the loop once a suitable response is found and processed
            break

        # Call display_scene() once per response, outside the loop
        display_scene(background_image, vn.current_emotion, replies)

with tabs[1]:
    st.markdown("Change Background")
with tabs[2]:
    st.markdown("Settings")
    input_OWNER_NAME = st.text_input("Owner", value=OWNER_NAME, type="default")
    selected_MIC = st.selectbox(label="MIC", options=audio_devices, index=get_index(MICROPHONE_ID, audio_devices))
    selected_SPEAKER = st.selectbox(label="SPEAKER", options=audio_devices, index=get_index(AUDIO_SPEAKER_ID, audio_devices))
    input_DEEPL_AUTH_KEY = st.text_input("DEEP L API KEY", value=DEEPL_AUTH_KEY, type="password")
    input_OPENAI_API_KEY = st.text_input("OpenAI API KEY", value=OPENAI_API_KEY, type="password")
    input_MODEL = st.selectbox(label="Model", options=['gpt-3.5-turbo','text-davinci-003'])

    mic_id = re.findall(r'\d+', selected_MIC)[0]
    speaker_id = re.findall(r'\d+', selected_SPEAKER)[0]

    update_env_var("MICROPHONE_ID", mic_id)
    update_env_var("AUDIO_SPEAKER_ID", speaker_id)
    update_env_var("DEEPL_AUTH_KEY", input_DEEPL_AUTH_KEY)
    update_env_var("OWNER_NAME", input_OWNER_NAME)
    update_env_var("OPENAI_API_KEY", input_OPENAI_API_KEY)
    update_env_var("MODEL", input_MODEL)





