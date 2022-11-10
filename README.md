<p align="center">
  <a href="https://customer.io">
    <img src="https://user-images.githubusercontent.com/6409227/144680509-907ee093-d7ad-4a9c-b0a5-f640eeb060cd.png" height="60">
  </a>
  <p align="center">Power automated communication that people like to receive.</p>
</p>

[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blueviolet?logo=gitpod)](https://gitpod.io/#https://github.com/customerio/customerio-python/)
![PyPI](https://img.shields.io/pypi/v/customerio)
![Software License](https://img.shields.io/github/license/customerio/customerio-python)
[![Build status](https://github.com/customerio/customerio-python/actions/workflows/main.yml/badge.svg)](https://github.com/customerio/customerio-python/actions/workflows/main.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/customerio)
![PyPI - Downloads](https://img.shields.io/pypi/dm/customerio)

# Customer.io Python 

This module has been tested with Python 3.6, 3.7, 3.8 and 3.9.

## Installing

```bash
pip install customerio
```

## Usage

```python
from customerio import CustomerIO, Regions
cio = CustomerIO(site_id, api_key, region=Regions.US)
cio.identify(id="5", email='customer@example.com', name='Bob', plan='premium')
cio.track(customer_id="5", name='purchased')
cio.track(customer_id="5", name='purchased', price=23.45)
```

### Instantiating customer.io object

Create an instance of the client with your [Customer.io credentials](https://fly.customer.io/settings/api_credentials).

```python
from customerio import CustomerIO, Regions
cio = CustomerIO(site_id, api_key, region=Regions.US)
```
`region` is optional and takes one of two values—`Regions.US` or `Regions.EU`. If you do not specify your region, we assume that your account is based in the US (`Regions.US`). If your account is based in the EU and you do not provide the correct region (`Regions.EU`), we'll route requests to our EU data centers accordingly, however this may cause data to be logged in the US. 

### Create or update a Customer.io customer profile

```python
cio.identify(id="5", email='customer@example.com', name='Bob', plan='premium')
```

Only the id field is used to identify the customer here.  Using an existing id with
a different email (or any other attribute) will update/overwrite any pre-existing
values for that field.

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Creating_or_updating_customers)

### Track a custom event

```python
cio.track(customer_id="5", name='purchased')
```

### Track a custom event with custom data values

```python
cio.track(customer_id="5", name='purchased', price=23.45, product="widget")
```

You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Track_a_custom_event)

### Backfill a custom event

```python
from datetime import datetime, timedelta

customer_id = "5"
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

### Track an anonymous event

```python
cio.track_anonymous(anonymous_id="anon-event", name="purchased", price=23.45, product="widget")
```

An anonymous event is an event associated with a person you haven't identified. The event requires an `anonymous_id` representing the unknown person and an event `name`. When you identify a person, you can set their `anonymous_id` attribute. If [event merging](https://customer.io/docs/anonymous-events/#turn-on-merging) is turned on in your workspace, and the attribute matches the `anonymous_id` in one or more events that were logged within the last 30 days, we associate those events with the person.

#### Anonymous invite events

If you previously sent [invite events](https://customer.io/docs/anonymous-invite-emails/), you can achieve the same functionality by sending an anonymous event with the anonymous identifier set to `None`. To send anonymous invites, your event *must* include a `recipient` attribute. 

```python
cio.track_anonymous(anonymous_id=None, name="invite", first_name="alex", recipient="alex.person@example.com")
```

### Delete a customer profile
```python
cio.delete(customer_id="5")
```

Deletes the customer profile for a specified customer.

This method returns nothing.  Attempts to delete non-existent customers will not raise any errors.

See original REST documentation [here](http://customer.io/docs/api/rest.html#section-Deleting_customers)


You can pass any keyword arguments to the `identify` and `track` methods. These kwargs will be converted to custom attributes.

### Merge duplicate customer profiles

When you merge two people, you pick a primary person and merge a secondary, duplicate person into it. The primary person remains after the merge and the secondary is deleted. This process is permanent: you cannot recover the secondary person.

For each person, you'll set the type of identifier you want to use to identify a person—one of `id`, `email`, or `cio_id`—and then you'll provide the corresponding identifier.

```python
## Please import identifier types
cio.merge_customers(primary_id_type=ID,
  primary_id="cool.person@company.com", 
  secondary_id_type=EMAIL, 
  secondary_id="cperson@gmail.com"
)
```

### Add a device
```python
cio.add_device(customer_id="1", device_id='device_hash', platform='ios')
```

Adds the device `device_hash` with the platform `ios` for a specified customer.

Supported platforms are `ios` and `android`. 

Optionally, `last_used` can be passed in to specify the last touch of the device. Otherwise, this attribute is set by the API.

```python
cio.add_device(customer_id="1", device_id='device_hash', platform='ios', last_used=1514764800})
```

This method returns nothing.

### Delete a device
```python
cio.delete_device(customer_id="1", device_id='device_hash')
```

Deletes the specified device for a specified customer.

This method returns nothing. Attempts to delete non-existent devices will not raise any errors.

### Suppress a customer
```python
cio.suppress(customer_id="1")
```

Suppresses the specified customer. They will be deleted from Customer.io, and we will ignore all further attempts to identify or track activity for the suppressed customer ID

See REST documentation [here](https://learn.customer.io/api/#apisuppress_add)

### Unsuppress a customer
```python
cio.unsuppress(customer_id="1")
```

Unsuppresses the specified customer. We will remove the supplied id from our suppression list and start accepting new identify and track calls for the customer as normal

See REST documentation [here](https://learn.customer.io/api/#apisuppress_delete)

### Send Transactional Messages

To use the [Transactional API](https://customer.io/docs/transactional-api), instantiate the Customer.io object using an [app key](https://customer.io/docs/managing-credentials#app-api-keys) and create a request object containing:

* `transactional_message_id`: the ID of the transactional message you want to send, or the `body`, `from`, and `subject` of a new message.
* `to`: the email address of your recipients 
* an `identifiers` object containing the `id` of your recipient. If the `id` does not exist, Customer.io will create it.
* a `message_data` object containing properties that you want reference in your message using Liquid.
* You can also send attachments with your message. Use `attach` to encode attachments.

Use `send_email` referencing your request to send a transactional message. [Learn more about transactional messages and `SendEmailRequest` properties](https://customer.io/docs/transactional-api).

```python
from customerio import APIClient, Regions, SendEmailRequest
client = APIClient("your API key", region=Regions.US)

request = SendEmailRequest(
  to="person@example.com",
  transactional_message_id="3",
  message_data={
    "name": "person",
    "items": [
      {
        "name": "shoes",
        "price": "59.99",
      },
    ]
  },
  identifiers={
    "id": "2",
  }
)

with open("path to file", "rb") as f:
  request.attach('receipt.pdf', f.read())

response = client.send_email(request)
print(response)
```

## Notes
- The Customer.io Python SDK depends on the [`Requests`](https://pypi.org/project/requests/) library which includes [`urllib3`](https://pypi.org/project/urllib3/) as a transitive dependency.  The [`Requests`](https://pypi.org/project/requests/) library leverages connection pooling defined in [`urllib3`](https://pypi.org/project/urllib3/).  [`urllib3`](https://pypi.org/project/urllib3/) only attempts to retry invocations of `HTTP` methods which are understood to be idempotent (See: [`Retry.DEFAULT_ALLOWED_METHODS`](https://github.com/urllib3/urllib3/blob/main/src/urllib3/util/retry.py#L184)).  Since the `POST` method is not considered to be idempotent, any invocations which require `POST` are not retried.

- It is possible to have the Customer.io Python SDK effectively *disable* connection pooling by passing a named initialization parameter `use_connection_pooling` to either the `APIClient` class or `CustomerIO` class.  Setting this parameter to `False` (default: `True`) causes the [`Session`](https://github.com/psf/requests/blob/main/requests/sessions.py#L355) to be initialized and discarded after each request.  If you are experiencing integration issues where the cause is reported as `Connection Reset by Peer`, this may correct the problem.  It will, however, impose a slight performance penalty as the TCP connection set-up and tear-down will now occur for each request.

### Usage Example Disabling Connection Pooling
```python
from customerio import CustomerIO, Regions
cio = CustomerIO(site_id, api_key, region=Regions.US, use_connection_pooling=False)
```

## Running tests

Changes to the library can be tested by running `make test` from the parent directory.

## Thanks!

* [Dimitriy Narkevich](https://github.com/dimier) for creating the library.
* [EZL](https://github.com/ezl) for contributing customer deletes and improving README
* [Noemi Millman](https://github.com/sbnoemi) for adding custom JSON encoder
* [Jason Kraus](https://github.com/zbyte64) for event backfilling
* [Nicolas Paris](https://github.com/niparis) for better handling of NaN values
