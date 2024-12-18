import sqlite3

# Schema definition (provided in your question)
schema = r"""
CREATE TABLE "people" (
  "resource_id" TEXT PRIMARY KEY, 
  "full_name" TEXT, 
  "email" TEXT, 
  "first_name" TEXT,
  "last_name" TEXT, 
  "direct_line_manager_id" TEXT, 
  "direct_line_manager_name" TEXT, 
  "line_manager_email" TEXT, 
  "location_name" TEXT, 
  "data_source" TEXT, 
  "hub_location" TEXT, 
  "is_onshore" TEXT, 
  "fte" REAL, 
  "scheduled_working_hours" REAL, 
  "grade" TEXT, 
  "job_title" TEXT, 
  "job_code" TEXT, 
  "business_title" TEXT, 
  "cost_centre_id" TEXT, 
  "agency" TEXT, 
  "original_tenure_start" TEXT, 
  "current_start_date" TEXT, 
  "leave_date" TEXT, 
  "contractor_day_rate_banding" TEXT, 
  "on_leave" TEXT, 
  "job_family" TEXT, 
  "worker_type" TEXT, 
  "high_lev_workertype" TEXT, 
  "funding_source" TEXT, 
  "division" TEXT, 
  "cc_layer_1" TEXT, 
  "cc_layer_2" TEXT, 
  "cc_layer_3" TEXT, 
  "cc_layer_4" TEXT, 
  "is_manager" TEXT, 
  "post_code" TEXT, 
  "city" TEXT, 
  "location_id" REAL, 
  "position_id" TEXT, 
  "workday_job_family_group" TEXT, 
  "workday_job_category" TEXT, 
  "compensation_grade_profile" TEXT, 
  "oim_learner" TEXT, 
  "workday_learner" TEXT, 
  "learner_type" TEXT, 
  "layer_2" TEXT, 
  "layer_3" TEXT, 
  "layer_4" TEXT, 
  "layer_5" TEXT, 
  "layer_6" TEXT, 
  "layer_7" TEXT, 
  "layer_8" TEXT, 
  "layer_9" TEXT, 
  "layer_10" TEXT, 
  "layer_11" TEXT, 
  "layer_12" TEXT, 
  "layer_13" TEXT, 
  "layer_2_file_id" TEXT, 
  "layer_3_file_id" TEXT, 
  "layer_4_file_id" TEXT, 
  "layer_5_file_id" TEXT, 
  "layer_6_file_id" TEXT, 
  "layer_7_file_id" TEXT, 
  "layer_8_file_id" TEXT, 
  "layer_9_file_id" TEXT, 
  "layer_10_file_id" TEXT, 
  "layer_11_file_id" TEXT, 
  "layer_12_file_id" TEXT, 
  "layer_13_file_id" TEXT, 
  "colleague_layer" REAL, 
  "line_manager_grade" TEXT, 
  "line_manager_business_title" TEXT
);

CREATE TABLE "art" (
  "resource_id" TEXT,  
  "full_name" TEXT, 
  "group" TEXT, 
  "start_date" TEXT, 
  "compliance_program" TEXT, 
  "course_name" TEXT, 
  "course_completion_date" TEXT, 
  "art_due_date" TEXT, 
  "course_completion_status" TEXT, 
  "final_art_status" TEXT, 
  "wd_file_date" TEXT, 
  "run_date" TEXT
);

CREATE TABLE "holiday_balance" (
  "colleague_id" TEXT PRIMARY KEY,  
  "report_date" DATE,  
  "carried_forward" REAL,  
  "accrued" REAL,  
  "entitlement" REAL,  
  "booked" REAL,  
  "taken" REAL,  
  "booked_not_yet_taken" REAL,  
  "unbooked" REAL,  
  "untaken" REAL,  
  "using_workday" INTEGER,  
  "hours_not_using_workday" REAL,  
  "Unbooked_ex_nuw" REAL
);

CREATE TABLE "holiday_details" (
  "colleague_id" TEXT NOT NULL,  
  "hours" REAL,  
  "date" TEXT,  
  "entered_on" TEXT,  
  "report_date" TEXT,  
  "taken_tf" INTEGER
);
"""

# Function to build the database
def build_database(db_name, schema):
    # Connect to SQLite database (creates the file if it does not exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Execute the schema
        cursor.executescript(schema)
        print("Database and tables created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

# Main execution
if __name__ == "__main__":
    DATABASE_NAME = "company_data.db"  # Name of the database file
    build_database(DATABASE_NAME, schema)
