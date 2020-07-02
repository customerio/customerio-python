"""
Sample code to demonstrate sending event data to CustomerIO using large CSVs. Created using Python3.
"""

import time
import logging
import os
from multiprocessing.pool import ThreadPool as Pool
from customerio import CustomerIO, CustomerIOException

logger = logging.getLogger(__name__)


class CIO_CSVProcessor(object):
    def __init__(self, site_id, api_key, csv_full_file_path):
        self.csv_full_file_path = csv_full_file_path
        self.site_id = site_id
        self.api_key = api_key
        self.csv_full_file_path = os.path.normpath(csv_full_file_path)
        self.cio_api_client = CustomerIO(self.site_id, self.api_key, retries=5)

    def _read_csv(self):
        with open(self.csv_full_file_path, 'r') as csv:
            for line in csv:
                yield line

    def _send_event_to_cio(self, data):
        """Assuming the CSV row has customer-id in the first column and event name is in the second column"""
        try:
            self.cio_api_client.track(customer_id=data[0], name=data[1])
        except CustomerIOException as e:
            # log the exception and move to processing the next row
            logger.exception(e.message)

    def pre_process(self):
        """Use this function to do some tasks before the CSV is processed"""
        pass

    def process(self, no_of_processes=4):
        """
        First runs some pre-processing. Read the CSV and send data from each row to CustomerIO. Then it finally
        runs some post-processing.
        """
        self.pre_process()
        csv = self._read_csv()
        pool = Pool(processes=no_of_processes)
        for row in csv:
            pool.map(self._send_event_to_cio, (row,))
        secs = 0.03  # rate limiting 30 requests per sec (i.e. 1  / 30 = 0.03)
        time.sleep(secs)
        self._post_process()
        pool.close()
        pool.join()

    def _post_process(self):
        """Use this function to do some tasks after the CSV is processed"""
        pass

