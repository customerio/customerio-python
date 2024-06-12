# Sending event data to CustomerIO from CSVs 


Let's say you have large amounts of data in CSV. And you need to process
each row, and then send data from that row to CustomerIO. 

Well, there are many ways one to do this. But we have demonstrated one way to do that
in the file `cio_event_manager.py`.

To run the code, you will need the following data:
* Site-ID and API Key from your CustomerIO workspace
* Event name
* Full CSV file path


And then run the code like this:
````
cio_event_manager = CIOEventManager(site_id, api_key, full_file_path_in_str)
cio_event_manager.event_name = 'purchase'
cio_event_manager.send_events()
````

Behind the scenes, the CSV will be read, and data will be sent to CustomerIO. To speed
up the process of sending data, parallelism is demonstrated using Python's `Multiprocessing` module. 

