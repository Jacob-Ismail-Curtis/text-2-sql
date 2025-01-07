import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from table_schema import schema

def select_columns(model, table_schema: str, user_question: str):
    # Split the string construction into manageable parts
    task_description = f"""
    ### TASK ###
    You are a highly skilled data analyst. Your goal is to examine the provided {table_schema}, interpret the posed {user_question}, and identify the specific columns from the relevant tables required to construct an accurate SQL query.

    The database schema includes tables, columns, primary keys, foreign keys, relationships, column descriptions and any relevant constraints.
    """
    
    instructions = """
    ### INSTRUCTIONS ###
    1. Carefully analyze the schema and identify the essential tables and columns needed to answer the question.
    2. For each table, provide a clear and concise reasoning for why specific columns are selected.
    3. List each reason as part of a step-by-step chain of thought, justifying the inclusion of each column.
    4. If a "." is included in columns, put the name before the first dot into chosen columns.
    5. The number of columns chosen must match the number of reasoning.
    6. Final chosen columns must be only column names, don't prefix it with table names.
    7. If the chosen column is a child column of a STRUCT type column, choose the parent column instead of the child column.
    """
    
    final_answer_format = """
    ### FINAL ANSWER FORMAT ###
    Please provide your response as a JSON object, structured as follows:

    {
        "results": [
            {
                "table_selection_reason": "Reason for selecting tablename1",
                "table_contents": {
                "chain_of_thought_reasoning": [
                    "Reason 1 for selecting column1",
                    "Reason 2 for selecting column2",
                    ...
                ],
                "columns": ["column1", "column2", ...]
                },
                "table_name":"tablename1",
            },
            {
                "table_selection_reason": "Reason for selecting tablename2",
                "table_contents":
                {
                "chain_of_thought_reasoning": [
                    "Reason 1 for selecting column1",
                    "Reason 2 for selecting column2",
                    ...
                ],
                "columns": ["column1", "column2", ...]
                },
                "table_name":"tablename2"
            },
            ...
        ]
    }
    """
    
    # Concatenate the parts into the final prompt string
    prompt = f"{task_description} {instructions} {final_answer_format}"
    
    response = model.generate_content(prompt).text
    return response

def initialise_vertex_ai(location="europe-west2"):
    vertexai.init(location=location)
    return GenerativeModel("gemini-1.5-pro-001")

# Load environment variables
load_dotenv('./.env')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


table_schema = schema
model = initialise_vertex_ai()
user_question = "How many people work onshore vs offshore?"
selected_columns = select_columns(model, table_schema, user_question)
print(selected_columns)
