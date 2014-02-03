# Customer.io Python bindings

This module has been tested with Python 2.7.

## Installing

    pip install customerio

## Usage

### Instantiating customer.io object

	from customerio import CustomerIO
	cio = CustomerIO(site_id, api_key)

### Create or update a Customer.io customer profile

	cio.identify(id=5, email='customer@example.com', name='Bob', plan='premium')

Only the id field is used to identify the customer here.  Using an existing id with
a different email (or any other attribute) will update/overwrite any pre-existing
values for that field.

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Creating_or_updating_customers)

### Track a custom event

	cio.track(customer_id=5, name='purchased')
	cio.track(customer_id=5, name='purchased', price=23.45)

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Track_a_custom_event)

### Delete a customer profile

	cio.delete(customer_id=5)

Deletes the customer profile for a specified customer.

This method returns nothing.  Attempts to delete non-existent customers will not raise any errors.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Deleting_customers)

### Retrieve list of customer profiles

Retrieve customer profiles.

Available arguments:

* results - the number of results you want to return
* starting_page - which page to start from. 25 results per page.

	cio.list_customers(results=100)

Returns a python list of dicts that contain customer profiles like this:

    {u'_first_seen': 1391353863,
     u'_last_visit': 1391353863,
     u'_segment:1707': 1391353816,
     u'_segment:1708:cache': [1391353863],
     u'_segment:1807': 1391353863,
     u'_segment:1808': 1391353863,
     u'created_at': 1391353816,
     u'email': u'walter@breakingbad.com',
     u'first_name': u'Walter',
     u'id': u'customer_id_string',
     u'last_name': u'White'}

### Get count of current customer profiles

How many customer profiles do you have?

	cio.get_customer_count()

Returns an integer

## Thanks

* [Dimitriy Narkevich](https://github.com/dimier) for creating the library.
