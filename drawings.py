import goocanvas

SPACE = 40
class Drawing(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super(Drawing, self).__init__()

    def render(self):
        return self._render()

    def _render(self):
        raise NotImplementedError, "need to overload this"

class Line(Drawing):
    klass = goocanvas.PolylineModel
    def __init__(self, points, **kwargs):
        kwargs.setdefault('stroke_color_rgba', 0x000000ff)
        super(Line, self).__init__(**kwargs)
        self.points = p(*points)

    def _render(self):
        return self.klass(points=self.points.scale(SPACE), **self.kwargs)

class Square(Drawing):
    def __init__(self, **kwargs):
        super(Square, self).__init__(**kwargs)
        
    def _render(self):
        return goocanvas.RectModel(x=0, y=0, width=SPACE, height=SPACE,
                                   line_width=1.0, **self.kwargs)

class p(object):
    def __init__(self, *args):
        self.original = args

    def scale(self, scale):
        self.scalepoints = []
        for p in self.original:
            self.scalepoints.append((p[0]*scale, p[1]*scale))
            
        self.points = goocanvas.Points(self.scalepoints)
        return self.points

PROPERTY_DRAWINGS_LINE = {
    'present': Line([(0, 0), (0, 1)], line_width=3),
    'not_present': Line([(0, 0), (0, 1)], stroke_color_rgba=0xffffffcf,
                        line_width=3),
}

PROPERTY_DRAWINGS_CONNECT = {
    'one_way': [Line([(0, 0.5), (0, 0.25)], end_arrow=True, line_width=1),
                Line([(0, 0.25), (0, 0.5)], end_arrow=True, line_width=1)],
    'two_way': []
    }

# ADJ drawings are drawn to fit in the left side of the first place (p1).
PROPERTY_DRAWINGS_CONNECT_ADJ = {
    'one_way': Line([(0.25, 0.5), (-0.25, 0.5)], end_arrow=True, line_width=1)
    }

PROPERTY_DRAWINGS_SQUARE = {
    'present': Square(fill_color="red")
    }
