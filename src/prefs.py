from .utils import InputType

import operator

def default_default_values():
    # Because the object is each time this function is called, it will
    # always return the same object (won't be affected by prior calls)
    return Preferences({
        (InputType.DigitalRead,): 0,
        (InputType.AnalogRead,): 0,
        (InputType.Accelerometer,): 0,
        (InputType.Accelerometer, 'z'): 1, # Gravity baked in by default on 'z' channel
        (InputType.Gyroscope,): 0,
        (InputType.Magnetometer,): 0,
    })

def default_check_functions():
    # Because the object is each time this function is called, it will
    # always return the same object (won't be affected by prior calls)
    return Preferences({
        tuple(): operator.__eq__
    })

def default_aggregators():
    # Because the object is each time this function is called, it will
    # always return the same object (won't be affected by prior calls)
    return Preferences({
        tuple(): all
    })

# Wrapper for a preferences dict
class Preferences:
    def __init__(self, prefs_dict=None):
        if prefs_dict is None:
            prefs_dict = {}
        self.prefs = prefs_dict.copy() # Copy to partially protect against changes to prefs_dict

    # Extracts the preference associated with the key list/tuple
    #   Checks for the full-length tuple and iteratively chops
    #   off the last element until the key is in the prefs dict, and
    #   returns the associated value.  If no matching pref is found,
    #   raises ValueError
    # If key == None is equivalent to empty tuple, keys that aren't
    # a tuple or list will be wrapped as a singleton tuple.  Generally,
    # tuples and lists are interchangeable
    def get_preference(self, key):
        key = make_key(key)
        while True:
            if key in self.prefs:
                return self.prefs[key]
            elif len(key) > 0:
                key = key[:-1]
            else: # No match
                raise ValueError("No preference for key={}".format(key))

    # Adds a preference (value) for a given key.  If override_subprefs,
    # then subpreferences (i.e. prefs where the key is a prefix) are deleted
    def set_preference(self, key, value, override_subprefs=False):
        key = make_key(key)
        self.prefs[key] = value
        if override_subprefs: # Delete any subpreferences

            def is_subpref(existing_key): # Any keys for which this is true will be deleted
                return len(existing_key) > len(key) and existing_key[:len(key)] == key

            self.prefs = {k:v for (k,v) in self.prefs.items() if not is_subpref(k)}

    # Returns a copy of this object, including a copy of the underlying dictionary
    def copy(self):
        return Preferences(prefs_dict=self.prefs.copy())

    def __eq__(self, other):
        return type(other) is Preferences and self.prefs == other.prefs

    def __str__(self):
        return str(self.prefs)

    def __repr__(self):
        return repr(self.prefs)

# Mostly just a helper method for properly formatting keys
# None becomes the empty tuple, lists become tuples, tuples stay the same,
# and everything else gets wrapped as a singleton tuple
def make_key(key):
    if key is None:
        return tuple()
    elif type(key) is list:
        return tuple(key)
    elif type(key) is tuple:
        return key
    else:
        return (key,)
