import pendulum
import subprocess
import sys
from pathlib import Path

from airflow.sdk import dag, task


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dag(
    schedule=None,
    start_date=pendulum.datetime(2026, 10, 5, tz="UTC"),
    catchup=False,
    tags=["cricket_datahub", "learning"],
)
def cricket_datahub_first_dag():

    """
    Cricket DataHub pipeline.

    Start -> Domestic Pipeline -> International Pipeline -> Finish
    """

    @task
    def start_pipeline():
        print("Cricket DataHub Pipeline Started.")

    @task
    def process_domestic_data():
        scripts = [
            ("Extract Domestic Match", PROJECT_ROOT / "data" / "extract_espn.py"),
            ("Load Domestic Match", PROJECT_ROOT / "data" / "load_postgres.py"),
        ]

        for step_name, script_path in scripts:
            print(f"Starting {step_name} step...")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(PROJECT_ROOT),
                check=True,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                print(result.stdout)

            if result.stderr:
                print(f"{step_name} messages:")
                print(result.stderr)

            print(f"{step_name} step completed successfully.")

    @task
    def process_international_data():
        script_path = PROJECT_ROOT / "data" / "load_international_match.py"

        print("Starting international match validation and load...")

        result = subprocess.run(
            [sys.executable, str(script_path), "--load"],
            cwd=str(PROJECT_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("International pipeline messages:")
            print(result.stderr)

        print("International match load completed successfully.")

    @task
    def finish_pipeline():
        print("Cricket DataHub Pipeline Finished.")

    start = start_pipeline()
    domestic = process_domestic_data()
    international = process_international_data()
    finish = finish_pipeline()

    start >> domestic >> international >> finish


cricket_datahub_first_dag()
