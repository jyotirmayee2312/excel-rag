from langchain_aws import ChatBedrock
from langchain.prompts import PromptTemplate
from sqlalchemy import create_engine, text
from tenacity import retry, wait_exponential, stop_after_attempt
from langchain_community.utilities import SQLDatabase
from langchain_experimental.agents import create_pandas_dataframe_agent
import re
import botocore
import time
import pandas as pd

# ---------------- DB Connection ----------------
username = "admin"
password = "Admin1234"
host     = "database-1.c7ogiau4ix5v.ap-south-1.rds.amazonaws.com"
port     = 3306
database = "excel_rag"

engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")
db = SQLDatabase(engine)


def refresh_db():
    global db
    db = SQLDatabase(engine)
    return db

# ---------------- Retry Wrapper ----------------
def excel_to_mysql(excel_file):
    """
    Load all sheets of an Excel file into a MySQL database.
    Automatically detects the correct header row if multiple header rows exist.
    Each sheet becomes a table with the sheet name as the table name.
    """

    table_names = []
    sheet_dfs = pd.read_excel(excel_file, sheet_name=None, header=None)  # raw data

    username = "admin"
    password = "Admin1234"
    host = "database-1.c7ogiau4ix5v.ap-south-1.rds.amazonaws.com"
    port = "3306"
    database_name = "excel_rag"

    # SQLAlchemy engine
    engine = create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}")
    with engine.connect() as conn:
        # Disable FK checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # Get all tables
        tables = conn.execute(text("SHOW TABLES;")).fetchall()
        
        # Drop each table
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table[0]}`;"))
        
        # Re-enable FK checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

    def detect_header_row(df):
        best_row, max_score = 0, -1
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            non_nulls = row.notnull().sum()
            unique_vals = row.nunique()
            score = non_nulls + unique_vals
            if score > max_score:
                max_score, best_row = score, i
        return best_row

    for sheet_name, raw_df in sheet_dfs.items():
        print(f"\nProcessing sheet: {sheet_name}")

        # Detect header row
        header_row = detect_header_row(raw_df)
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

        # Save into MySQL
        df.to_sql(sheet_name, con=engine, if_exists="replace", index=False)
        print(f"✅ Data loaded into '{sheet_name}' table in '{database_name}'.")
        table_names.append(sheet_name)
    print(table_names)
    engine.dispose()
    print(f"\nAll sheets from '{excel_file}' loaded into '{database_name}' database.")
    return table_names


def is_retryable_exception(e):
    if isinstance(e, botocore.exceptions.ClientError):
        if "ThrottlingException" in str(e):
            return True
    if "Throttling" in str(e) or "Rate exceeded" in str(e):
        return True
    if "InternalServerError" in str(e) or "ModelError" in str(e):
        return True
    return False

class RetryableChatBedrock(ChatBedrock):
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(20),
        retry=lambda rs: is_retryable_exception(rs.outcome.exception()),
        reraise=True
    )
    def invoke(self, *args, **kwargs):
        return super().invoke(*args, **kwargs)

    def stream(self, *args, **kwargs):
        while True:
            try:
                for token in super().stream(*args, **kwargs):
                    yield token
                break
            except Exception as e:
                if is_retryable_exception(e):
                    print(f"Retryable error in stream: {e}, sleeping...")
                    time.sleep(10)
                    continue
                else:
                    raise

llm = RetryableChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    region_name="ap-south-1",
    model_kwargs={"temperature": 0, "max_tokens": 4000}
)

# ---------------- SQL Generator ----------------
def generate_sql_with_llm(question: str, schema: str) -> str:
    prompt = f"""
You are a SQL generator.

Schema:
{schema}

Task:
Write a SQL query that retrieves only the *relevant subset* of data required 
to answer the question. The query should filter by time ranges, product IDs, 
categories, or other conditions implied in the question. 

Rules:
- You MUST NOT compute derived metrics like percentages, ratios, 
  differences, or accuracy scores. Leave those for Python.
- Keep the query efficient by returning only necessary rows and columns.
- Do NOT return extra explanations or text — only SQL.
- don't use keywords as alias.
- if someone ask about how many table in this database or excel or sheet then take database_name as excel_rag.
- if column name contain space then wrap it in backticks (`).
- if column name contain "/" then wrap it in backticks (`).

Question:
{question}

SQL Query:
"""
    resp = llm.invoke(prompt).content.strip()
    print(resp)
    match = re.search(r"(SELECT|INSERT|UPDATE|DELETE)[\s\S]*?;", resp, re.IGNORECASE)
    if match:
        check=False
        return match.group(0).strip(),check
    else:
        check=True
        print("check",check)
        return resp,check

# ---------------- Run SQL ----------------
def execute_sql(query: str) -> pd.DataFrame:
    """Run SQL query against DB, return DataFrame."""
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)

        # ✅ Optional: Prevent overload if query returns too many rows
        if len(df) > 2000:
            print(f"⚠️ Large result ({len(df)} rows), truncating to first 2000 rows.")
            df = df.head(2000)

        return df

# ---------------- Pandas Agent ----------------
def run_dataframe_agent(question: str, df: pd.DataFrame, llm) -> str:
    instruction = f"""
You are a data analysis assistant. You must compute the final answer from the DataFrame provided.
Do NOT describe the DataFrame or repeat columns. Instead:
- Perform necessary calculations (e.g., sums, percentages, counts, groupings).
- Return only the final computed answer clearly and concisely (not as code).
- For inventory aging buckets, compute totals or relevant metrics as required by the question.
"""
    pandas_agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        allow_dangerous_code=True  

    )
    result = pandas_agent.invoke({"input": instruction + "\n\nQuestion: " + question})
    return result["output"]

# ---------------- Pipeline ----------------
def pipeline(question: str, table_names: list, max_retries: int = 5, check: bool=False) -> str:
    current_question = question
    schema = refresh_db().get_table_info()


    for attempt in range(max_retries):
        print(f"\n🔄 Attempt {attempt+1} ----------------------")
        
        # Generate SQL
        try:
            sql, check = generate_sql_with_llm(current_question, schema)
            print(f"Generated SQL:\n{sql}")
        except Exception as e:
            print(f"❌ SQL Generation Error: {e}")
            continue

        # Execute SQL
        try:
            if check:
                print("⚠️ Please correct the SQL query as it seems invalid.")
                return sql
            df = execute_sql(sql)
        except Exception as e:
            print(f"❌ SQL Execution Error: {e}")
            current_question = f"""
Original Question: {question}
The last SQL failed with error: {e}
Schema Info: {schema}
Be aware of column names with spaces must be in backticks (`) if name contain "/" then wrap it in backticks (`).
Please fix the SQL query and try again. Only return SQL.
"""
            continue

        # Handle empty result
        if df.empty:
            negation_prompt = f"""
Original Question: {question}

The SQL query returned no rows from the database. 
Based on this, provide a concise answer in natural language:
- Negate the condition in the question if appropriate (e.g., 'No, the condition is not met').
- If timing, stock levels, or additional info is missing, mention it clearly.
- Return only the final answer, do not include SQL or data.
- be aware of output parser structure.
"""
            llm_response = llm.invoke(negation_prompt).content.strip()
            return llm_response

        # ✅ Skip Pandas Agent if it's a metadata query
        if "INFORMATION_SCHEMA" in sql.upper():
            print("⚠️ Metadata query detected — returning raw SQL result.")
            return df.to_dict(orient="records")

        # Run Pandas agent otherwise
        try:
            if df.shape[1] == 1:
                return df.iloc[0, 0]

            final_answer = run_dataframe_agent(question, df, llm)
            return final_answer
        except Exception as e:
            print(f"❌ Pandas Agent Error: {e}")
            match = re.search(r"Could not parse LLM output:\s*`(.*?)`\s*For troubleshooting", str(e), re.DOTALL)

            if match:
                return match.group(1).strip()
            return str(e)

    return "NO result found"



# # ---------------- Run ----------------
# question = "which is most used packaging and the least used, along with Volume sold in each packaging type"
# final_answer = pipeline(question)
# print("\n💡 Final Answer:", final_answer)
