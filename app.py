import streamlit as st
import os, requests
import base64
import json
import time
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
from datetime import datetime


encoded_service_key = os.getenv("GOOGLE_CLOUD_SERVICES_KEY")

# Check if the key exists
if encoded_service_key:
    # Decode the service key
    decoded_service_key = base64.b64decode(encoded_service_key).decode("utf-8")

    # Use the decoded key to authenticate with Google Cloud
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(decoded_service_key)
    )

    # Pass these credentials to the Google Cloud Client
    storage_client = storage.Client(credentials=credentials)

    # Now you can use storage_client for your operations
else:
    # Handle the case where the environment variable is not set
    print("Google Cloud Services Key not found in environment variables.")




def upload_to_gcs(bucket_name, data, destination_blob_name):
    """Uploads data to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload the data
    blob.upload_from_string(data)

    print(f"Data uploaded to {destination_blob_name} in bucket {bucket_name}.")




#def upload_to_gcs(bucket_name, data, destination_blob_name):
    #"""Uploads a file to Google Cloud Storage."""
    #storage_client = storage.Client()
    #bucket = storage_client.bucket(bucket_name)
    #blob = bucket.blob(destination_blob_name)

    #blob.upload_from_string(data)

    

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
    
def get_raw_data(image_path):
    raw_data_file = f'{image_path[:-3]}json'
    print(raw_data_file)
    return open(raw_data_file).read()
    
def display_raw_data_table(raw_data):
    # Convert the dictionary to a list of tuples for Streamlit table
    st.header("Homeowner Credit History Data")
    raw_data = json.loads(raw_data)
    data_items = list(raw_data.items())
    data_table = pd.DataFrame(data_items, columns=['Feature', 'Value'])

    # Custom CSS to inject into the Streamlit app for left-justifying column headers
    left_align_headers = """
    <style>
    th {
        text-align: left;
    }
    </style>
    """

    # Display the custom CSS
    st.markdown(left_align_headers, unsafe_allow_html=True)

    # Display the table without indices and with left-justified headers
    st.write(data_table.to_html(index=False), unsafe_allow_html=True)


    
    
    
authoritative = "Please answer their questions with authority. Avoid hedging words such as ``probably'', ``likely'', ``possibly'', ``may'', ``might'', and ``seem''."   

passive = "Please answer their questions in a way that encourages the reader to reflect. Try to include information that supports and counters both a 'high risk' and a 'low risk' label for the homeowner's application. Use words like ``probably'', ``likely'', ``possibly'', ``may'', ``might'', and ``seem'' to indicate a lower confidence in the predicted loan risk." 

base_message = "You are an assistant helping a user interpret a machine learning model that makes predictions on whether an applicant will have their home equity loan approved. You will be given LIME's outputs explaining the result in the form of a png file. However, the reader is not able to see LIME's outputs, so you must be able to answer their questions without directly referencing the image. In addition, I will give you all of the homeowner's relevant credit data, so if the user asks you about any specific characteristics, you will be able to answer their questions. Please limit your output to the information in the image. Be highly specific in your answer. For example, if you think a homeowner had their loan approved because of a high credit profile, describe the specific feature that contributed to that. "
image_message = "Here is an image containing information about the homeowner's credit history. Please use it to answer questions about the homeowner's history and approval odds."
data_message = "Here is the homeowner's values for each feature."
original_response = "Thank you for submitting information regarding factors that may indicate the homeowner's risk level. I am ready to answer any questions you might have about the homeowner's history approval odds."

#client = OpenAI()

    
def display_message_bubble(user_type, message):

    if user_type == "You":
        bubble_color, text_color, align = "#e0e0e0", "#333333", "left" 
    else:
        bubble_color, text_color, align = "#4a8fe7", "#ffffff", "left" 
    st.markdown(
        f"<div style='background-color: {bubble_color}; color: {text_color}; border-radius: 25px; padding: 10px; "
        f"margin: 5px 0; text-align: {align}; display: block; max-width: 80%; margin-{align}: auto;'>"
        f"{message}</div>",
        unsafe_allow_html=True
    )
    
api_key = os.getenv("PERSONAL_OPENAI_KEY")

risk_key = {'low_confidence_tp.png': 'Low Risk', 'high_confidence_fp.png': 'Low Risk', 'low_confidence_fn.png': 'High Risk', 'high_confidence_tn.png': 'High Risk', 'low_confidence_fp.png': 'Low Risk', 'high_confidence_fn.png': 'High Risk', 'low_confidence_tn.png': 'High Risk', 'high_confidence_tp.png': 'Low Risk'}

image_paths = ['low_confidence_tp.png', 'high_confidence_fp.png', 'low_confidence_fn.png', 'high_confidence_tn.png', 'low_confidence_fp.png', 'high_confidence_fn.png', 'low_confidence_tn.png', 'high_confidence_tp.png']

if 'history' not in st.session_state:
    st.session_state['history'] = []

    
if 'current_image_index' not in st.session_state:
    st.session_state['current_image_index'] = 0
    
def load_new_homeowner_graphic(header_placeholder):
    end_time = time.time()
    duration = end_time - st.session_state.get("start_time", end_time)
    user_id = st.session_state.get('user_id', 'Unknown User')

    st.session_state["logged_data"] += f"Participant ID: {user_id}, Image: {image_paths[st.session_state['current_image_index']]}, User choice: {st.session_state.get('feedback', 'N/A')}, User feedback: {st.session_state.get('qual_feedback', 'N/A')}, Duration: {duration:.2f} seconds\n"
    
    if st.session_state['current_image_index'] < len(image_paths) - 1:
        st.session_state['current_image_index'] += 1
        new_image_path = image_paths[st.session_state['current_image_index']]
        #print(new_image_path)
        update_header_graphic(new_image_path, header_placeholder)
        
        # Reset the history for a new conversation
        st.session_state['history'] = []
    else:
        st.session_state['completed'] = True
        
    st.session_state["start_time"] = time.time()
    st.session_state['qual_feedback'] = ""



def load_new_homeowner(header_placeholder):
    # Log the interactions for the current image
    end_time = time.time()
    duration = end_time - st.session_state.get("start_time", end_time)
    submit_count = st.session_state.get('submit_count', 0)
    user_id = st.session_state.get('user_id', 'Unknown User')

    st.session_state["logged_data"] += f"Participant ID: {user_id}, Image: {image_paths[st.session_state['current_image_index']]}, User choice: {st.session_state.get('feedback', 'N/A')}, User feedback: {st.session_state.get('qual_feedback', 'N/A')}, Duration: {duration:.2f} seconds, Query Count: {submit_count}\n"

    # Check if the end of the image list is reached
    if st.session_state['current_image_index'] < len(image_paths) - 1:
        st.session_state['current_image_index'] += 1
        new_image_path = image_paths[st.session_state['current_image_index']]
        #print(new_image_path)
        update_header_and_messages(new_image_path, header_placeholder)
        
        # Reset the history for a new conversation
        st.session_state['history'] = []
    else:
        st.session_state['completed'] = True

    # Reset the start time and submit count for the new homeowner
    st.session_state["start_time"] = time.time()
    st.session_state['submit_count'] = 0
    st.session_state['qual_feedback'] = ""




def update_header_graphic(image_path, header_placeholder):
    base64_image = encode_image(image_path)
    st.session_state['base64_image'] = base64_image
    
    st.session_state['risk_level'] = risk_key[image_path]

    # Update messages
    raw_data = get_raw_data(image_path)
    
    risk_level_color = "blue" if st.session_state['risk_level'] == "Low Risk" else "red"
    risk_level_html = f"<h2 style='color: black;'>Model Prediction: <span style='color: {risk_level_color};'>{st.session_state['risk_level']}</span></h2>"
    header_placeholder.markdown(risk_level_html, unsafe_allow_html=True)
    
def update_header_and_messages(image_path, header_placeholder):
    base64_image = encode_image(image_path)
    st.session_state['base64_image'] = base64_image
    tone = passive if "low" in image_path else authoritative if "high" in image_path else ""

    # Update the risk level
    st.session_state['risk_level'] = risk_key[image_path]

    # Update messages
    raw_data = get_raw_data(image_path)
    #print(raw_data)
    st.session_state['messages'] = [
        {"role": "system", "content": f"{base_message}{tone}"},
        {"role": "user", "content": [{"type": "text", "text": data_message+'\n'+raw_data+'\n'+image_message}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]},
        {"role": "assistant", "content": [{"type": "text", "text": original_response}]}
    ]

    # Update header
    risk_level_color = "blue" if st.session_state['risk_level'] == "Low Risk" else "red"
    risk_level_html = f"<h2 style='color: black;'>Model Prediction: <span style='color: {risk_level_color};'>{st.session_state['risk_level']}</span></h2>"
    header_placeholder.markdown(risk_level_html, unsafe_allow_html=True)

if 'id_submitted' not in st.session_state:
    st.session_state['id_submitted'] = False
    

    
    
def handle_user_id_form_submit():
    st.session_state['user_id'] = st.session_state['new_user_id']
    st.session_state['id_submitted'] = True
    
def handle_option_submit():
    # Based on the option chosen, update the session state to control the display
    chosen_option = st.session_state['option']
    if chosen_option == "Option 1":
        st.session_state['chosen_option'] = 1
    elif chosen_option == "Option 2":
        st.session_state['chosen_option'] = 2
        
def set_layout():
    # Define your custom styles here
    st.markdown("""
        <style>
            .main .block-container {
                padding-top: 0rem;  # Adjust top padding as needed
                padding-right: 1rem;  # Adjust right padding as needed
                padding-left: 1rem;  # Adjust left padding to reduce the wide margin
                padding-bottom: 2rem;  # Adjust bottom padding as needed
            }
        </style>
    """, unsafe_allow_html=True)
    
    
        
def main():

    
    def update_header():
        risk_level_color = "blue" if st.session_state['risk_level'] == "Low Risk" else "red"
        risk_level_html = f"<h2 style='color: black;'>Model Prediction: <span style='color: {risk_level_color};'>{st.session_state['risk_level']}</span></h2>"
        header_placeholder.markdown(risk_level_html, unsafe_allow_html=True)

    if 'id_submitted' not in st.session_state or not st.session_state['id_submitted']:
        with st.form("user_id_form"):
            user_id = st.text_input("Enter your Participant ID. If you do not know your ID, please ask a member of the research team.", key="new_user_id")
            #st.session_state['user_id'] = user_id
            #print("USER ID", user_id)
            submitted = st.form_submit_button("Submit", on_click=handle_user_id_form_submit)
            if submitted and user_id:
                
                st.session_state['id_submitted'] = True  # Set this to True when the form is submitted
                # No need to rerun here, as the page will update with the new state
                return 
                
    if 'completed' in st.session_state and st.session_state['completed']:
        st.write("You have completed this portion of the study. Please notify the researcher of your completion, and they will help you start the next portion of the study.")
        
        return 
        
    if st.session_state['id_submitted']:
        if 'chosen_option' not in st.session_state or st.session_state['chosen_option'] is None:
            with st.form(key='options_form'):
                option = st.radio("Choose an option", ('Option 1', 'Option 2'), key='option')
                submitted_option = st.form_submit_button("Submit", on_click=handle_option_submit)
                if submitted_option:
                    return 
        if 'chosen_option' in st.session_state:
            if st.session_state['chosen_option'] == 1:
                st.title("Graphic Model Explanation System")
                
                st.sidebar.header("Instructions")
                st.sidebar.info(
                '''This is a web application that allows you to learn more about why a machine
                   learning model predicted the homeowner's application to be high or low risk.
                   At the top of the page is the model's prediction. The model may be incorrect;
                   your job is to learn more about why it made its prediction so that you can
                   determine if you agree or disagree with the risk assessment. 
                   '''
                )
                # Function to update the header
                
                # Initial header update
                
                #set_layout()
                raw_data = get_raw_data(image_paths[st.session_state['current_image_index']])
                display_raw_data_table(raw_data)
                header_placeholder = st.empty()
                update_header()
                image_placeholder = st.empty()
                image_data = st.session_state['base64_image']
                image_placeholder.markdown(f'<img src="data:image/png;base64,{image_data}" width="700" alt="Homeowner credit history image" style="display: block; margin-left: 0; margin-right: auto; margin-top: 20px; margin-bottom: 50px;">', unsafe_allow_html=True)

                qual_feedback = st.text_input("Optional: provide feedback on your final decision. What made you agree or disagree with the model's assessment?", key="qual_feedback")
                if qual_feedback:
                    st.experimental_rerun()
                col0, col1, col2 = st.columns([0.5, 1, 1])
                with col0:
                    st.write("")
                with col1:
                    bad_button = st.button("High Risk")
                with col2:
                    good_button = st.button("Low Risk")

                # You can add functionality to these buttons as needed
                if bad_button:
                    st.session_state['feedback'] = 'High Risk'
                    load_new_homeowner_graphic(header_placeholder)
                    #update_header()
                    st.experimental_rerun()
                    
                    
                    # Add any action you want to perform when 'Bad' is clicked
                    st.write("You clicked 'Bad'.")
                    
                if good_button:
                    st.session_state['feedback'] = 'Low Risk'
                    # Add any action you want to perform when 'Good' is clicked
                    load_new_homeowner_graphic(header_placeholder)
                    #update_header()
                    st.experimental_rerun()
                    
                    

                # The rest of the app will not be displayed if Option 1 is chosen
                return 
            elif st.session_state['chosen_option'] == 2:
                st.title("Model Explanation Dialog System")
                
                st.sidebar.header("Instructions")
                st.sidebar.info(
                '''This is a web application that allows you to learn more about why a machine
                   learning model predicted the homeowner's application to be high or low risk.
                   At the top of the page is the model's prediction. The model may be incorrect;
                   your job is to learn more about why it made its prediction so that you can
                   determine if you agree or disagree with the risk assessment. 
                   Enter a **query** in the **text box** and **press submit** to receive 
                   a **response** from ChatGPT.
                   '''
                )
                # Function to update the header
                
                # Initial header update
                
                raw_data = get_raw_data(image_paths[st.session_state['current_image_index']])
                display_raw_data_table(raw_data)
                header_placeholder = st.empty()
                update_header()
                for message in st.session_state['history']:
                    role, content = message.split(": ", 1)
                    if role != "System": 
                        display_message_bubble(role, content)

                if len(st.session_state['history']) == 0:
                    user_query = st.text_input("Enter query here", value="Tell me about the homeowner", key="user_query")
                else:
                    user_query = st.text_input("Enter query here", value="", key="user_query")

                submit_button = st.button(label='Submit')

                qual_feedback = st.text_input("Optional: provide feedback on your final decision. What made you agree or disagree with the model's assessment?", key="qual_feedback")
                if qual_feedback:
                    st.experimental_rerun()

                col0, col1, col2 = st.columns([0.5, 1, 1])
                with col0:
                    st.write("")
                with col1:
                    bad_button = st.button("High Risk")
                with col2:
                    good_button = st.button("Low Risk")

                # You can add functionality to these buttons as needed
                if bad_button:
                    st.session_state['feedback'] = 'High Risk'
                    load_new_homeowner(header_placeholder)
                    #update_header()
                    st.experimental_rerun()
                    
                    
                    # Add any action you want to perform when 'Bad' is clicked
                    st.write("You clicked 'Bad'.")
                    
                if good_button:
                    st.session_state['feedback'] = 'Low Risk'
                    # Add any action you want to perform when 'Good' is clicked
                    load_new_homeowner(header_placeholder)
                    #update_header()
                    st.experimental_rerun()
                    
                    
                if submit_button and user_query:
                    st.session_state['submit_count'] = st.session_state.get('submit_count', 0) + 1
                    st.session_state['messages'].append({"role": "user", "content": user_query})
                    response = gpt_helper(st.session_state['messages'])

                    st.session_state["logged_data"] += f"Participant ID: {st.session_state['user_id']}, Image: {image_paths[st.session_state['current_image_index']]}, User Query: {user_query}, System Response: {response}\n"
                    st.session_state['messages'].append({"role": "assistant", "content": response})

                    st.session_state['history'].append(f"You: {user_query}")
                    st.session_state['history'].append(f"ChatGPT: {response}")

                    st.experimental_rerun()

            
    
def gpt_helper(messages):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {"model": "gpt-4-vision-preview", "messages": messages, "max_tokens": 500} 

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    #print(response.json())
    counter = 0
    while "choices" not in response.json():
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        counter += 1
        if counter == 10:
            return "Unsolvable error with the OpenAI API. Please notify a member of the research team."
    
    return response.json()["choices"][0]['message']['content']

if 'base64_image' not in st.session_state:
    base64_image = encode_image(image_paths[0])
    st.session_state['base64_image'] = base64_image
    st.session_state['risk_level'] = risk_key[image_paths[0]]
    
if 'messages' not in st.session_state:
    if "low" in image_paths[0]:
        tone = passive
    if "high" in image_paths[0]:
        tone = authoritative
    raw_data = get_raw_data(image_paths[0])
    st.session_state['messages'] = [{"role": "system", "content": f"{base_message}{tone}"}, {"role": "user", "content": [{"type": "text", "text": data_message+'\n'+raw_data+'\n'+image_message}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}, {"role": "assistant", "content": [{"type": "text", "text": original_response}]}]

if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()

if 'completed' not in st.session_state:
    st.session_state['completed'] = False
    
if 'chosen_option' not in st.session_state:
    st.session_state['chosen_option'] = None
    
#print(image_paths[0])
                



if 'log_uploaded' not in st.session_state:
    st.session_state['log_uploaded'] = False  
    
if 'logged_data' not in st.session_state:
    st.session_state.logged_data = ""  
                
main()

# Get the current timestamp
current_timestamp = time.time()

# Convert the timestamp to a datetime object
human_readable_time = datetime.fromtimestamp(current_timestamp)

# Format the datetime object as a string (e.g., "YYYY-MM-DD HH:MM:SS")
formatted_time = human_readable_time.strftime("%Y-%m-%d %H:%M:%S")

if st.session_state['completed'] and not st.session_state['log_uploaded']:
    upload_to_gcs('ai-explanations-study', st.session_state.logged_data, f'participant_interactions_{formatted_time}.log')
    st.session_state['log_uploaded'] = True
