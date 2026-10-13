import pendulum
import subprocess
import sys
from pathlib import Path

from airflow.sdk import dag, task

PROJECT_ROOT=Path(__file__).resolve().parents[2]

@dag(
    schedule=None,
    start_date=pendulum.datetime(2026,10,5,tz="UTC"),
    catchup=False,
    tags=["cricket_datahub","learning"],
)
def cricket_datahub_first_dag():

    """
    Cricket DataHub pipeline.

    Start -> Extract, Transform and Load -> Finish
    """

    @task
    def start_pipeline():
        print("Cricket DataHub Pipeline Started.")

    @task
    def process_data():
        scripts=[
            ("Extract",PROJECT_ROOT/"data"/"extract_espn.py"),
            ("Transform and Load", PROJECT_ROOT/"data"/"load_postgres.py"),
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
                print(f"{step_name}messages:")
                print(result.stderr)
            print(f"{step_name} step completed successfully.")
    @task
    def finish_pipeline():
        print("Cricket DataHub Pipeline Finished.")

    start=start_pipeline()
    process=process_data()
    finish=finish_pipeline()

    start>>process>>finish

cricket_datahub_first_dag()