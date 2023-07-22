"""
Загружаем три локации с наибольшим количеством резидентов из API Рика и Морти
"""

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.dummy import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from plugins.s_aliev_rick_and_morty import SamirRamOperator


DEFAULT_ARGS = {
    'start_date': days_ago(2),
    'owner': 's-aliev',
    'poke_interval': 600
}

with DAG(
    dag_id='ram_locations',
    schedule_interval='@daily',
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    tags=['s-aliev']
) as dag:
    start = DummyOperator(task_id='start')

    create = PostgresOperator(
        task_id='create',
        postgres_conn_id='conn_greenplum_write',
        sql='''
            CREATE TABLE IF NOT EXISTS s_aliev_ram_location (
                        id text NOT NULL,
                        name text NOT NULL,
                        "type" text NOT NULL,
                        dimension text NOT NULL,
                        resident_cnt text NOT NULL);
            '''
    )

    clear = PostgresOperator(
        task_id='clear',
        postgres_conn_id='conn_greenplum_write',
        sql='TRUNCATE TABLE s_aliev_ram_location'
    )

    get_top3_locs = SamirRamOperator(
        task_id='get_top3_locs',
        locs_count=3,
    )

    start >> create >> clear >> get_top3_locs
