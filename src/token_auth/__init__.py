#v0.3.2b3
VERSION = (1, 3, 2, 'beta', 3)

STATUSES = {'alpha': 'a', 'beta': 'b', 'releasecandidiate': 'rc' }

def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    
    else:
        if VERSION[3] != 'final':
            version = '%s%s%s' % (version, STATUSES[VERSION[3]], VERSION[4])
    return version
