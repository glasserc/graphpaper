import yaml
import properties
import operation
import place as places

class GraphPaper(object):
    '''Class to represent "digital graph paper".

    Digital graph paper is made up of places and properties.  A given
    (place, property) pair is unique. Places are described in the
    place module, and properties in the properties module.'''
    
    def __init__(self):
        self.propdict = {}
        self.connect_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        self.connect_letters_used = {}

    ### To change the internal representation of the graph paper, override
    ### these functions.
    def has_prop(self, place, propname):
        '''Primitive function to check if we have a property for propname at place.

        Override this if you change the internal graphpaper representation.'''
        return self.propdict.has_key((place, propname))

    def get_prop(self, place, propname):
        '''Primitive function to get the property for propname at place.

        Override this if you change the internal graphpaper representation.'''
        return self.propdict[place, propname]

    def del_prop(self, prop):
        '''Primitive function to delete the property of propname at place.

        Override this if you change the internal graphpaper representation.'''
        return self.propdict.pop((prop.place, prop.name))

    def add_prop(self, prop):
        '''Primitive function to add a property to the graphpaper.

        Override this if you change the internal graphpaper representation.'''
        self.propdict[prop.place, prop.name] = prop
        
    def add_property(self, place, propname):
        '''Add a property to the graph paper.

        This function is "high-level"; it includes dealing with dependencies
        and conflictions. The return value is a list of operations which were
        performed, including one for adding the property.'''
        if self.has_prop(place, propname):
            print self.get_prop(place, propname), 'is', (place, propname)
            return None, []
        prop = properties.Property(place, propname)
        if isinstance(place, places.ConnectPlace):
            for letter in self.connect_letters:
                if self.connect_letters_used.has_key(letter):
                    continue
                else: break
            prop.letter = letter
            self.connect_letters_used[letter] = True

        self.add_prop(prop)
        actions = [operation.Addition(prop)]

        for dep in self.connect_deps(prop):
            # FIXME: loop detection?
            dactions = self.add_property(dep.place, dep.name)
            actions.extend(dactions)

        self.connect_deps(prop)
        
        aprop = getattr(properties, prop.name)
        for conf in aprop.conflicts(self, place):
            # Just recursively add for now. More sophistication is needed!
            # FIXME: conflicts with dependencies?
            if self.has_prop(conf.place, conf.name):
                cact = self.del_property(conf)
                actions.extend(cact)

        return actions

    def del_property(self, property):
        '''Delete a property from the graph paper.

        This function is "high-level"; it deals with dependencies and
        conflicts. The return value is a list of operations which were
        performed, including one for deleting the property.'''
        if not self.has_prop(property.place, property.name):
            print "deleting nothing at %s %s" % (property.place, property.name)
            return None, []
        prop = self.del_prop(property)
        actions = [operation.Removal(prop)]
        for dprop in properties.depended_on(property.place, property.name):
            # Use recursion here. For now, don't check for inf. looping because
            # eventually we'd run out of properties!
            # FIXME: alternate satisfaction of dependencies? resolver?
            # need to really think this through!
            delact = self.del_property(dprop)
            actions.extend(delact)
        return actions

    def connect_deps(self, prop):
        '''Adds all the dependencies of a property to the properties
        dependencies, and returns the missing dependencies.'''
        missing = []
        for dep in self.get_all_deps(prop):
            prop.add_depends((dep.place, dep.name))
            if not self.has_prop(dep.place, dep.name):
                missing.append(dep)
        return missing

    def get_all_deps(self, prop):
        aprop = getattr(properties, prop.name)
        return aprop.depends(self, prop.place)

    def serialize_stuff(self):
        props = [prop.serialize() for prop in self.propdict.values()]

        return yaml.dump({'props': props, 'version': 'graphpaper-1'})

    def act_operations(self, ops, reverse=False):
        t = operation.transform(reverse)
        for op in ops:
            if t[op.__class__] == operation.Addition:
                self.add_prop(op.property)
            if t[op.__class__] == operation.Removal:
                self.del_prop(op.property)

    def read_stuff(self, filename):
        d = yaml.load(file(filename))
        for prop in d['props']:
            prop = properties.unserialize(prop)
            self.propdict[prop.place, prop.name] = prop

        for prop in self.propdict.values():
            for missing in self.connect_deps(prop):
                print "WARNING: %s %s missing dependency %s %s; adding"%\
                      (prop.place, prop.name, missing.place, missing.name)
                self.add_prop(missing)
                
