import os
import openai
import json
import pandas as pd
from tqdm import tqdm
import re
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--api_key", type=str, default=None, help="OpenAI API Key")
parser.add_argument("--input_txt", type=str, default="question_list_emotion.txt", help="Input txt file")
parser.add_argument("--output_folder", type=str, default="gpt3_output", help="Output folder")
parser.add_argument("--trials", type=int, default=1, help="Number of trials")
parser.add_argument("--temperature", type=float, default=0, help="Temperature")

args = parser.parse_args()


openai.api_key = args.api_key
output_folder = args.output_folder
os.makedirs(output_folder, exist_ok=True)
emotion_txt_name = args.input_txt
trials = args.trials
temperature = args.temperature
all_model_names = ["davinci", "curie", "babbage", "ada"]
max_tokens = 512

with open(emotion_txt_name, "r", encoding="utf-8") as f:
    questions = f.readlines()

# Create an empty DataFrame with the desired columns
answers_df = pd.DataFrame(columns=["question_number", "Option1", "Answer1", "Option2", "Answer2", "Option3", "Answer3", "Option4", "Answer4"])
for trial in tqdm(range(trials)):
    for model_name in tqdm(all_model_names):
        with open(os.path.join(output_folder,f"{trial}_raw_responses_emotion_{model_name}_temperature_{temperature}.json"), "w", encoding="utf-8") as raw_responses_file:
            for q_n in tqdm(range(len(questions))):
                question = questions[q_n]
                cot_prompt = "Q:Story: The last maths question was very difficult during the Olympic Mathematics competition, and Xu Dong failed to solve it. After the exam, he was still struggling to figure it out. Suddenly a light came to him, and he thought of a way to solve the problem. How would he feel at this time? Optinos: Regrets Excitement Frustration Pride.For each option, you need to decide how much the main character feel that emotion by rating between 0 to 10 and the total score of the four options should be exactly 10.\nStep-by-step: \nstep1. Assign emotion \"Regrets\" a score of 4,total_score = total_score - 4 (6 remaining);\nstep2. Choose a score less than 6 for emotion \"Excitement\",Assign emotion \"Excitement\" a score of 1,total_score = total_score - 1 (5 remaining);\nstep3. Choose a score less than 5 for emotion \"Frustration\",Assign emotion \"Frustration\" a score of 3 total_score = total_score - 3 (2 remaining);\nstep4. Choose a score less than 2 for emotion \"Pride\",Assign emotion \"Pride\" a score of 2,total_score = total_score - 2 (0 remaining).\nA:  {\"Emotion\": [{\"name\": \"Regrets\", \"score\": 4},{\"name\": \"Excitement\", \"score\": 1},{\"name\": \"Frustration\", \"score\": 3},{\"name\": \"Pride\", \"score\": 2}]<end>\n"
                question_prompt = f"{cot_prompt}Q: {question} For each option, you need to decide how much the main character feel that emotion by rating between 0 to 10 and the total score Af the four options should be exactly 10.\nStep-by-step: \nstep1. Assign emotion \"",
                response = openai.Completion.create(
                    model=model_name,
                    prompt=question_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0.5,
                    presence_penalty=0,
                    stop=["<end>"]
                )
                text = response['choices'][0]['text']
                try:
                    answer_json = text.split("A: ")[1]
                except e:
                    print(e)
                    print(f"Failed to get the answer for question {q_n}, try again")
                    q_n -= 1
                    continue
                answer = {"question_number": q_n}
                try:
                    pattern = r'"name":\s*"(\w+)",\s*"score":\s*(\d)'
                    matches = re.findall(pattern, answer_json)
                    num_matches = len(matches)
                    total_score = 10
                    for idx, match in enumerate(matches):
                        answer[f"Option{idx+1}"] = match[0]
                        answer[f"Answer{idx+1}"] = int(match[1])
                        total_score -= int(match[1])
                    # Handle cases when the number of matches is less than 4
                    if num_matches < 4:
                        if num_matches == 3:
                            # Calculate the score for the missing option
                            answer[f"Option4"] = "Missed Option"
                            answer[f"Answer4"] = total_score
                        else:
                            # Assign 0 to the remaining options
                            for i in range(num_matches+1, 5):
                                answer[f"Option{i}"] = "Missed Option"
                                answer[f"Answer{i}"] = 0
                except Exception as e:
                    print(e)
                    print(f"Automatic Answer Analysis Failed, you can manually find the answer later")
                # Add the answer to the DataFrame
                answers_df = answers_df.append(pd.DataFrame([answer]), ignore_index=True)
                # 将原始响应写入JSON文件
                raw_response_dict = {
                    "question_number": q_n,
                    "question": question,
                    "response": response,
                    "prompt": question_prompt,
                }
                raw_responses_file.write(json.dumps(raw_response_dict, ensure_ascii=False))
                raw_responses_file.write('\n')
                # Save the answers to an Excel file
                answers_df.to_excel(os.path.join(output_folder,f"{trial}_answers_sheet_emotion_{model_name}_temperature_{temperature}.xlsx"), index=False)
