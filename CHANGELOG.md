# Changelog

## [1.3.0]
### Added
- Support for merging duplicate customers using `merge_customers` function. 

## [1.2.0]
### Added
- Support for anonymous events using `track_anonymous` function. 

## [1.1.0]  - March 25, 2021
### Added
- Support for EU region

### Removed
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