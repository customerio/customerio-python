# Changelog

## [1.0.0]
### Added
- Support for transactional api
- Validations for behavioural api methods

### Removed
- Manual segmentation functions `add_to_segment` & `remove_from_segment`
- Python 2 support

### Changed
- ID fields in request path are url escaped
- Sanitize event data ([#32](https://github.com/customerio/customerio-python/pull/32))