import logging

from airflow.models import BaseOperator
from airflow.hooks.http_hook import HttpHook
from airflow.hooks.postgres_hook import PostgresHook
import json
import requests


class SamirRickMortyHook(HttpHook):
    def __init__(self, http_conn_id: str, **kwargs) -> None:
        super().__init__(http_conn_id=http_conn_id, **kwargs)
        self.method = 'GET'

    def get_loc_page_count(self):
        return self.run('api/location').json()['info']['pages']

    def get_loc_page(self, page_num: str) -> list:
        return self.run(f'api/location?page={page_num}').json()['results']


class SamirRamOperator(BaseOperator):
    def __init__(self, locs_count: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.locations_count = locs_count

    def set_count_of_residents(self, locs: list) -> None:
        for loc in locs:
            loc['residents'] = len(loc['residents'])

    def get_top_locs(self):
        url = 'https://rickandmortyapi.com/api/location'
        r = requests.get(url)
        if r.status_code == 200:
            data = json.loads(r.text)
            locs = data['results']
            result = []
            for loc in locs:
                loc_dict = {
                    'id': loc['id'],
                    'name': loc['name'],
                    'type': loc['type'],
                    'dimension': loc['dimension'],
                    'resident_cnt': len(loc['residents'])
                }
                result.append(loc_dict)
            sorted_loc = sorted(result,
                                      key=lambda cnt: cnt['resident_cnt'],
                                      reverse=True)
            self.top3_loc = sorted_loc[:3]
        else:
            logging.warning(f"Error {r.status_code}")

    def execute(self, context):
        self.get_top_locs()

        pg_hook = PostgresHook(postgres_conn_id='conn_greenplum_write')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        data = []
        for loc in self.top3_loc:
            insert_values = f"({loc['id']}, '{loc['name']}', '{loc['type']}', '{loc['dimension']}', {loc['resident_cnt']})"
            data.append(insert_values)

        cursor.execute(f"INSERT INTO s_aliev_ram_location VALUES {','.join(data)}")
        logging.info(f"Top location in Rick&Morty is {data}")
        conn.commit()
        conn.close()
