import csv
from datetime import datetime

def log_result(passport, assigned_center, success, proxy):
    with open("logs/activity_log.csv", mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            passport,
            assigned_center or "N/A",
            "MATCH" if success else "SKIPPED",
            proxy or "None"
        ])
