# Customer.io Python bindings

This module has been tested with Python 2.6, 2.7 and 3.4

## Installing

```bash
pip install customerio
```

## Usage

```python
from customerio import CustomerIO
cio = CustomerIO(site_id, api_key)
cio.identify(id=5, email='customer@example.com', name='Bob', plan='premium')
cio.track(customer_id=5, name='purchased')
cio.track(customer_id=5, name='purchased', price=23.45)
```

### Instantiating customer.io object

```python
from customerio import CustomerIO
cio = CustomerIO(site_id, api_key)
```

### Create or update a Customer.io customer profile

```python
cio.identify(id=5, email='customer@example.com', name='Bob', plan='premium')
```

Only the id field is used to identify the customer here.  Using an existing id with
a different email (or any other attribute) will update/overwrite any pre-existing
values for that field.

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Creating_or_updating_customers)

### Track a custom event

```python
cio.track(customer_id=5, name='purchased')
```

### Track a custom event with custom data values

```python
cio.track(customer_id=5, name='purchased', price=23.45, product="widget")
```

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Track_a_custom_event)

### Backfill a custom event

```python
from datetime import datetime, timedelta

customer_id = 5
event_type = "purchase"

# Backfill an event one hour in the past
event_date = datetime.utcnow() - timedelta(hours=1)
cio.backfill(customer_id, event_type, event_date, price=23.45, coupon=True)

event_timestamp = 1408482633
cio.backfill(customer_id, event_type, event_timestamp, price=34.56)

event_timestamp = "1408482680"
cio.backfill(customer_id, event_type, event_timestamp, price=45.67)
```

Event timestamp may be passed as a ```datetime.datetime``` object, an integer or a string UNIX timestamp

Keyword arguments to backfill work the same as a call to ```cio.track```.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Track_a_custom_event)

### Delete a customer profile
```python
cio.delete(customer_id=5)
```

Deletes the customer profile for a specified customer.

This method returns nothing.  Attempts to delete non-existent customers will not raise any errors.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Deleting_customers)


You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

### Add a device
```python
cio.add_device(customer_id=1, device_id='device_hash', platform='ios')
```

Adds the device `device_hash` with the platform `ios` for a specified customer.

Supported platforms are `ios` and `android`. 

Optionally, `last_used` can be passed in to specify the last touch of the device. Otherwise, this attribute is set by the API.

```python
cio.add_device(customer_id=1, device_id='device_hash', platform='ios', last_used=1514764800})
```

This method returns nothing.

### Delete a device
```python
cio.delete_device(customer_id=1, device_id='device_hash')
```

Deletes the specified device for a specified customer.

This method returns nothing. Attempts to delete non-existent devices will not raise any errors.

### Suppress a customer
```python
cio.suppress(customer_id=1)
```

Suppresses the specified customer. They will be deleted from Customer.io, and we will ignore all further attempts to identify or track activity for the suppressed customer ID

See REST documentation [here](https://learn.customer.io/api/#apisuppress_add)

### Unsuppress a customer
```python
cio.unsuppress(customer_id=1)
```

Unsuppresses the specified customer. We will remove the supplied id from our suppression list and start accepting new identify and track calls for the customer as normal

See REST documentation [here](https://learn.customer.io/api/#apisuppress_delete)

## Running tests

Changes to the library can be tested by running `make test` from the parent directory.

## Thanks!

* [Dimitriy Narkevich](https://github.com/dimier) for creating the library.
* [EZL](https://github.com/ezl) for contributing customer deletes and improving README
* [Noemi Millman](https://github.com/sbnoemi) for adding custom JSON encoder
* [Jason Kraus](https://github.com/zbyte64) for event backfilling
* [Nicolas Paris](https://github.com/niparis) for better handling of NaN values