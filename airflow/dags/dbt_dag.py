from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.utils.trigger_rule import TriggerRule

# Tweak these to match your environment
DBT_CONTAINER = os.getenv("DBT_CONTAINER_NAME", "dbt_airflow_project-dbt-1")
ALERT_EMAILS = os.getenv("DBT_ALERT_EMAILS", "data-team@example.com").split(",")

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

with DAG(
    dag_id="dbt_transform",
    description="Run dbt models and data quality checks for the SQL Server warehouse",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    is_paused_upon_creation=False,
    catchup=False,
    max_active_runs=1,
    tags=["dbt", "sqlserver", "daily"],
) as dag:
    dag.doc_md = """
    ### dbt_transform
    Orchestrates the dbt pipeline:
    - Install packages, run models, then run tests/data quality checks
    - Daily schedule, single active run, with retries and exponential backoff
    - Sends an email notification if any task fails
    """

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"docker exec {DBT_CONTAINER} dbt deps",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"docker exec {DBT_CONTAINER} dbt run --fail-fast",
    )

    data_quality_checks = BashOperator(
        task_id="dbt_test",
        bash_command=f"docker exec {DBT_CONTAINER} dbt test --fail-fast --store-failures",
    )

    notify_failure = EmailOperator(
        task_id="notify_failure",
        to=ALERT_EMAILS,
        subject="Airflow alert: dbt_transform DAG failed",
        html_content=(
            "The DAG <b>dbt_transform</b> encountered a failure.<br>"
            "Please review the Airflow task logs for details."
        ),
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    dbt_deps >> dbt_run >> data_quality_checks
    [dbt_deps, dbt_run, data_quality_checks] >> notify_failure
