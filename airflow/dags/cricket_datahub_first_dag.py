import pendulum

from airflow.sdk import dag, task

@dag(
    schedule=None,
    start_date=pendulum.datetime(2026,10,5,tz="UTC"),
    catchup=False,
    tags=["cricket_datahub","learning"],
)
def cricket_datahub_first_dag():
    """ 
    First DAG for the Cricket DataHub project.

    The DAG demonstrates the basic Airflow workflow structure:
    Start->Process->Finish
    """

    @task
    def start_pipeline():
       print("Cricket DataHub Pipeline Started.")

    @task
    def process_data():
        print("processing cricket data...")

    @task
    def finish_pipeline():
        print("Cricket DataHub Pipeline Finished.") 

    start=start_pipeline()
    process=process_data()
    finish=finish_pipeline()

    start >> process >> finish

cricket_datahub_first_dag()