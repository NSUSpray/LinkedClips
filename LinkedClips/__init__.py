from __future__ import absolute_import

def create_instance (c_instance):
    from .LinkedClips import LinkedClips
    return LinkedClips (c_instance)
