VERSION = (2, 2, 0, 'final', 0)

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s-pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s-%s-%s' % (version, VERSION[3], VERSION[4])
    return version

__version__=get_version()
