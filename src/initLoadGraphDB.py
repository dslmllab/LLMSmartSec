import json
from datasets import load_dataset
from openai import OpenAI
import os
from textwrap import wrap
from neo4j import GraphDatabase
import csv
import re
from neo4j.exceptions import CypherSyntaxError

#Update the key with your openai key.

os.environ["OPENAI_API_KEY"] = "sk-"


#Give your local neo4j desktop password.

uri = "bolt://localhost:7687"
user = "neo4j"
password = "changeme7"
driver = GraphDatabase.driver(uri, auth=(user, password))


dataset = load_dataset("mwritescode/slither-audited-smart-contracts", "all-multilabel")

LABELS = {
    0: 'access-control',
    1: 'arithmetic',
    2: 'other',
    3: 'reentrancy',
    4: 'safe',
    5: 'unchecked-calls'
}

def extract_cypher_queries(text):
    cypher_queries = []
    pattern = r'```cypher\s*(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        cypher_queries.append(match.strip())
    print(cypher_queries)
    return cypher_queries

def preprocess_code(code):

    code = re.sub(r'\/\/.*', '', code)


    code = re.sub(r'\/\*[\s\S]*?\*\/', '', code)


    code = re.sub(r'\s+', ' ', code)


    #max_line_length = 100
    #code_lines = code.split('\n')
    #truncated_lines = [line[:max_line_length] for line in code_lines]
    code = '\n'.join(code)

    return code

def generate_cypher_queries(contract_address, code, example):
    label_name = []
    for label in example["slither"]:
        label_name.append(LABELS.get(label))
        print(label_name)

    print(code)

    client = OpenAI()


    prompt = f"""
    As an AI language model, your task is to generate Cypher queries that create a comprehensive Knowledge Graph (KG) representing vulnerability patterns in smart contracts. The KG should capture the following crucial elements:

    1. Contract Nodes:
    - Create nodes with the label "Contract" for each smart contract. 
    - Include properties such as "address", "name", "sourceCode", and other relevant metadata.
    
    2. Vulnerability Nodes:
    - Create nodes with the label "Vulnerability" for different types of vulnerabilities (e.g., reentrancy, integer overflow/underflow, access control issues).
    - Include properties like "name", "description", "severity", "cweId", and "cveId" to describe the vulnerability.
    
    3. Vulnerability Relationships:
    - Establish relationships between "Contract" nodes and "Vulnerability" nodes using the "HAS_VULNERABILITY" or "AFFECTED_BY" relationship types.
    
    4. Code Pattern Nodes:
    - Create nodes with the label "CodePattern" representing specific code patterns indicative of vulnerabilities.
    - Include properties like "pattern", "description", and "vulnerability" to describe the code pattern and its associated vulnerability.
    - Connect "CodePattern" nodes to the corresponding "Vulnerability" nodes using the "INDICATES" or "ASSOCIATED_WITH" relationship types.
    
    5. Function Nodes:
    - Create nodes with the label "Function" for individual functions within smart contracts.
    - Include properties like "name", "visibility", and "vulnerability" to describe the function and its associated vulnerabilities. 
    - Connect "Function" nodes to "Contract" nodes using the "DEFINED_IN" or "PART_OF" relationship types.

    6. Variable Nodes:
    - Create nodes with the label "Variable" for important variables used within smart contracts.
    - Include properties like "name", "type", and "vulnerability" to describe the variable and its associated vulnerabilities.
    - Connect "Variable" nodes to "Contract" or "Function" nodes using the "USED_IN" or "DEFINED_IN" relationship types.
    
    7. Control Flow Relationships:
    - Establish relationships between "Function" nodes to represent control flow using the "CALLS" or "TRANSFERS_CONTROL_TO" relationship types.

    8. Data Flow Relationships: 
    - Establish relationships between "Variable" nodes and "Function" nodes to represent data dependencies and flows using the "READS_FROM" or "WRITES_TO" relationship types.

    9. External Interaction Nodes:
    - Create nodes with appropriate labels (e.g., "ExternalContract", "Library") for external entities interacted with by the smart contracts.
    - Connect these external entity nodes to "Contract" or "Function" nodes using the "INTERACTS_WITH" or "CALLS_EXTERNAL" relationship types.

    10. Mitigation Technique Nodes:
    - Create nodes with the label "MitigationTechnique" representing mitigation techniques or best practices for specific vulnerabilities. 
    - Connect "MitigationTechnique" nodes to the corresponding "Vulnerability" nodes using the "MITIGATES" or "PREVENTS" relationship types.
       
    11. Fixes Nodes:
    - Create nodes with the label "Fix" representing specific fixes or patches for identified vulnerabilities.
    - Include properties like "description", "version", and "fixType" to describe the fix.
    - Connect "Fix" nodes to the corresponding "Vulnerability" nodes using the "FIXES" or "PATCHES" relationship types.
       
    12. Recommendation Nodes: 
    - Create nodes with the label "Recommendation" representing recommendations or best practices to improve smart contract security.
    - Include properties like "description", "category", and "priority" to describe the recommendation.
    - Connect "Recommendation" nodes to relevant "Contract", "Function", or "Vulnerability" nodes using the "RECOMMENDS" or "SUGGESTS" relationship types.

    13. Analyze the Solidity code and identify the relevant entities such as other contracts, variables, functions, and Dataset labels. For each entity:
       - Create a node with an appropriate label (e.g., 'Contract', 'Variable', 'Function').
       - Set relevant properties on the node to store important information about the entity.
    
    14. Create an additional node with the label 'LLM_Insights' to capture your audit summary on the smart contract. Set relevant properties on this node to store the insights and observations from you.
    
    15. Use the `WITH` clause to pass the created nodes and relationships from the `CREATE` clause to the subsequent `MATCH` clause. This is required to avoid the "WITH is required between CREATE and MATCH" error.
    
    16. In the `MATCH` clause, use the previously created central Contract node to establish meaningful relationships with the other entity nodes and the LLM_Insights node:
       - Use appropriate relationship types (e.g., 'CALLS', 'DEFINES', 'REFERENCES', 'HAS_INSIGHT') to connect the nodes based on their interactions in the Solidity code and the LLM audit.
       - If applicable, set properties on the relationships to provide additional context or metadata.
    
    17. Ensure that the generated Cypher queries are well-structured, efficient, and follow Neo4j best practices for query optimization.
    
    Please generate Cypher queries that create the necessary nodes, relationships, and properties to build this vulnerabilities pattern Knowledge Graph. Ensure that the queries are properly formatted, efficient, and adhere to Neo4j best practices.
    
    Provide the generated Cypher queries in a code block format, with each query separated by a blank line for readability.

    
 
    Solidity code:
    {code}
    
    
    Contract ID: {contract_address}
    
    Return the generated Cypher queries as a single string, with each query separated by a newline.
    """
    chunk_size = 10000
    if len(code) > 10000:
        text_resp = []

        text_chunks = wrap(code, width=chunk_size)
        for chunk in text_chunks:
            completion = client.chat.completions.create(
                model="gpt4",
                temperature=0.2,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": chunk}
                ]
            )
            text_resp.append(completion.choices[0].message.content)
    else:
        completion = client.chat.completions.create(
            model="gpt-4",
            temperature=0.2,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": code}
            ]
        )
        text_resp = []
        text_resp.append(completion.choices[0].message.content)

    return text_resp

def execute_cypher_queries(cypher_queries):
    with driver.session() as session:
        for query in cypher_queries.split(';'):
            query = query.strip()
            if query:
                session.run(query)

def process_examples(start_index, end_index, output_file):
    with open(output_file, "a") as file:
        for i in range(start_index, end_index):
            example = dataset["train"][i]
            contract_address = example["address"]
            source_code = example["source_code"]
            preprocessed_code = preprocess_code(source_code)

            try:
                cypher_queries = generate_cypher_queries(contract_address, preprocessed_code, example)
                cypher_queries_str = '\n'.join(cypher_queries)
                cypher_queries_str_ = extract_cypher_queries(cypher_queries_str)
                cypher_queries_str = '\n'.join(cypher_queries_str_)
                file.write(cypher_queries_str)
                #file.write("\n\n")

                for label in example["slither"]:
                    label_name = LABELS.get(label, f"Unknown_Label_{label}")
                    query = f"MATCH (c:Contract {{address: '{contract_address}'}}) MERGE (l:Label {{name: '{label_name}'}}) MERGE (c)-[:HAS_LABEL]->(l)"
                    print(query)
                    file.write(query)
                    with driver.session() as session:
                        session.run(query)
                file.write("\n\n")
                try:
                    execute_cypher_queries(cypher_queries_str)
                except CypherSyntaxError as e:
                    print(f"Error executing Cypher queries for contract {contract_address}: {str(e)}")
                    continue

            except Exception as e:
                print(f"Error generating queries for contract {contract_address}: {str(e)}")
                continue

            print(f"Processed example {i + 1}/{end_index}")

def main():
    output_file = "cypher_queries.txt"
    batch_size = 1
    num_examples = len(dataset["train"])
    num_examples = 5

    for start_index in range(0, num_examples, batch_size):
        end_index = min(start_index + batch_size, num_examples)
        process_examples(start_index, end_index, output_file)

    driver.close()

if __name__ == "__main__":
    main()