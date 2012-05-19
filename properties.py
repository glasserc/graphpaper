from gobject import GObject as object
import place

class AbstractProperty(object):
    '''Class to represent the attributes a property has -- dependencies,
    conflicts, opposites, and so on.'''
    def __init__(self, name, depends=None, conflicts=None):
        self.name = name
        self.here_depends = listify(depends)
        self.here_conflicts = listify(conflicts)

    def basename(self):
        if self.name.startswith('not_'): return self.name.replace('not_', '')
        return self.name

    def opposite(self):
        if self.name.startswith('not_'): return self.name.replace('not_', '')
        else: return 'not_%s' % self.name

    def conflicts(self, game, place):
        return [Property(place, self.opposite())] + \
               [Property(place, c) for c in self.here_conflicts] + \
               self._conflicts(game, place)

    def depends(self, game, place):
        return [Property(place, d) for d in self.here_depends] + \
               self._depends(game, place)

    # Overload these for smarter properties
    def _conflicts(self, game, place):
        return []

    def _depends(self, game, place):
        return []
    
class ConnectProperty(AbstractProperty):
    def __init__(self, *args, **kwargs):
        self.symmetric = kwargs.pop('symmetric', False)
        super(ConnectProperty, self).__init__(*args, **kwargs)


def listify(strings):
    if strings == None: strings = []
    if isinstance(strings, str): strings = [strings]
    return strings

present = AbstractProperty('present')
not_present = AbstractProperty('not_present')
one_way_leftup = AbstractProperty('one_way_leftup', depends='present')
one_way_rightdown = AbstractProperty('one_way_rightdown', depends='present')

one_way = ConnectProperty('one_way')
two_way = ConnectProperty('two_way', symmetric=True)

global_rdepends = {}

class Property(object):
    '''Class to represent one of the properties that a place has.'''
    def __init__(self, place, name, **kwargs):
        super(Property, self).__init__()
        self.place = place
        self.name = name
        self.__dict__.update(kwargs)

    def add_depends_prop(self, prop):
        self.add_depends((prop.place, prop.name))

    def add_depends(self, (place, name)):
        global_rdepends.setdefault((place, name), []).append(self)

    def __eq__(self, other):
        '''Two Properties are the same if they have the same name.

        A property is the same as a tuple if the tuple matches (place, name).
        This allows code like: ((0, 1), 'present') in squareproperties
        
        A property is the same as a string if the string matches the property
        name. DEPRECATED.'''

        if isinstance(other, tuple):
            return (self.place, self.name) == other
        if isinstance(other, Property):
            return self.place == other.place and self.name == other.name
        if isinstance(other, str):
            return self.name == other

    def __repr__(self):
        return "Property(%s, %s)"%(self.place, repr(self.name))

    PROP_TUPLE_ATTRS = ['place']
    def serialize(self):
        d = dict(self.__dict__)
        place = d.pop('place')
        for k in d.keys():
            if k.startswith('_'): del d[k]
            if k in self.PROP_TUPLE_ATTRS: d[k] = list(d[k]) # store as list
        d['place'] = place.serialize()
        return d

def depended_on(place, prop):
    return global_rdepends.get((place, prop), [])

def unserialize(obj):
    if isinstance(obj, str): return Property(obj)
    elif isinstance(obj, dict):
        for k in Property.PROP_TUPLE_ATTRS:
            if obj.has_key(k): obj[k] = tuple(obj[k]) # convert to tuple for use
        name = obj.pop('name')
        p = obj.pop('place')
        p = place.unserialize(p)
        return Property(p, name, **obj)
                
