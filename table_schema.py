import re

schema = r"""CREATE TABLE "people" (
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
  "is_onshore" TEXT, --- Identifies if a colleague is based in the UK (onshore) or elsewhere (offshore)
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
  "leave_date" TEXT, --- Date that colleague is due to leave the company where known
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
  "is_manager" TEXT, --- Flag denoting whether colleague is set as a manager in Workday Manager = Yes. **Note: Discrepancies observed between "is_manager" flag and presence of direct reports. Requires further investigation on how "is_manager" is defined.**
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
  "colleague_id" TEXT NOT NULL,  --- Colleague's unique identifier. This is a foreign key that should link to the 'colleague' table. This ID is consistent across related tables and is crucial for linking holiday data to specific colleagues. No null values are allowed in this column.
  "hours" REAL,  --- Total holiday hours booked by the colleague. Values can be positive or negative. Negative values indicate a cancellation of the holiday. 
  "date" TEXT,  --- The date for which holiday hours were booked (YYYY-MM-DD). The data in this column ranges from 2024-01-01 to 2024-12-31.
  "entered_on" TEXT, --- The date when the holiday was recorded in the system (YYYY-MM-DD). It's crucial to ensure this date is not later than the holiday 'date'. Data entry errors have been observed where this date is later than the holiday date.
  "report_date" TEXT,  --- snapshot date of the data (YYYY-MM-DD). Currently, the table contains data only for 2024-07-22
  "taken_tf" INTEGER  --- A binary flag (0 or 1) indicating if the holiday hours were actually taken. This field often differs from 'hours', suggesting a significant discrepancy between booked and actual holiday taken (221087 instances). It's unclear if 'hours' represents the intended duration while 'taken_tf' reflects the actual time off. 
  );"""

# Regular expression patterns to extract tables, columns, and descriptions
table_pattern = r'CREATE TABLE "(\w+)" \((.*?)\);'
column_pattern = r'"(\w+)" \w+.*?--- (.*?)$'

# Dictionary to store table schemas
schema_dict = {}

# Find each table and its columns
tables = re.findall(table_pattern, schema, re.DOTALL)
for table, columns in tables:
    # Dictionary to store column descriptions
    column_descriptions = {}
    
    # Find each column and its description
    for column, description in re.findall(column_pattern, columns, re.MULTILINE):
        column_descriptions[column] = description.strip()
    
    # Store in main dictionary under the table name
    schema_dict[table] = column_descriptions

# Example output of dictionary contents
# for table, columns in schema_dict.items():
#     print(f"Table: {table}")
#     for column, description in columns.items():
#         print(f'  "{column}": "{description}"')
#     print()
print(schema_dict)