# Changelog

## [2.2]
### Added
- Add support for sending transactional sms messages [#108](https://github.com/customerio/customerio-python/pull/108)

## [2.1]
### Added
- Add support for sending [transactional push messages](https://customer.io/docs/transactional-api/#transactional-push-notifications) ([#95](https://github.com/customerio/customerio-python/pull/95))

## [2.0]
### Changed
- Updated transactional email request optional argument `amp_body` to `body_amp` for consistency across APIs ([#93](https://github.com/customerio/customerio-python/pull/93))

## [1.6.1]
### Added
- Added the `disable_css_preprocessing` and `language` optional fields to send request

## [1.3.0]
### Added
- Support for merging duplicate customers using `merge_customers` function. 

## [1.2.0]
### Added
- Support for anonymous events using `track_anonymous` function. 

## [1.1.0]  - March 25, 2021
### Added
- Support for EU region

### Changed
- `customerio.CustomerIO` and `customerio.APIClient`  have a new keyword parameter `region` that can be set to either `Regions.US` or `Regions.EU`

## [1.0.0] December 3, 2020
### Added
- Support for transactional api
- Validations for behavioural api methods

### Removed
- Manual segmentation functions `add_to_segment` & `remove_from_segment`
- Python 2 support

### Changed
- ID fields in request path are url escaped
- Sanitize event data ([#32](https://github.com/customerio/customerio-python/pull/32))
