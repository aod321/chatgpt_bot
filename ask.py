# %% import library
from revChatGPT.V1 import Chatbot
from datetime import datetime
from tqdm import tqdm
import re
import json
import pandas as pd
import os
import argparse
# %% argparse
parser = argparse.ArgumentParser()
parser.add_argument("--email", type=str)
parser.add_argument("--password", type=str)
parser.add_argument("--use_paid_model", type=int, default=0)
parser.add_argument("--repeat_per_question", type=int, default=1)
# args = parser.parse_args(args=[])
args = parser.parse_args()
repeat_per_question = args.repeat_per_question
email = args.email
password = args.password
use_paid = bool(args.use_paid_model)
# %% Configure access to the ChatGPT
chatbot = Chatbot(config={
  "email": email,
  "password": password,
  "paid": use_paid,
})
# %% Create folder to save the data
raw_json_output_folder = "raw_json_output"
answer_sheet_folder = "answer_sheet"
time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
answer_sheet_folder_path = os.path.join(os.getcwd(), answer_sheet_folder, time_stamp)
json_output_folder_path = os.path.join(os.getcwd(), raw_json_output_folder, time_stamp)
os.makedirs(answer_sheet_folder_path, exist_ok=True)
os.makedirs(json_output_folder_path, exist_ok=True)
json_output_name = "raw_response.json"
#%%  Read the prompt from txt
prompt_txt_file = "prompt.txt"
with open(prompt_txt_file, "r") as f:
    raw_prompt = f.read()
#%% Read all the questions from txt
questions_txt_file = "question_list.txt"
with open(questions_txt_file, "r") as f:
    questions = f.readlines()
print(f"Total {len(questions)} questions, and each repeat {repeat_per_question} times")
# %% Ask all the questions line by line, each question ask N times
answer_trial_dict = {}
for t_n in range(repeat_per_question):
    answer_trial_dict[t_n] = []
for q_n, question in tqdm(enumerate(questions)):
    for t_n in range(repeat_per_question):
        full_question = f"{raw_prompt}{question}"
        # Start asking
        response = ""
        for data in chatbot.ask(
          full_question
        ):
            response = data["message"]
        try:
            # re find {Yes} or {No}
            answer = re.findall("{(.*?)}", response)[0]
            print(f"Answer found: {answer}")
        except:
            print(f"Waring No Answer found: {response}")
            answer = "NotFound"
        # Wrte Response to json
        raw_response_dict = {
            "question_number": q_n,
            "question": question,
            "same_question_trials": t_n,
            "answer": answer,
            "response": response,
            "prompt": raw_prompt,
        }
        # write raw_response_dict to json
        with open(os.path.join(json_output_folder_path, json_output_name), "a") as f:
            json.dump(raw_response_dict, f)
            f.write("\n")
        # write answer to answer_sheet
        answer_trial_dict[t_n].append({"question_number": q_n, "answer": answer})
        # answer_sheet.json
        with open(os.path.join(json_output_folder_path, "answer_sheet.json"), "a") as f:
            json.dump(answer_trial_dict, f)
            f.write("\n")
# save answer_list to excel
for t_n in range(repeat_per_question):
    df = pd.DataFrame(answer_trial_dict[t_n])
    df.to_excel(os.path.join(answer_sheet_folder_path, f"answer_sheet_trial{t_n}.xlsx"))
# %%