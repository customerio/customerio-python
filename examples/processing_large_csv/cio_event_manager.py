"""
Sample code to demonstrate sending event data to CustomerIO using large CSVs. This script uses Python3.
"""
import csv
import time
import logging
import os
from multiprocessing.pool import ThreadPool as Pool
from customerio import CustomerIO, CustomerIOException

logger = logging.getLogger(__name__)


class CIOEventManager(object):
    def __init__(self, cio_site_id, cio_api_key, csv_full_file_path):
        self.csv_full_file_path = csv_full_file_path
        self.site_id = cio_site_id
        self.api_key = cio_api_key
        self.csv_full_file_path = os.path.normpath(csv_full_file_path)
        self.cio_api_client = CustomerIO(self.site_id, self.api_key, retries=5)
        self.event_name = None

    def _read_csv(self):
        with open(self.csv_full_file_path, 'r') as csv_file:
            data = csv.DictReader(csv_file)
            for line in data:
                yield line

    def _send_data_to_cio(self, data):
        try:
            # Assume each CSV row looks like
            # {'age': '23', 'created_at': '', 'location': 'Boston', 'id': 'id: 1', 'unsubscribed': 'false'}
            self.cio_api_client.track(customer_id=data['id'], name=self.event_name)
        except CustomerIOException as e:
            # log the CSV row and exception and move to processing the next row
            logger.exception("Failed to send the row data: {row}. Error message={message}".format(row=data,
                                                                                                  message=e.message))

    def pre_process(self):
        """Use this function to do some tasks before the CSV is processed"""
        pass

    def send_events(self, no_of_processes=4):
        """
        First runs some pre-processing. Read the CSV and send data from each row to CustomerIO. Then it finally
        runs some post-processing.
        """
        self.pre_process()
        csv = self._read_csv()
        pool = Pool(processes=no_of_processes)
        for row in csv:
            pool.map(self._send_data_to_cio, (row,))
        rate_limit_in_secs = 0.03  # rate limiting 30 requests per sec (i.e. 1  / 30 = 0.03)
        time.sleep(rate_limit_in_secs)
        self._post_process()
        pool.close()
        pool.join()

    def _post_process(self):
        """Use this function to do some tasks after the CSV is processed"""
        pass
