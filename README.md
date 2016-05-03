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

## Thanks

* [Dimitriy Narkevich](https://github.com/dimier) for creating the library.
* [EZL](https://github.com/ezl) for contributing customer deletes and improving README
* [Noemi Millman](https://github.com/sbnoemi) for adding custom JSON encoder
* [Jason Kraus](https://github.com/zbyte64) for event backfilling
