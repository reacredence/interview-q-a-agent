import schedule
import time
from batch_runner import run_batch

def job():
    print("Running scheduled batch job...")
    run_batch()

# Schedule the job every day at 09:00 AM
schedule.every().day.at("09:00").do(job)

print("Scheduler started. Waiting for next job...")
print("Press Ctrl+C to exit.")

if __name__ == "__main__":
    # For demonstration, we can uncomment the next line to run immediately on start
    # run_batch()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
