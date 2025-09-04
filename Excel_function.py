import sqlite3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import pandas as pd
import boto3
import faiss
import numpy as np
import sqlite3
import json
import os
import re

db_name = "data_2db.db"
region = "ap-south-1"
error_message=""
bedrock = boto3.client("bedrock-runtime", region_name=region)

# ================== FAISS Setup ==================

def csv_to_sqlite(excel_file, db_name):
    """
    Load all sheets of an Excel file into a SQLite database.
    Automatically detects the correct header row if multiple header rows exist.
    Each sheet becomes a table with the sheet name as the table name.
    """

    # Read all sheets into a dictionary of DataFrames (without setting header yet)
    table_names = []

    sheet_dfs = pd.read_excel(excel_file, sheet_name=None, header=None)  # raw data

    # Connect to SQLite
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"Database '{db_name}' deleted successfully.")
    else:
        print(f"Database '{db_name}' does not exist.")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    def detect_header_row(df):
        """
        Detect the most likely header row.
        Strategy:
        - Choose the row with the most non-null and unique values
        """
        best_row = 0
        max_score = -1
        for i in range(min(10, len(df))):  # check first 10 rows
            row = df.iloc[i]
            non_nulls = row.notnull().sum()
            unique_vals = row.nunique()
            score = non_nulls + unique_vals
            if score > max_score:
                max_score = score
                best_row = i
        return best_row

    def create_table_from_df(df, table_name):
        col_types = []
        for col in df.columns:
            dtype = df[col].dtype
            if dtype == "int64":
                col_type = "INTEGER"
            elif dtype == "float64":
                col_type = "REAL"
            else:
                col_type = "TEXT"
            col_types.append(f'"{col}" {col_type}')
        col_definitions = ", ".join(col_types)
        create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_definitions});'
        cursor.execute(create_table_query)
        print(f"Table '{table_name}' created with schema: {col_definitions}")
  
    # Loop through sheets
    for sheet_name, raw_df in sheet_dfs.items():
        print(f"\nProcessing sheet: {sheet_name}")

        # Detect correct header row
        header_row = detect_header_row(raw_df)
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

        # Create table and insert
        table_names.append(sheet_name)
        create_table_from_df(df, sheet_name)
        df.to_sql(sheet_name, conn, if_exists="replace", index=False)
        print(f"Data loaded into '{sheet_name}' table in '{db_name}'.")

    conn.commit()
    conn.close()
    print(f"\nAll sheets from '{excel_file}' loaded into '{db_name}' SQLite database.")
    return table_names


# def get_embeddings(text):
#     """
#     Converts text into an embedding using Amazon Titan on Bedrock.
#     """
#     response = bedrock.invoke_model(
#         modelId="amazon.titan-embed-text-v1",
#         body=json.dumps({"inputText": text}),
#         contentType="application/json",
#         accept="application/json"
#     )
#     output = json.loads(response["body"].read())
#     embedding = np.array(output["embedding"])
#     return embedding


# def search_cache(question_embedding, threshold=0.1):
#     """
#     Searches FAISS index for a similar question.
#     """
#     if index.ntotal > 0:
#         distances, indices = index.search(np.array([question_embedding]), k=1)
#         if distances[0][0] < threshold:
#             cache_index = indices[0][0]
#             return cache[cache_index][1], cache[cache_index][2]
#     return None


def get_table_schema(db_name, table_name):
    """
    Retrieves schema for a SQLite table.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table_name}");')
    schema = cursor.fetchall()
    conn.close()
    return schema

def checking_query(sql_query, user_question, db_name, table_names):
    """
    Rechecks the SQL query against the user question and table schemas.
    """
    max_retries = 5
    delay = 1
    for attempt in range(1, max_retries + 1):
        result = run_sql_query(db_name, sql_query)
        if result is not None:
            global error_message
            error_message = ""
            return result
        else:
            print(f"Retry {attempt}/{max_retries} failed. Retrying...")
            # time.sleep(delay)
            print("Error_message : ", error_message)
            sql_query = generate_sql_query(user_question, table_names)

def handle_user_question(user_question, table_names):
    """
    Handles the user's question by first searching the cache, and if there's no hit, generating a SQL query and response.
    
    Args:
        user_question (str): The user's natural language question.
    
    Returns:
        list: The response to the user's question.
    """
    # Convert the user's question to an embedding
    # question_embedding = get_embeddings(user_question)
    
    # Step 1: Search cache for similar questions
    # cache_hit = search_cache(question_embedding)
    # if cache_hit:
    #     sql_query, response = cache_hit
    #     print(f"Cache hit! SQL Query: {sql_query}")
    #     return response
    
    # Step 2: No hit, go to LLM for SQL generation
    # print("Cache miss! Generating SQL from LLM...")
    sql_query = generate_sql_query(user_question, table_names)
    
    # Step 3: Run the SQL query on the database
    response = checking_query(sql_query, user_question, db_name, table_names)
    
    # Step 4: Store question, SQL, and response in cache
    # cache.append((user_question, sql_query, response))
    # index.add(np.array([question_embedding]))  # Add question embedding to FAISS index

    llm_response = final_LLM(user_question, sql_query, response)

    return llm_response


def final_LLM(question, sql_query, response):
    print("Question : ", question)
    print("Sql_Query : ", sql_query)
    print("Response : ", response)

    # Build dynamic prompt
    final_prompt = f"""
You are a data assistant.  
The user asked the following question:
{question}

The SQL query executed was:
{sql_query}

The raw database response is:
{response}

Your task:
1. Provide a **clear, direct, and complete answer** to the user’s question using the response.
2. sometimes response comes with "None" means in table there is empty but othe  
2. If the response seems incomplete or unclear, **augment with logical/statistical reasoning** instead of talking about fixing the query.  
3. Do **not** explain SQL or analyze the query itself. Just give the user the best possible **final answer** in plain language.  
4. Format the answer so it reads like a business insight, not a technical log.
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "messages": [
            {"role": "user", "content": final_prompt}
        ]
    }

    response_llm = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    final_output = json.loads(response_llm["body"].read())
    final_answer = final_output["content"][0]["text"]

    return final_answer

def generate_llm_prompt(db_name, table_names, error_message=""):
    """
    Builds an instruction prompt for the LLM with all table schemas
    and optionally includes the last error message.
    """
    schema_texts = []
    for table in table_names:
        schema = get_table_schema(db_name, table)
        schema_text = "\n".join([f'"{col[1]}" ({col[2]})' for col in schema])
        schema_texts.append(f"Table '{table}':\n{schema_text}\n")

    error_section = ""
    if error_message.strip():
        error_section = f"""
The last generated SQL query failed with this error:
{error_message}

Please fix the mistake and regenerate a correct query.
"""

    return f"""
You are an expert SQLite assistant.
Here are the schemas for all available tables:

{chr(10).join(schema_texts)}

{error_section}

Rules:
- Generate a single valid SQL query. Do not include multiple statements or semicolons.
- Always wrap column names and table names in double quotes (") in your SQL queries.
- When generating SQL queries, never use SQL reserved words like AS, ON, JOIN, etc. as table aliases. Always choose a safe short alias like a, b, fd, act.
- If Question contain wrong column name then check it near by column names (ex "Packaging" but actual column name is "Packageing").
- Always double-check column names against schema_texts before using them in the SQL query. If a column is not present, do not invent or assume it. Use only the exact column names from schema_texts.
- Output ONLY a valid SQL query inside a fenced code block: ```sql ... ```
- Do not add extra explanations, only return pure SQL inside code fences.
- Always separate each selected column or CASE expression with a comma.
- Ensure the query is valid SQLite syntax.
"""


def generate_sql_query(question, table_names):
    """
    Uses Claude Haiku on AWS Bedrock to generate a SQL query from a natural language question.
    """
    # table_names = ['Forecast Data',
    #                'Open Order',
    #                'Actual Sales',
    #                'Warehouse Inventory',
    #                'Customer Receivable',
    #                'List of queries']
    # table_schema = get_table_schema(db_name, table_names)

    llm_prompt = generate_llm_prompt(db_name, table_names)
    user_prompt = f"Question: {question}"

    # Bedrock Claude request (no 'system' role inside messages)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "system": llm_prompt,   # system prompt goes here ✅
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )
    output = json.loads(response["body"].read())
    answer = output["content"][0]["text"]

    # Clean SQL
    # query = answer.replace("```sql", "").replace("```", "").strip()
    query=answer
    # print("Generated SQL:\n", query)

    # Extract SQL between ```sql ... ```
    match = re.search(r"```sql\s+(.*?)```", query, re.DOTALL)
    if match:
        sql_query = match.group(1).strip()
    else:
        # fallback: try to find first SELECT...; block
        match = re.search(r"(SELECT.*?;)", query, re.DOTALL | re.IGNORECASE)
        sql_query = match.group(1).strip() if match else query.strip()
    print("Query : ", sql_query)
    return sql_query

def run_sql_query(db_name, query):
    """
    Executes a SQL query on a SQLite database and returns the results.

    Args:
        db_name (str): The name of the SQLite database file.
        query (str): The SQL query to run.

    Returns:
        list: Query result as a list of tuples, or an empty list if no results or error occurred.
    """
    try:
        print("Running query...")
        # Connect to the SQLite database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(query)

        # Fetch all results
        results = cursor.fetchall()

        # Close the connection
        conn.close()
        print("Done")
        # Return results or an empty list if no results were found
        return results if results else []
    
    except sqlite3.Error as e:
        print(f"An error occurred while executing the query: {e}")
        global error_message
        error_message = str(e)
        return None


def main():
    csv_file = "Sales_Data_for_AI_Model_-_Operisoft.xlsx"
    csv_to_sqlite(csv_file, db_name)
    # print(table_names)
    question = "What is the total sales amount for each product?"
    output_response=handle_user_question(question)
    print(output_response)


if __name__ == "__main__":
    main()