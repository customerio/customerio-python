# Changelog

## [1.0.0]
### Added
- Support for transactional api

### Removed
- Manual segmentation functions `add_to_segment` & `remove_from_segment`
- Python 2 support

### Changed
- ID fields in request path are url escaped
- Sanitize event data (customerio/customerio-python#32)
