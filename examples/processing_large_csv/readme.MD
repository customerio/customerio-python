# Sending event data to CustomerIO from CSVs 


Let's say you have large amounts of data in CSV. And you need to process
each row, and then send data from that row to CustomerIO. 

Well, there are many ways one to do this. But we have given an 
example in this directory in a this file `cio_csv_processor.py`.

To run the code, you will need the following data:
* Site-ID and API key from your CustomerIO workspace
* Full CSV file path


And then run it like this:
````
csv_processor = CIO_CSVProcessor(site_id, api_key, full_file_path_in_str)
csv_processor.process()
````

Behind the scenes, the CSV will be opened, and data will be sent to CustomerIO. To speed
up the process of sending data, parallelism is demonstrated using Python's `Multiprocessing` module. 

