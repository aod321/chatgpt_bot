# %% import library
import os
import openai
from datetime import datetime
from tqdm import tqdm
import re
import json
import pandas as pd
import os
import argparse
# %% argparse
parser = argparse.ArgumentParser()
parser.add_argument("--key", type=str)
# parser.add_argument("--select_model2", type=int, default=0)
parser.add_argument("--repeat_per_question", type=int, default=1)
args = parser.parse_args(args=[])
# args = parser.parse_args()
repeat_per_question = args.repeat_per_question
# selected_model2 = bool(args.select_model2)
key = args.key
# %% Configure access to the ChatGPT
openai.api_key = key
all_model_list = openai.Model.list()
all_model_id = [model.id for model in all_model_list.data]
print(f"Total number of models: {len(all_model_id)}")
print("All model ids:")
print(all_model_id)
# gpt-3.5-turbo-0301 or text-davinci-003
selected_model = "gpt-3.5-turbo-0301"
# if selected_model2:
    # selected_model = "text-davinci-003"
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
        failed = True
        failed_count = 0
        while failed:
            try:
                result = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                        {"role": "system", "content": "You are a helpful and understanding assistant."},
                        {"role": "user", "content": full_question},
                        # {"role": "assistant", "content": "Comment: Processing conversation with direct/indirect logical relationships detection.Question: Do you think fruit is cheap now?Statement: Xiao Zhu is very good at playing computer games.Comment: The statement and the question appear to be unrelated.Relationship: {No}, there is no logical relationship between the statement and the question.Output: {No}, the statement and the question have no logical relationship.Note: As there is no apparent logical relationship between the question and the statement, I cannot provide an explanation for a direct or indirect logical relationship."},
                        # {"role": "user", "content": "Do you usually eat breakfast?	I always get up at noon."}
                    ]
                )
                response = result['choices'][0]['message']['content']
                failed = False
            except Exception as e:
                if e is not KeyboardInterrupt:
                    failed_count+=1
                    print("Error: Ask Failed, try again")
                    failed = True
                    if failed_count > 10:
                        print("Error: Ask Failed for 10 times, skip this question")
                        break
        try:
            # re find {Yes} or {No}
            answer = re.findall("{(.*?)}", response)[0]
            print(f"Automatic Anwser Analysis Succeed, ChatGPT think the answer is: {answer}")
        except Exception as e:
            print(f"Automatic Anwser Analysis Failed, you can manually find the answer later: {response}")
            answer = "NotFound"
        # Wrte Response to json
        raw_response_dict = {
            "question_number": q_n,
            "question": question,
            "same_question_trials": t_n,
            "answer": answer,
            "response": result,
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