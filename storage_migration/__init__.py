'''A simple way to migrate between Django's storage backends'''
#: The version list
VERSION = (0, 3, 0)


def get_version():
    '''
    Converts the :attr:`VERSION` into a nice string
    '''
    if len(VERSION) > 3 and VERSION[3] not in ('final', ''):
        return '%s.%s.%s %s' % (VERSION[0], VERSION[1], VERSION[2], VERSION[3])
    else:
        return '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])


#: The actual version number, used by python (and shown in sentry)
__version__ = get_version()
