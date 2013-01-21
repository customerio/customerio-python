# Customer.io Python bindings

This module has been tested with Python 2.7.

## Installing

    pip install customerio

## Usage

	from customerio import CustomerIO
	cio = CustomerIO(site_id, api_key)
	cio.identify(id=5, email='customer@example.com', name='Bob', plan='premium')
	cio.track(customer_id=5, name='purchased')
	cio.track(customer_id=5, name='purchased', price=23.45)

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

## Thanks

* [Dimitriy Narkevich](https://github.com/dimier) for creating the library.
