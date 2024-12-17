import instructor
import vertexai
from pydantic import BaseModel
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import pandas as pd
import json
import re
from vertexai.generative_models import GenerativeModel, GenerationConfig
from enum import Enum
from typing import List, Tuple, Optional
import concurrent.futures
from IPython.utils.io import capture_output
import tiktoken
import concurrent.futures

from openai import OpenAI

project_id = "prj-lbg-dialogwithdata-270624"

def initialise_vertex_ai(project_id, location="europe-west2"):
    vertexai.init(project=project_id, location=location)
    return GenerativeModel("gemini-1.5-pro-001")


with capture_output():
    client = instructor.from_vertexai(
        client=GenerativeModel("gemini-1.5-pro-002"),
        mode=instructor.Mode.VERTEXAI_TOOLS,
    )

# Structured output classes

# Zero-shot structured SQL output
class SQLGenerationOutput(BaseModel):
    sql_query: str
    sql_explanation: str

# TAI-shot structured SQL output
class Action(str, Enum):
    RUN_SQL = 'Run SQL'
    CONTINUE = 'Continue'
    FINISH = 'FINISH'

class SQLResponse(BaseModel):
    critical_thinking: str
    sql: str
    action: Action
    finished: str

class ThoughtSQLActionTriplet(BaseModel):
    triplet: List[SQLResponse]

# Validation output
class ValidationOutput(BaseModel):
    validation_results: str = "Validation results not provided."
    validation_bool: bool
    agent_error_bool: bool
    
# Assumptions output
# class ConsiderationOption(BaseModel):
#     number: int
#     description: str
#     follow_up: Optional[str]

# class Consideration(BaseModel):
#     description: str
#     options: List[ConsiderationOption]

# class AssumptionsOutput(BaseModel):
#     assumptions: List[Consideration]
#     ambiguities: List[Consideration]
#     edge_cases: List[Consideration]

class AssumptionsOutput(BaseModel):
    assumptions: str

    # Table schema

table_schema=r"""CREATE TABLE "people" (
"resource_id" TEXT PRIMARY KEY, --- Colleague's GID, the unique number assigned to each colleague. **No NULL values observed**. 
  "full_name" TEXT, --- Colleague's first and last names
  "email" TEXT, --- Colleague's LBG email address
  "first_name" TEXT,--- Colleague's first name
  "last_name" TEXT, --- Colleague's last name
  "direct_line_manager_id" TEXT, --- GID the unique number assigned assigned to colleague's line manager
  "direct_line_manager_name" TEXT, --- first and last names of colleague's line manager
  "line_manager_email" TEXT, --- LBG email address of colleague's line manager
  "location_name" TEXT, --- LBG building colleague primarily works out of
  "data_source" TEXT, --- System where colleague's data is mastered; Possible values: ('Workday', 'Beeline', 'OIM-Beeline','Workday_Advanced', 'Workday Headcount Prompt'). **NULL values observed - requires further investigation to determine the source.**
  "hub_location" TEXT, --- Identifies the regional hub that a colleague's primary work location is part of
  "is_onshore" TEXT, --- Identifies if a colleague is based in the UK ('onshore') or elsewhere ('offshore')
  "fte" REAL, --- Identifies whether a colleague is Full Time (FTE = 1) or on reduced hours (FTE < 1); if the latter shows the amount of an FTE the reduced hours equate to (e.g. 4 days a week = 0.8). **fte should not exceed 1 and no values greater than 1 were observed. All observed values are within the expected range of 0-1.**
  "scheduled_working_hours" REAL, --- The number of hours per week a colleague is contracted to work; corresponds to their FTE amount. **Should be a positive value and no negative values were observed.**
  "grade" TEXT, --- Colleague's grade, or if colleague is a contingent worker the equivalent grade of the role they are fulfilling
  "job_title" TEXT, --- Title of colleague's role in Workday for perms and in Beeline for non-perms
  "job_code" TEXT, --- Code that is assigned to each job type in Workday
  "business_title" TEXT, --- Title of colleague's role in Workday for perms and in Beeline for non-perms 
  "cost_centre_id" TEXT, --- Cost Centre number
  "agency" TEXT, --- Name of contingent workers' agency
  "original_tenure_start" TEXT, --- Date colleague started at LBG. **NOTE: This column contains a significant number of NULL values (231 observed). It is unclear if these represent new employees or a data collection issue. Further investigation is recommended.**
  "current_start_date" TEXT, --- Date that colleague's most recent assignment started if they've had multiple periods of service
  "leave_date" TEXT, --- Date that colleague is due to leave where known
  "contractor_day_rate_banding" TEXT, --- Obfuscation code indicating day rate range for contingent workers eg: Rhino, (NULL), Kangaroo, Bison, Wombat, etc
  "on_leave" TEXT, --- Flags if a colleague is on leave
  "job_family" TEXT, --- Job family of colleague's role
  "worker_type" TEXT, --- Identifies colleagues' contract type - permanent or different types of non-permanent eg: 5. T&M Partner, 1. Permanent Colleague, 8. IT Specialist, 6. Fixed Price Partner, 9. Professional Services Consultant, etc
  "high_lev_workertype" TEXT, ---Identifies colleagues' contract type - permanent or different types of non-permanent - but groups partner types eg: Partner, Permanent, IT Specialist, Consultant, Contractor
  "funding_source" TEXT, --- Identifies how colleagues are paid. Possible values include: 'BAU', 'Delivery', 'TBC', 'Business Support'. **NOTE: This field also contains NULL values, requiring further investigation. Distinct values observed:  ('Delivery', 'BAU', NULL, 'TBC', 'Business Support')**
  "division" TEXT, --- Division that the colleague is part of eg: Platforms 2 Shadow Rep, Chief Data & Analytics Office, Retail Platforms, GCOO Centre INV, Chief Technology Office, etc
  "cc_layer_1" TEXT, --- layer 1 cost centre in colleague's reporting line
  "cc_layer_2" TEXT, --- layer 2 cost centre in colleague's reporting line
  "cc_layer_3" TEXT, --- layer 3 cost centre in colleague's reporting line
  "cc_layer_4" TEXT, --- layer 4 cost centre in colleague's reporting line
  "is_manager" TEXT, --- Flag denoting whether colleague is set as a manager in Workday {Manager = Yes}. **Note: Discrepancies observed between "is_manager" flag and presence of direct reports. Requires further investigation on how "is_manager" is defined.**
  "post_code" TEXT, --- post code of colleague's primary work location **Note: Discrepancies observed between city and post code. Requires further investigation.**
  "city" TEXT, --- city of colleague's primary work location **Note: Discrepancies observed between city and post code. Requires further investigation.**
  "location_id" REAL, --- unique code associated with colleague's primary location
  "position_id" TEXT, --- unique code associated with the colleague's role in the organisational structure
  "workday_job_family_group" TEXT, --- Workday Job Family that the colleague's role belongs to
  "workday_job_category" TEXT, --- Workday Job Category that the colleague's role belongs to
  "compensation_grade_profile" TEXT, --- Comprised of colleagues pay group and grade 
  "oim_learner" TEXT, --- Flag in OIM designating whether colleague is classified as having to complete mandatory training
  "workday_learner" TEXT, --- Flag in Workday designating whether colleague is classified as having to complete mandatory training
  "learner_type" TEXT, --- Identifies whether colleague is designated as having to complete or is exempt from mandatory training  
  "layer_2" TEXT, --- Name of colleague positioned at layer 2 in colleague's reporting line
  "layer_3" TEXT, --- Name of colleague positioned at layer 3 in colleague's reporting line
  "layer_4" TEXT, --- Name of colleague positioned at layer 4 in colleague's reporting line
  "layer_5" TEXT, --- Name of colleague positioned at layer 5 in colleague's reporting line
  "layer_6" TEXT, --- Name of colleague positioned at layer 6 in colleague's reporting line
  "layer_7" TEXT, --- Name of colleague positioned at layer 7 in colleague's reporting line
  "layer_8" TEXT, --- Name of colleague positioned at layer 8 in colleague's reporting line
  "layer_9" TEXT, --- Name of colleague positioned at layer 9 in colleague's reporting line
  "layer_10" TEXT, --- Name of colleague positioned at layer 10 in colleague's reporting line
  "layer_11" TEXT, --- Name of colleague positioned at layer 11 in colleague's reporting line
  "layer_12" TEXT, --- Name of colleague positioned at layer 12 in colleague's reporting line
  "layer_13" TEXT, --- Name of colleague positioned at layer 13 in colleague's reporting line
  "layer_2_file_id" TEXT, --- GID colleague positioned at layer 2 in colleague's reporting line
  "layer_3_file_id" TEXT, --- GID colleague positioned at layer 3 in colleague's reporting line
  "layer_4_file_id" TEXT, --- GID colleague positioned at layer 4 in colleague's reporting line
  "layer_5_file_id" TEXT, --- GID colleague positioned at layer 5 in colleague's reporting line
  "layer_6_file_id" TEXT, --- GID colleague positioned at layer 6 in colleague's reporting line
  "layer_7_file_id" TEXT, --- GID colleague positioned at layer 7 in colleague's reporting line
  "layer_8_file_id" TEXT, --- GID colleague positioned at layer 8 in colleague's reporting line
  "layer_9_file_id" TEXT, --- GID colleague positioned at layer 9 in colleague's reporting line 
  "layer_10_file_id" TEXT, --- GID colleague positioned at layer 10 in colleague's reporting line
  "layer_11_file_id" TEXT, --- GID colleague positioned at layer 11 in colleague's reporting line
  "layer_12_file_id" TEXT, --- GID colleague positioned at layer 12 in colleague's reporting line 
  "layer_13_file_id" TEXT, --- GID colleague positioned at layer 13 in colleague's reporting line
  "colleague_layer" REAL, --- layer of colleague in organisational structure
  "line_manager_grade" TEXT, --- colleague's line manager's grade
  "line_manager_business_title" TEXT --- colleague's line manager's job title
);
CREATE TABLE "art" (
"resource_id" TEXT,  --- Colleague's GID, the unique number assigned to each colleague. WARNING: This field contains duplicates with the top 5 most frequent values being:  99067269, 98414660, 97710479, 97563946, and 97343750. Avoid using as a primary key. 
  "full_name" TEXT, --- Colleague's first and last names
  "group" TEXT, --- The area of the group the colleague is part of 
  "start_date" TEXT, --- The date the employee started working for the group
  "compliance_program" TEXT, --- Name of the training compliance program. Should be limited to 'Q3 2024 - ART' (112648 records) and 'Q2 2024 - ART' (172814 records). WARNING: This column contains inconsistent values. 
  "course_name" TEXT, --- The individual course name in the program 
  "course_completion_date" TEXT, --- The date the course was completed. WARNING: There are data quality issues where the course completion date is later than the art due date.
  "art_due_date" TEXT, --- The date the compliance program is due by 
  "course_completion_status" TEXT, --- The registration or completion status for the course. It has possible values of  'not registered' (71375 records), 'completed' (204886 records), and 'optional' (9201 records). WARNING: This column contains inconsistent values.
  "final_art_status" TEXT, --- Indicator if the program has been completed. Possible values include:  'Completed' (199970 records), 'Not Started' (63894 records), 'In Progres' (6025 records), 'Not started' (63894 records), 'Known Exception' (5654 records), 'Overdue' (5253 records), and 'Completed late' (4666 records).
  "wd_file_date" TEXT, --- Workday file date of report extraction
  "run_date" TEXT --- The date on which the report was generated
);

CREATE TABLE "holiday_balance" (
  "colleague_id" TEXT PRIMARY KEY,  --- Colleague's unique identifier. Each ID represents a snapshot of their holiday balance on the report date. Note: Multiple entries for the same colleague ID on a single report date indicate potential data duplication and require further investigation.
  "report_date" DATE,  --- The date when the holiday balance snapshot was taken. This field is crucial for time-series analysis. Note: Currently, there is only one distinct report date ('2024-07-22') in the dataset, indicating a potential limitation for historical analysis.
  "carried_forward" REAL,  --- The number of holiday hours carried over from the previous year, contributing to the colleague's total holiday entitlement for the current year.
  "accrued" REAL,  --- The number of holiday hours accrued by the colleague in the current year, up to the report date.
  "entitlement" REAL,  --- The total holiday entitlement for the year, encompassing any additional days purchased or carried forward. This represents the maximum number of holiday hours a colleague is entitled to take for the year. Note: No colleague has taken more holiday than their entitlement.
  "booked" REAL,  --- The total number of holiday hours booked, including both hours that have been taken and those yet to be taken. 
  "taken" REAL,  --- The number of holiday hours already taken by the colleague.
  "booked_not_yet_taken" REAL,  --- The number of holiday hours booked but not yet taken. This represents the holiday hours committed to but not yet utilized. 
  "unbooked" REAL,  --- The remaining holiday hours available for the colleague to book, calculated as "entitlement" - "booked".
  "untaken" REAL,  --- The total holiday hours the colleague still has available, including "booked_not_yet_taken" and "unbooked" hours.
  "using_workday" INTEGER,  --- A flag indicating whether the colleague has booked any holiday in the Workday system. A value of 1 signifies that at least one holiday booking was made through Workday. It's essential to note that this field doesn't reflect the total number of hours booked through Workday, only the presence or absence of such bookings. For a comprehensive understanding of holiday booked outside Workday, refer to "hours_not_using_workday".
  "hours_not_using_workday" REAL,  --- The number of holiday hours not booked through the Workday system. This field warrants further analysis to determine the reasons behind booking holidays outside the designated system and identify any potential limitations or data discrepancies. Further investigation is needed to understand why some colleagues book holidays outside of the Workday system and whether this data is consistently captured.
  "Unbooked_ex_nuw" REAL  --- Represents the remaining holiday hours available for booking, excluding any hours not booked in the Workday system ("hours_not_using_workday"). This field offers a more conservative estimate of available holiday hours by considering only those booked within the Workday system, providing a more accurate reflection of manageable holiday balances. 
);
CREATE TABLE "holiday_details" (
  "colleague_id" TEXT NOT NULL,  -- Colleague's unique identifier. This is a foreign key that should link to the 'colleague' table. This ID is consistent across related tables and is crucial for linking holiday data to specific colleagues. No null values are allowed in this column.
  "hours" REAL,  -- Total holiday hours booked by the colleague. Values can be positive or negative. Negative values indicate a cancellation of the holiday. 
  "date" TEXT,  -- The date for which holiday hours were booked (YYYY-MM-DD). The data in this column ranges from 2024-01-01 to 2024-12-31.
  "entered_on" TEXT,  -- The date when the holiday was recorded in the system (YYYY-MM-DD). It's crucial to ensure this date is not later than the holiday 'date'. Data entry errors have been observed where this date is later than the holiday date.
  "report_date" TEXT,  -- snapshot date of the data (YYYY-MM-DD). Currently, the table contains data only for 2024-07-22
  "taken_tf" INTEGER  -- Count of holiday days taken by the colleague. Can be greater than holiday hours, indicating potential data discrepancies that require investigation.
);
"""

class UserInteraction:
    @staticmethod
    def should_act_on_assumptions() -> bool:
        choice = input("Do you want to act on assumption? (yes/no): ").strip().lower()
        return choice == 'yes'

    @staticmethod
    def get_user_choice(description, options):
        print(f"\n{description}")
        for option in options:
            print(f"{option['number']}. {option['description']}")
        print("custom")  # Self-declare option
        print("skip")  # Skip option
        
        while True:
            choice = input("Please choose an option (number), 'custom' to declare your own response, or type 'skip': ")
            if choice.lower() == 'skip':
                return None, None
            elif choice.lower() == 'custom':
                # When "Self" is chosen, prompt the user for a custom response
                custom_response = input("Please enter your custom response: ").strip()
                return None, custom_response
            try:
                choice = int(choice)
                if any(option['number'] == choice for option in options):
                    follow_up_response = None
                    for option in options:
                        if option['number'] == choice and option['follow_up']:
                            follow_up_response = input(f"{option['follow_up']} ")
                    return choice, follow_up_response
            except ValueError:
                pass
            print("Invalid choice. Please try again.")

    @staticmethod
    def collect_user_choices(data):
        # Collect user choices
        user_choices = {'assumptions': [], 'ambiguities': [], 'edge_cases': []}
        
        # Iterate over each category and get user choices
        for category in ['assumptions', 'ambiguities', 'edge_cases']:
            for item in data[category]:
                choice, follow_up_response = UserInteraction.get_user_choice(item['description'], item['options'])
                chosen_option = next((option for option in item['options'] if option['number'] == choice), None)
                
                # Add the user choice to the results
                user_choices[category].append({
                    'consideration_description': item['description'],
                    'option_description': chosen_option['description'] if chosen_option else None,
                    'follow_up_question': chosen_option['follow_up'] if chosen_option else None,
                    'follow_up_response': follow_up_response
                })
        return user_choices

    @staticmethod
    def format_assumptions(data):
        def print_section(title, items):
            print(f"{title}:")
            for item in items:
                print(f"  - {item['description']}")
            print()

        print_section("Assumptions", data.get("assumptions", []))
        print_section("Ambiguities", data.get("ambiguities", []))
        print_section("Edge Cases", data.get("edge_cases", []))
        
    @staticmethod
    def filter_user_choices(user_choices):
        """
        Filters the user choices and returns them as a multiline string, with each line ending with '\n'.
        - Removes `consideration_description` if the user responds with 'Skip' or if there is a follow-up question and response.
        - Includes both follow-up question and response on the same line if provided.
        """
        filtered_choices = []

        for category in ['assumptions', 'ambiguities', 'edge_cases']:
            for choice in user_choices[category]:
                # If the user skipped the choice, don't include it in the final result
                if choice['follow_up_question'] is None and choice['follow_up_response'] is None and choice['option_description'] is None:
                    continue 
                
                filtered_choice = []

                # If the user skipped the option or there is a follow-up question/response, skip the consideration_description
                if choice['follow_up_question'] and choice['follow_up_response']:
                    # Only include the follow-up question and response on the same line
                    filtered_choice.append(f"- {choice['follow_up_question']} - {choice['follow_up_response']}")
                elif choice['option_description']:
                    # If no follow-up, include just the option description
                    filtered_choice.append(f"- {choice['option_description']}")
                elif choice['follow_up_response']:
                    # If "custom" was chosen and a custom response was provided, include that response
                    filtered_choice.append(f"- {choice['consideration_description']}: {choice['follow_up_response']}")

                if filtered_choice:
                    filtered_choices.append('\n'.join(filtered_choice) + '\n')

        return ''.join(filtered_choices)

#SQL executor class

class SQLRunnerClient:
    def __init__(self, sql_runner_url):
        self.sql_runner_url = sql_runner_url

    def execute_sql(self, sql_query):
        # get google auth token to use cloud run function
        auth_req = google_requests.Request()
        id_token_value = id_token.fetch_id_token(auth_req, self.sql_runner_url)

        response = requests.post(
                self.sql_runner_url,
                json={"query": sql_query},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {id_token_value}"
                }
            )

        if response.status_code == 200:
            return response.json(), None
        else:
            # can return error codes: 400, 402, 405, 500
            return response.text, response.status_code
        
    def query_cleaner(self, query: str) -> str:
        # interprets and removes escape characters
        query = query.encode('utf-8').decode('unicode_escape')
        # convert double quoted string literals to single quotes
        # match patterns like string_literals that are not identifiers
        query = re.sub(r'"([^"]*?)"', lambda m: f"'{m.group(1)}'" if not m.group(1).isidentifier() else m.group(0), query)
        
        # TODO: replace in near future to make more robust
        query = query.replace('"', "'")

        return query

    def error_parse(self, error_text):
        try:

            # Parse the outer JSON string
            error_dict = json.loads(error_text)
            # Extract the inner JSON string and replace single quotes with double quotes
            inner_error_json = error_dict['error']
            inner_error_json = inner_error_json.replace("'", "temp_single_quote")
            inner_error_json = inner_error_json.replace('"', "'")
            inner_error_json = inner_error_json.replace("temp_single_quote", '"')

            # Parse the inner JSON string
            inner_error_dict = json.loads(inner_error_json)
 
            # Extract the message and hint
            message = inner_error_dict['M']
            hint = inner_error_dict.get('H', '')  # Use .get() to avoid KeyError if 'H' is not present
            error_message = f"Error message: {message}. {hint}"
            return error_message
 
        except Exception as e:
            return str(e)

sql_client = SQLRunnerClient("https://sql-executor-205675408770.europe-west2.run.app")

# zero shot
def generate_sql(model, table_schema: str, user_question:str) -> SQLGenerationOutput:
    prompt = f"""/*Given the following database schema: */\n{table_schema}\n/* 
    Answer the following: {user_question}

    Ensure that you think from first principles, and don't forget to ensure your (PostgreSQL) SQL code is on one line, 
    and to include the semi-colon at the end of your SQL code! 
    Also please prefer to use ILIKE over strict equal signs!*/\n\n
    The sql code that best answers the question: {user_question} is the following sql statement:\n\n
    I will tip you $50 if the answer is good!
    """

    response = client.chat.completions.create(
    messages=[
        {
            "role":"user",
            "content":prompt,
        }
    ],
    response_model=SQLGenerationOutput,
    generation_config={
        "temperature": 0,
    },
    )
    
    return response

def augment_sql(model, table_schema, user_question, user_choices, original_sql_query) -> SQLGenerationOutput:
    augmented_sql_prompt = f"""
    You are an advanced senior PostgreSQL engineer agent tasked with analysing the user question and user choices 
    to change the original sql query to better handle the new considerations brought in by the user.
    Ensure the sql query still captures broader contexts to handle any unseen edge cases

    Given the information below, generate the new PostgreSQL.
    
    User's Question: {user_question}
    database schema: {table_schema} 
    original sql query: {original_sql_query}
    I have collected the following additional considerations {user_choices}.
    
    This JSON object contains further considerations about the question including the 
    `consideration_description`, the `option_description` the user has chosen, and any follow-up 
    questions and user responses about these considerations.

    Use the original sql query to guide you or build off the original sql query,
    Account for additional considerations by altering the original sql query but keep it generalised
    Only alter the original sql query if needed otherwise keep it the same with minor changes if neccesary
    don't forget to ensure your PostgreSQL code is on one line, 
    use of wildcards instead of exact matching and use pattern matching instead of exact matching for every query,
    and to include the semi-colon 
    at the end of your SQL code! */
    
    I will tip you $50 if the answer is very good
    
    **Output Format**:
    Respond only in JSON format with the following fields:
    - `"sql_query"`: The augmented SQL query that incorporates the user choices and handles edge cases.
    - `"sql_explanation"`: A concise explanation of how and why the SQL query was updated.

    **Example Output**:
    {{
        "sql_query": "SELECT * FROM people;",
        "sql_explanation": "Explanation of each part of the sql query and what it does. Explain difference between original query and augmented"
    }}
    """
    
    # Log token size of the prompt
    encoding = tiktoken.encoding_for_model("gpt-4")  
    token_size = len(encoding.encode(augmented_sql_prompt))
    print(f"Estimated token size of the prompt: {token_size}")

    # Send the prompt to the LLM
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": augmented_sql_prompt}
        ],
        response_model=SQLGenerationOutput,
        generation_config={"temperature": 0},
    )
    return response

def generate_analytics(model, user_question, sql_query, sql_explanation, sql_results):
    analytics_prompt = f"""
    You are a 140 IQ top performing senior data engineer and analyst.
    Given the following question: {user_question}
    You have come up with the SQL code to answer it: {sql_query}
    You did this because of the following reason: {sql_explanation}
    The result of this was: {sql_results}
    Provided with this, please answer the user's request to the best of your ability with the work you have done so far. I will tip you $50 if the answer is good!
    """

    # Generate the analytical response
    analytical_response = model.generate_content(analytics_prompt).text
    return analytical_response
    
def generate_assumptions(model, user_question, table_schema, validation_results):
    # Allows users to refine assumptions, handle ambiguities, address edge cases, uses feedback to augment SQL generation
    assumptions_prompt=f"""
       You are an advanced reasoning agent tasked with analysing the user questions to ensure the SQL queries account for broader contexts, edge cases and ambiguities.
       Your goal is to generate considerations to guide the SQL generation to handle broader contexts, edge cases and ambiguities.
       Given the information below, answer the user question by following these steps.
       User's Question: {user_question}
       Database Schema: {table_schema}
       Validation Results: {validation_results}
       Follow these steps to create a detailed interpretation:
       1. **Assumptions**: List any assumptions you are making to interpret the query logical or syntactic.
                           Identify points requiring clarifications or additional context from the user to ensure accurate query construction.      
       2. **Ambiguities**: Identify any ambiguities or unclear aspects of the question. This will be used for making questions later
       3. **Potential Edge Cases**: Consider any edge cases that might affect query accuracy such as handling syntactic complications or logical complications
       Output your analysis as a json object with the following fields: `assumptions`, `ambiguities`, `edge_cases` containing considerations for each field to augment the sql question.
       Each consideration will be an object containing a `description` and an `options` array (option of how to handle the consideration). The option array will contain `number`, `description` and if the option needs further clarification, `follow_up` questions. If there are no further clarrifications needed, make `follow_up` null.

       Ensure these interpretations are broad enough to guide an initial SQL query without losing essential details. If this response is precise, I will tip you $50.

    """

    response = model.generate_content(assumptions_prompt).text
    

    return json.loads(response.replace("```json", "").replace("```", "").strip())

def validate_results(user_question, table_schema, user_choices, augmented_sql_query, augmented_sql_result_data):
    # Define the validation prompt
    validation_prompt = f"""
    You are a decision-making agent responsible for validating whether a SQL query and its results fully answer a user's question and assumptions. Provide a detailed but concise explanation of the validation results. Your output must strictly follow the JSON format specified below.

    **Inputs**:
    - User Question: {user_question}
    - Generated SQL Query: {augmented_sql_query}
    - SQL Results: {augmented_sql_result_data}
    - User Assumptions and Interpretations: {json.dumps(user_choices)}
    - Database Schema: {json.dumps(table_schema)}

    **Your Task**:
    1. Analyze the SQL query results:
       - Determine if the results provide sufficient and relevant information to answer the users question and meet their assumptions.
       - If the results are empty or unexpected (e.g., weird patterns), assess whether the SQL query logic is correct and explain why such results might occur (e.g., lack of matching data).
       - Confirm that an empty result set is acceptable if the SQL query logic is sound and reflects the users question accurately.

    2. Evaluate the SQL query:
       - Identify missing or redundant conditions in the SQL query that might cause incomplete, overly general, or irrelevant results.
       - Check if the query uses appropriate conditional statements (e.g., WHERE, JOIN conditions).
       - Suggest the use of wildcard characters or adjustments to generalize or narrow the query if required.

    3. Suggest improvements:
       - If the results are incomplete, specify what additional information, conditions, or filters should be added to the SQL query.
       - If the results are overly generalized, recommend conditional statements or constraints to refine the query.
       - Provide guidance on adding or removing conditions to align the SQL query with the users intent.

    4. Handle ambiguous or unclear inputs:
       - If the user question or assumptions are ambiguous, propose clarifications or additional input needed to refine the query.

    5. Output structured feedback:
       - State whether the SQL query and its results are valid and address the user question fully.
       - If validation fails, provide actionable suggestions for improving the SQL query or results.

    **Output Format**:
    Respond only in JSON format with the following fields:
    - `"validation_results"`: A detailed explanation of the validation outcome:
      - For SQL issues, describe **exactly where the SQL query fails** and why the results are incorrect.
      - For user input issues, describe **exactly what input or clarification is needed**.
    - `"validation_bool"`: `True` if the SQL query and results fully answer the user's question and assumptions. Use validation results to make this decision. Otherwise, `False`.
    - `"agent_error_bool"`: 
      - `True` if the failure is due to an agent error (e.g., SQL query logic issue).
      - `False` if the failure is due to incomplete or ambiguous user input.
      - If validation passes, always return `False`.
      
    **Example output**:
    {{
        "validation_results": "A detailed explanation of the validation outcome.",
        "validation_bool": `True`  or `False` bool,
        "agent_error_bool": `True`  or `False` bool"
    }}
    """

    # Send the validation prompt to the LLM or AI service
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": validation_prompt}],
        response_model=ValidationOutput,  # Assuming this is a model for the response
        generation_config={"temperature": 0},
    )

    # Return the validation response
    return response

def display_results(result_data, title):
    df = pd.DataFrame(result_data)
    print(f"\n{title}:")
    print(df)

def validate_results(user_question, table_schema, user_choices, augmented_sql_query, augmented_sql_result_data):
    # Define the validation prompt
    validation_prompt = f"""
    You are a decision-making agent responsible for validating whether a SQL query and its results fully answer a user's question and assumptions. Provide a detailed but concise explanation of the validation results. Your output must strictly follow the JSON format specified below.

    **Inputs**:
    - User Question: {user_question}
    - Generated SQL Query: {augmented_sql_query}
    - SQL Results: {augmented_sql_result_data}
    - User Assumptions and Interpretations: {json.dumps(user_choices)}
    - Database Schema: {json.dumps(table_schema)}

    **Your Task**:
    1. Analyze the SQL query results:
       - Determine if the results provide sufficient and relevant information to answer the users question and meet their assumptions.
       - If the results are empty or unexpected (e.g., weird patterns), assess whether the SQL query logic is correct and explain why such results might occur (e.g., lack of matching data).
       - Confirm that an empty result set is acceptable if the SQL query logic is sound and reflects the users question accurately.

    2. Evaluate the SQL query:
       - Identify missing or redundant conditions in the SQL query that might cause incomplete, overly general, or irrelevant results.
       - Check if the query uses appropriate conditional statements (e.g., WHERE, JOIN conditions).

    3. Suggest improvements:
       - If the results are incomplete, specify what additional information, conditions, or filters should be added to the SQL query.
       - If the results are overly generalized, recommend conditional statements or constraints to refine the query.
       - Provide guidance on adding or removing conditions to align the SQL query with the users intent.

    4. Handle ambiguous or unclear inputs:
       - If the user question or assumptions are ambiguous, propose clarifications or additional input needed to refine the query.

    5. Output structured feedback:
       - State whether the SQL query and its results are valid and address the user question fully.
       - If validation fails, provide actionable suggestions for improving the SQL query or results.

    **Output Format**:
    Respond only in JSON format with the following fields:
    - `"validation_results"`: A detailed explanation of the validation outcome:
      - For SQL issues, describe **exactly where the SQL query fails** and why the results are incorrect.
      - For user input issues, describe **exactly what input or clarification is needed**.
    - `"validation_bool"`: Always return True
    - `"agent_error_bool"`: 
      - `True` if the failure is due to an agent error (e.g., SQL query logic issue).
      - `False` if the failure is due to incomplete or ambiguous user input.
      
    **Example output**:
    {{
        "validation_results": "A detailed explanation of the validation outcome.",
        "validation_bool": `True` or `False` bool,
        "agent_error_bool": `True` or `False` bool"
    }}
    """

    # Send the validation prompt to the LLM or AI service
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": validation_prompt}],
        response_model=ValidationOutput,  # Assuming this is a model for the response
        generation_config={"temperature": 0},
    )

    # Return the validation response
    return response

import concurrent.futures

def run_pipeline(project_id, sql_runner_url, table_schema, user_question, max_retries=3):
    model = initialise_vertex_ai(project_id)
    sql_client = SQLRunnerClient(sql_runner_url)
    retry_count = 0

    while retry_count < max_retries:  # SQL generation loop
        try:
            # Step 1: Generate initial SQL asynchronously and assumptions concurrently
            print(f"SQL Generation Attempt {retry_count + 1}...\n")

            # Using ThreadPoolExecutor to handle both tasks in parallel
            with concurrent.futures.ThreadPoolExecutor() as executor:
                sql_future = executor.submit(generate_sql, model, table_schema, user_question)
                assumptions_future = executor.submit(generate_assumptions, model, user_question, table_schema, "")

                # Wait for both tasks to complete
                sql_generation_response = sql_future.result()
                assumptions = assumptions_future.result()

            print(f"Generated SQL Query:\n{sql_generation_response.sql_query}\n")
            print(f"SQL Explanation:\n{sql_generation_response.sql_explanation}\n")

            # Step 2: Clean the SQL Query
            cleaned_query = sql_client.query_cleaner(sql_generation_response.sql_query)
            print(f"Cleaned SQL Query:\n{cleaned_query}\n")

            # Step 3: Execute the SQL Query
            sql_result, error = sql_client.execute_sql(cleaned_query)

            if error:
                print(f"SQL Execution Error: {error}. Regenerating SQL...\n")
                retry_count += 1
                continue  # Restart the loop for a new SQL generation

            # Step 4: Handle successful execution
            try:
                sql_result_data = sql_result["data"]
                display_results(sql_result_data, "First SQL Generation Result")
            except Exception as e:
                sql_result_data = sql_result
                print(f"No SQL result, error: {e}")

            # Step 5: Generate Analytics
            analytic_response = generate_analytics(
                model, user_question, cleaned_query, sql_generation_response.sql_explanation, sql_result_data
            )
            print(f"\nAnalytical Response: {analytic_response}\n")

            # Step 6: Validation and Augmentation
            validation_results = ""
            sql_query = cleaned_query
            sql_result = sql_result_data
            sql_explanation = sql_generation_response.sql_explanation
            agent_error = False
            filtered_choices = []  # Placeholder to ensure filtered_choices always exists

            augment_retry_count = 0  # Retry counter for augmenting SQL
            while True:  # Validation loop
                if not agent_error:  # Process assumptions only if agent error is NOT the issue
                    UserInteraction.format_assumptions(assumptions)

                    if not UserInteraction.should_act_on_assumptions():
                        break

                    user_choices = UserInteraction.collect_user_choices(assumptions)
                    filtered_choices = UserInteraction.filter_user_choices(user_choices)
                    print(f"\nFiltered Choices:\n{filtered_choices}\n")

                # Retry loop for augment SQL in case of execution error
                while augment_retry_count < 3:  # Allow up to 3 retries for augmenting SQL
                    augmented_sql_query = augment_sql(model, table_schema, user_question, filtered_choices, sql_query)
                    cleaned_augmented_sql_query = sql_client.query_cleaner(augmented_sql_query.sql_query)
                    print(f"\nCleaned Augmented SQL Query:\n{cleaned_augmented_sql_query}\n")
                    print(f"Augmented SQL Explanation:\n{augmented_sql_query.sql_explanation}")

                    augmented_sql_results, error = sql_client.execute_sql(cleaned_augmented_sql_query)

                    if error:
                        print(f"SQL Execution Error: {error}. Retrying augment SQL ({augment_retry_count + 1}/3)...\n")
                        augment_retry_count += 1
                    else:
                        print(f"Augmented SQL Results:\n{augmented_sql_results}")
                        augmented_sql_result_data = augmented_sql_results["data"]
                        display_results(augmented_sql_result_data, "Augmented SQL Generation Results")
                        break  # Exit retry loop if SQL execution is successful

                # Exit the validation loop if augment SQL exceeds max retries
                if augment_retry_count >= 3:
                    print("Max retries reached for augment SQL. Exiting validation loop...")
                    break

                # Validate results if augment SQL succeeds
                validation_response = validate_results(
                    user_question, table_schema, filtered_choices, augmented_sql_query, augmented_sql_result_data
                )
                print(validation_response.validation_bool)
                print(f"\nValidation {'Passed' if validation_response.validation_bool else 'Failed'}")
                print(f"Validation Response:\n{validation_response.validation_results}")
                validation_results = validation_response.validation_results
                agent_error = validation_response.agent_error_bool

                if validation_response.validation_bool:
                    sql_query = augmented_sql_query
                    sql_result = augmented_sql_result_data
                    sql_explanation = augmented_sql_query.sql_explanation
                    break

            # Step 7: Final Analytics
            final_analytic_response = generate_analytics(model, user_question, sql_query, sql_explanation, sql_result)
            print(f"\nFinal Analytical Response: {final_analytic_response}\n")
            return  # Exit the pipeline after successful execution and validation

        except Exception as e:
            print(f"Unexpected Error: {e}. Regenerating SQL...\n")
            retry_count += 1

    print(f"Pipeline failed after {max_retries} attempts.")

# Main runner
if __name__ == "__main__":
    PROJECT_ID="prj-lbg-dialogwithdata-270624"
    SQL_RUNNER_URL = "https://sql-executor-205675408770.europe-west2.run.app"
    TABLE_SCHEMA = table_schema
    USER_QUESTION = "can you share the null records id for onshore vs offshore"
    run_pipeline(PROJECT_ID, SQL_RUNNER_URL, TABLE_SCHEMA, USER_QUESTION) 
