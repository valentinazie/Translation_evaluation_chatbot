# import gradio as gr
# import random
# import time
# import json

# css='./css/template.css'

# """
# Global 변수, 함수 선언
# """

# selected_mode = 'Search'

# title=(
#     """
#     <center> 
#     <h1> Sample Chatbot  🛰️ </h1>
#     <br/><br/>
#     </center>
#     """
# )

# def change_mode(value):
#     global selected_mode
#     selected_mode = value
#     print(selected_mode)

# def change_slider(value):
#     print(value)

# def change_dropdown(value):
#     print(value)

# def add_message(history, message):
#     if message["text"] is not None:
#         history.append((message["text"], None))
#     return history, gr.MultimodalTextbox(value=None, interactive=False)

# def bot(history):
#     global selected_mode
#     if selected_mode == 'Search':
#         bot_message = "Search 모드 입니다. "
#     else:
#         bot_message = "AI Assistant Search Mode입니다. "
    
#     history[-1][1] = ""
#     for character in bot_message:
#         history[-1][1] += character
#         time.sleep(0.05)
#         yield history
    

# with gr.Blocks( css=css) as demo:
#     gr.HTML(title)

#     with gr.Row():
#         with gr.Column(scale=3, ): 
#             mode = gr.Radio(
#                 choices=["Search", "AI Assistant Search"],
#                 value="Search",
#                 label="Search Mode",
#             )
#             slider = gr.Slider(3, 10, value=4, label="Result Count", info="Choose between 3 and 10", step=1)
#             dropdown = gr.Dropdown(["Paper", "Patent", "News"], value=["Paper"], multiselect=True, label="Source", info="")
            
#             mode.change(change_mode, mode)
#             slider.change(change_slider, slider)
#             dropdown.change(change_dropdown, dropdown)

#         with gr.Column(scale=7, elem_id='col'):
#             chatbot = gr.Chatbot(
#                 elem_id="chatbot",
#                 bubble_full_width=False,
#                 scale=1,
#                 avatar_images=["files/ci.jpg", "files/avatar.png"]
#             )
            
#             chat_input = gr.MultimodalTextbox(
#                 interactive=True,
#                 placeholder="Enter message...",
#                 show_label=False,
#                 submit_btn=True
#             )

#             chat_msg = chat_input.submit(
#                 add_message, [chatbot, chat_input], [chatbot, chat_input]
#             )
#             bot_msg = chat_msg.then(
#                 bot, [chatbot], chatbot
#             )
#             bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input])


# demo.launch()


import os
from dotenv import load_dotenv
# Load the environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
PUBLIC_URL = os.getenv("PUBLIC_URL")

import gradio as gr
import requests
import json

css = './css/template.css'

# Get the IAM token
token_url = "https://iam.cloud.ibm.com/identity/token"
token_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}
token_data = {
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    "apikey": API_KEY,
}


def reset_iam_token():
    try:
        token_response = requests.post(token_url, headers=token_headers, data=token_data, verify=False)
        token_response.raise_for_status()
        iam_token = token_response.json()["access_token"]
        print("Token successfully created")
        return iam_token
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining IAM token: {e}")
        return None


def bot(content, translation1, translation2):
    iam_token = reset_iam_token()
    if not iam_token:
        return [("Error", "Could not obtain IAM token.")]

    scoring_url = PUBLIC_URL
    scoring_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {iam_token}",
    }

    scoring_data = {
        "parameters": {
            "prompt_variables": {
                "CONTENTS": content,
                "TRANSLATED_CONTENT1": translation1,
                "TRANSLATED_CONTENT2": translation2
            }
        }
    }

    try:
        print(f"Sending request to API with data: {json.dumps(scoring_data, indent=2)}")
        scoring_response = requests.post(scoring_url, headers=scoring_headers, json=scoring_data)
        scoring_response.raise_for_status()

        response_json = scoring_response.json()
        print(f"API Response: {json.dumps(response_json, indent=2)}")

        if "results" in response_json and len(response_json["results"]) > 0:
            bot_message = response_json['results'][0].get("generated_text", "No generated text found in response.")
            print(f"Generated Text: {bot_message}")
            return [(content, bot_message)]
        else:
            error_message = "Error: Unexpected response format from API."
            print(error_message)
            return [("Error", error_message)]

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {scoring_response.content}")
        return [("Error", f"HTTP error occurred: {http_err}")]

    except requests.exceptions.RequestException as req_err:
        print(f"API request error: {req_err}")
        return [("Error", f"API request error: {req_err}")]

    except Exception as e:
        print(f"Unexpected error: {e}")
        return [("Error", f"Unexpected error: {e}")]


with gr.Blocks(css=css) as demo:
    gr.HTML("<center><h1>Ko-En Translation result comparison Bot 🤖🍎</h1></center>")

    # Remove the image column and enlarge the chat column
    with gr.Row():
        with gr.Column(scale=8):
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                bubble_full_width=False,
                scale=1,
            )

    # Inputs at the bottom
    with gr.Row():
        with gr.Column(scale=3):
            content_input = gr.Textbox(
                interactive=True,
                placeholder="Enter content...",
                label="Content"
            )

        with gr.Column(scale=3):
            translation1_input = gr.Textbox(
                interactive=True,
                placeholder="Enter translation 1...",
                label="Translation 1"
            )

        with gr.Column(scale=3):
            translation2_input = gr.Textbox(
                interactive=True,
                placeholder="Enter translation 2...",
                label="Translation 2"
            )

        with gr.Column(scale=1):
            submit_button = gr.Button("Submit")
            submit_button.click(
                bot, [content_input, translation1_input, translation2_input], chatbot
            )

demo.launch(share=False)

# gr.Interface(classify_image, "image", "label").launch(share=True)
