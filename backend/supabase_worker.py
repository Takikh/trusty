import time
from main_supabase import fetch_pending_doctor, run_supabase_pipeline
from evaluate_supabase import fetch_interview_done_doctor, run_evaluation_worker

def run_worker_loop():
    print("============================================================")
    print(" 🚀 SUPABASE AI AUTONOMOUS BACKEND WORKER STARTED ")
    print("============================================================")
    print("Listening for jobs on Supabase... (Press Ctrl+C to stop)\n")
    
    while True:
        try:
            # 1. Check for new pending documents
            pending = fetch_pending_doctor()
            if pending:
                print(f"\n[WORKER] Picked up new document extraction job for {pending['name']}...")
                run_supabase_pipeline()
                print("\nListening for jobs on Supabase...")
                
            # 2. Check for completed interviews needing evaluation
            to_evaluate = fetch_interview_done_doctor()
            if to_evaluate:
                print(f"\n[WORKER] Picked up new evaluation job for {to_evaluate['name']}...")
                run_evaluation_worker()
                print("\nListening for jobs on Supabase...")
                
            # 3. Sleep briefly to avoid spamming the API
            time.sleep(5)
            
        except Exception as e:
            print(f"\n[!] Worker Error: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    run_worker_loop()
