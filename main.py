import os
import smtplib
import pandas as pd
import schedule
import time
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables securely
load_dotenv()

# Configuration
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# File Paths
CONTACTS_FILE = "data/contacts.csv"
LOG_FILE = "logs/email_report.csv"

# SET TO TRUE FOR TESTING WITHOUT SENDING REAL EMAILS
DRY_RUN = True 

def log_status(name, email, status, error_msg=""):
    """Logs the success or failure of an email attempt to a CSV."""
    log_entry = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Email": email,
        "Status": status,
        "Error": error_msg
    }])
    
    file_exists = os.path.isfile(LOG_FILE)
    log_entry.to_csv(LOG_FILE, mode='a', index=False, header=not file_exists)

def process_and_send_emails(keyword, email_subject):
    """Dynamically loads a template and ONLY sends emails if the DueDate is TODAY."""
    
    # Get today's date in YYYY-MM-DD format (matches our CSV format)
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting '{keyword}' batch process for Date: {today_date}...")
    
    template_filepath = f"templates/{keyword}.txt"
    
    if not os.path.exists(template_filepath):
        print(f"\n[ERROR] Could not find template file: {template_filepath}")
        return

    with open(template_filepath, 'r', encoding='utf-8') as file:
        body_template = file.read()

    try:
        contacts = pd.read_csv(CONTACTS_FILE)
        contacts = contacts.fillna("Not Provided") 

        server = None
        if not DRY_RUN:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Counter to track how many emails were actually sent today
        emails_sent_today = 0

        for index, row in contacts.iterrows():
            
            # SMART FILTER: Check if the row's DueDate matches Today's Date
            if str(row['DueDate']).strip() != today_date:
                print(f"[SKIPPED] {row['Name']} - Deadline is {row['DueDate']}, not today.")
                continue # Skips to the next person in the loop

            row_dict = row.to_dict()
            
            try:
                personalized_body = body_template.format(**row_dict)
            except KeyError as e:
                print(f"[ERROR] Skipping {row['Name']}. Template missing {e}.")
                continue

            msg = EmailMessage()
            msg['Subject'] = email_subject
            msg['From'] = SENDER_EMAIL
            msg['To'] = row['Email']
            msg.set_content(personalized_body)

            if DRY_RUN:
                print(f"\n[DRY RUN] MATCH FOUND! Would send to: {row['Email']}")
                print(f"--- Preview ---\n{personalized_body}\n---------------")
                log_status(row['Name'], row['Email'], f"Dry Run Success ({keyword})")
                emails_sent_today += 1
            else:
                try:
                    server.send_message(msg)
                    print(f"[SUCCESS] Email sent to: {row['Email']}")
                    log_status(row['Name'], row['Email'], f"Success ({keyword})")
                    emails_sent_today += 1
                except Exception as e:
                    print(f"[FAILED] Could not send to {row['Email']}: {e}")
                    log_status(row['Name'], row['Email'], f"Failed ({keyword})", str(e))

        if server:
            server.quit()
            
        print(f"\nBatch complete. Total '{keyword}' emails sent today: {emails_sent_today}")

    except Exception as main_e:
        print(f"Critical Error during execution: {main_e}")
        
        
if __name__ == "__main__":
    print("=========================================")
    print("  📧 DYNAMIC EMAIL AUTOMATION ENGINE     ")
    print("=========================================")
    
    # Ask user for the scenario (this decides which file opens)
    user_keyword = input("\nEnter the email type (e.g., money, book, meeting): ").strip().lower()
    
    # Ask user for the email subject line
    user_subject = input("Enter the subject line for this batch: ")
    
    # Run the program
    process_and_send_emails(user_keyword, user_subject)