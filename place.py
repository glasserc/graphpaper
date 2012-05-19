# Place.py
# Various location types and serializing/unserializing code for all.

import gobject

LINE_LEFT = 'left'
LINE_TOP = 'top'

class Place(gobject.GObject):
    def __init__(self):
        super(Place, self).__init__()

    def serialize(self):
        return []

    def __hash__(self): return hash(tuple(self.serialize()))

    def __eq__(self, o2): return self.__dict__ == o2.__dict__

    def adjacent(self, o2):
        return False

class SquarePlace(Place):
    """A place representing a Square.

    Squares are indexed by (x, y), where x and y are (positive or
    negative) integers and can extend infinitely in both
    directions."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        super(SquarePlace, self).__init__()

    def serialize(self):
        return [self.x, self.y]

    def adjacent(self, o2):
        return abs(self.x - o2.x) == 1 and self.y == o2.y or \
               abs(self.y - o2.y) == 1 and self.x == o2.x
        

class LinePlace(Place):
    '''A place represinting a Line.

    Lines are indexed by (x, y, top_or_left), where (x, y) is the
    index of a square and top_or_left is LINE_TOP if the line along
    the top of this square is meant, or LINE_LEFT if the line along
    the left of this square is meant.'''
    def __init__(self, x, y, side):
        self.x = x
        self.y = y
        self.side = side
        super(LinePlace, self).__init__()

    def serialize(self):
        return [self.x, self.y, self.side]

class PropertyPlace(Place):
    def __init__(self, place, name):
        self.place = place
        self.name = name
        super(PropertyPlace, self).__init__()

    def serialize(self):
        return [self.place.serialize(), self.name]

    def __hash__(self):
        return hash((hash(self.place), self.name))

class ConnectPlace(Place):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        super(ConnectPlace, self).__init__()

    def serialize(self):
        return [self.p1.serialize(), self.p2.serialize()]

    def __hash__(self):
        return hash((hash(self.p1), hash(self.p2)))

def unserialize(lst):
    if len(lst) == 3:
        return LinePlace(*lst)

    if len(lst) == 2:
        if isinstance(lst[0], list):
            p1 = unserialize(lst[0])
            if isinstance(lst[1], list):
                p2 = unserialize(lst[1])
                return ConnectPlace(p1, p2)
            else:
                return PropertyPlace(p1, lst[1])
        else:
            return SquarePlace(*lst)

            
