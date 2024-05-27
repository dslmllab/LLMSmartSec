import time
from time import sleep

from openai import OpenAI
import os
import csv

import os

#Specify the files to reivew
file_list = [
    "BlastDapp.sol",
    "BlastBox.sol",
    "BlastGovernor.sol",
    "BlastMagicLP.sol",
    "BlastOnboarding.sol",
    "BlastOnboardingBoot.sol",
    "BlastTokenRegistry.sol",
    "BlastWrappers.sol",
    "BlastPoints.sol",
    "BlastYields.sol",
    "MagicLP.sol",
    "FeeRateModel.sol",
    "FeeRateModelImpl.sol",
    "DecimalMath.sol",
    "Math.sol",
    "PMMPricing.sol",
    "periphery/Factory.sol",
    "periphery/Router.sol",
    "MagicLpAggregator.sol",
    "LockingMultiRewards.sol"
]



#update with your open AI API Key
def set_apikey():

    api_key = 'sk-proj-'
    return api_key
def pretty_print(messages):
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()


total_start_time = time.time()
total_api_cost = 0.0

# update with the model cost from openAI website

cost_per_request = 0.002
def get_developer_assistant(client):

    # update your openAI assistant ID
    assistant_id = 'asst_iGxx'
    assistant = client.beta.assistants.retrieve(assistant_id)
    return assistant

api_key = set_apikey()
if api_key:
    client = OpenAI(api_key=api_key)


assistant = get_developer_assistant(client)

print(assistant)


#Clone the repo to your local
csv_file_name = "responses_abracadabra_GPT4s.csv"

project_folder = "../../2024-03-abracadabra-money/src"


start_time = time.time()
for root, dirs, files in os.walk(project_folder):
    for file in files:
        if file in file_list:
            file_path = os.path.join(root, file)
            print(f"Found: {file_path}")


            if file.endswith(".sol"):
                file_path = os.path.join(root, file)
                print(f"Analyzing file: {file_path}")



                with open(file_path, "r") as f:
                    file_content = f.read()
                #thread.add_message(role="user", content=f"File: {file_path}\n\n{file_content}")
                thread = client.beta.threads.create(
                    messages=[
                        {
                            "role": "user",
                            "content": file_content,
                        }
                    ]
                )

                run = client.beta.threads.runs.create(
                    thread_id= thread.id,
                    assistant_id='asst_iGxx')
                print(run.status)

                while run.status != "completed":

                    run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
                    print(run.status)
                    sleep(10)
                    if run.status == "failed" or run.status == "expired":
                        print('failed')
                        run.status = "skip"
                        break


                if run.status == "completed":
                    print('here')

                    messages = client.beta.threads.messages.list(
                        thread_id=thread.id,run_id=run.id
                    ).data
                    end_time = time.time()
                    processing_time = end_time - start_time
                    for message in reversed(messages):
                        if message.role in ["assistant"]:
                            for content in message.content:
                                print(content)

                                with open(csv_file_name, mode='a', newline='') as file:
                                    writer = csv.writer(file)
                                    writer.writerow([file_path, content])  # Append each response to the CSV
                                total_api_cost += cost_per_request


total_processing_time = time.time() - total_start_time

print(f"Total processing time: {total_processing_time:.2f} seconds")
print(f"Estimated API cost: ${total_api_cost:.4f}")


with open("audit_summary_abracadabra_GPT4_s.csv", "w", newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Total Processing Time (in seconds)", "Estimated Total API Cost"])
    writer.writerow([round(total_processing_time, 2), round(total_api_cost, 4)])





