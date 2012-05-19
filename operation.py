class Operation(object):
    def __init__(self):
        pass

class Addition(Operation):
    def __init__(self, property):
        self.property = property

class Removal(Operation):
    def __init__(self, property):
        self.property = property

TRANSFORM_REV = { Removal: Addition,
                  Addition: Removal }
TRANSFORM_ORD = { Removal: Removal,
                  Addition: Addition }

def transform(reverse=False):
    if reverse: return TRANSFORM_REV
    else: return TRANSFORM_ORD
