# graphpaper.py -- a stab at making "digital graph paper"
# Ethan Glasser-Camp, 2007
import math
import sys
import gobject
import gtk
import cairo
import goocanvas

import model
from place import LINE_LEFT, LINE_TOP
import properties
import operation
import place
from drawings import PROPERTY_DRAWINGS_LINE, PROPERTY_DRAWINGS_SQUARE, \
     PROPERTY_DRAWINGS_CONNECT, PROPERTY_DRAWINGS_CONNECT_ADJ, Drawing, SPACE

import gobject
gobject.type_register(properties.Property)

CLICK_EITHER = 'either'
CLICK_LINES = 'lines'
CLICK_SQUARES = 'squares'

DRAG_SELECT_SQUARES = 'squares'
DRAG_SELECT_LINES = 'lines'
DRAG_SELECT_BOTH = 'both'
DRAG_EMIT_CONNECT = 'emit'

TARGET_EMPTY = 'empty'
TARGET_PROP = 'prop'

class DrawnProperty(object):
    '''goocanvas representation of a property.

    This class holds all the information relevant to the goocanvas
    representation of a property. Access is primarily through attributes:
    - property: the property that has been drawn
    - groups: a list of groups, one per visual "component"
    - allgroup: a group which contains all of the representation of
    the property
    '''
    def __init__(self, prop, groups, allgroup):
        self.property = prop
        self.groups = groups
        self.allgroup = allgroup

class GraphPaperView(goocanvas.Canvas):
    def __init__(self, scrolledwin):
        super(GraphPaperView, self).__init__()
        self.set_property('anchor', gtk.ANCHOR_CENTER)
        self.click_mode = CLICK_EITHER
        self.select_mode = DRAG_EMIT_CONNECT
        hscrollbar = scrolledwin.get_hscrollbar()
        vscrollbar = scrolledwin.get_vscrollbar()
        args = (hscrollbar, vscrollbar)
        hscrollbar.connect('adjust-bounds', self.on_scrolled, args)
        vscrollbar.connect('adjust-bounds', self.on_scrolled, args)

        self.model = model.GraphPaper()
        root = goocanvas.GroupModel()
        self.set_root_item_model(root)

        root_item = self.get_item(root)

        root_item.connect("button_press_event", self.on_root_button_press)
        root_item.connect("button_release_event", self.on_root_button_release)
        root_item.connect("motion_notify_event", self.on_root_motion_notify)

        self.connect('expose-event', self.on_expose_event)
        self.props_drawn = {}

        self.squares_connections = {}

        # Keeping track of when/where clicks/drags happen
        self.click_start = None
        self.click_current = None

        # Currently highlit properties
        self.highlit = None
        self.highlitprop = None

    def add_property(self, place, property):
        ops = self.model.add_property(place, property)
        self.draw_operations(ops)
        return ops

    def del_property(self, property):
        ops = self.model.del_property(property)
        self.draw_operations(ops)
        return ops

    def act_operations(self, ops, reverse=False):
        self.model.act_operations(ops, reverse)
        self.draw_operations(ops, reverse)

    def draw_operations(self, ops, reverse=False):
        t = operation.transform(reverse)
        for op in ops:
            print op
            if t[op.__class__] == operation.Removal:
                dprop = self.props_drawn.pop(op.property)
                dprop.allgroup.remove()
            elif t[op.__class__] == operation.Addition:
                p = op.property.place
                prop = op.property
                self.draw_property(prop, p)

    def draw_property(self, prop, propplace):
        p = propplace
        if isinstance(p, place.LinePlace):
            sx, sy, s = p.x, p.y, p.side
            groups = [self.draw_property_line(prop, sx, sy, s)]
        elif isinstance(p, place.SquarePlace):
            x, y = p.x, p.y
            groups = [self.draw_property_square(prop, x, y)]
        elif isinstance(p, place.ConnectPlace):
            groups = False
            if p.p1.adjacent(p.p2):
                groups = [self.draw_property_connect_adj(prop, p.p1, p.p2)]
            if not groups:
                groups = [self.draw_property_connect(prop, p.p1, 0),
                          self.draw_property_connect(prop, p.p2, 1)]

        root = self.get_root_item_model()
        allgroup = goocanvas.GroupModel()
        root.add_child(allgroup, -1)
        self.props_drawn[prop] = DrawnProperty(prop, groups, allgroup)
        allgroupitem = self.get_item(allgroup)
        for group in groups:
            allgroup.add_child(group, -1)
            r = self.bound_rect(self.get_item(group), line_width=0, fill_color_rgba=0x0077ff00)
            allgroup.add_child(r, -1)
        allgroupitem.connect('button-press-event',
                             self.on_property_button_press, prop)
        allgroupitem.connect('button-release-event',
                             self.on_property_button_release, prop)
        allgroupitem.connect('motion-notify-event',
                             self.on_property_motion_notify, prop)
        allgroupitem.connect('enter-notify-event',
                             self.on_property_enter_notify, prop)
        allgroupitem.connect('leave-notify-event',
                             self.on_property_leave_notify, prop)


    def draw_property_line(self, property, sx, sy, s):
        group = self.execute(PROPERTY_DRAWINGS_LINE[property.name])
        self.transform_line(group, sx, sy, s)
        return group

    def draw_property_connect_adj(self, prop, p1, p2):
        if not PROPERTY_DRAWINGS_CONNECT_ADJ.has_key(prop.name):
            return False
        group = self.execute(PROPERTY_DRAWINGS_CONNECT_ADJ[prop.name])
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        scale = (1, 1)
        if y1 == y2:
            side = 'left'
            if x1 < x2: # connect from left to right
                x, y = x2, y2
                scale = (-1, 1)
            else: # right to left
                x, y = x1, y1
        else: # x1 == x2
            side = 'top'
            if y1 < y2: # connect from top to bottom
                x, y = x2, y2
                scale = (-1, 1) # rotation takes care of scaling correctly
            else:
                x, y = x1, y1

        self.transform_line(group, x, y, side)
        group.scale(*scale)
        return group

    def draw_property_connect(self, prop, place, num):
        group = self.execute(PROPERTY_DRAWINGS_CONNECT[prop.name][num])
        t = goocanvas.TextModel(text=prop.letter, anchor=gtk.ANCHOR_NORTH,
                                font="Sans 8", x=0, y=0.0)
        group.add_child(t, -1)
        c = goocanvas.EllipseModel(center_x=0, center_y=0.5*SPACE+2,
                                  radius_x=2, radius_y=2)
        group.add_child(c, -1)
        self.translate_square(group, place.x+0.1, place.y)
        return group

    def draw_property_square(self, property, x, y):
        group = self.execute(PROPERTY_DRAWINGS_SQUARE[property.name])
        self.translate_square(group, x, y)
        return group

    def execute(self, drawing):
        g = goocanvas.GroupModel()
        if isinstance(drawing, Drawing):
            g.add_child(self.execute_one(drawing), -1)
        else:
            for d in drawing:
                l = self.execute_one(d)
                g.add_child(l, -1)
        return g

    def execute_one(self, drawing):
        return drawing.render()

    def translate_square(self, group, squarex, squarey):
        group.translate((squarex*SPACE)+0.5, (squarey*SPACE)+0.5)

    def transform_line(self, group, squarex, squarey, side):
        x1 = squarex*SPACE+0.5
        y1 = squarey*SPACE+0.5
        if side == LINE_LEFT:
            group.translate(x1, y1)
        elif side == LINE_TOP:
            group.translate(x1+SPACE*0.5, y1-SPACE*0.5)
            group.rotate(90, 0, 0.5*SPACE)

    def what_clicked(self, x, y, emit=False):
        '''Compute what place is at (x, y).

        Either returns a LinePlace or a SquarePlace.'''
        # Which square is it?
        squarex = math.floor(x/SPACE)
        squarey = math.floor(y/SPACE)

        offsetx = x - squarex*SPACE
        offsety = y - squarey*SPACE

        if self.click_mode == CLICK_EITHER:
            line = self.what_line(offsetx, offsety, squarex, squarey, 2)
            if line: return line
            return place.SquarePlace(squarex, squarey)
        elif self.click_mode == CLICK_SQUARES:
            return place.SquarePlace(squarex, squarey)

        else: #self.click_mode == CLICK_LINES
            return self.what_line(offsetx, offsety, squarex, squarey, SPACE/4)

    def what_line(self, offsetx, offsety, squarex, squarey, distance):
        '''Find which side of what square was clicked.

        offsetx and offsety are the distance from the topleft of
        the square at squarex, squarey. If this position is not within
        distance of any side of a square, returns False.'''
        if offsetx < distance:
            return place.LinePlace(squarex, squarey, LINE_LEFT)
        elif offsety < distance:
            return place.LinePlace(squarex, squarey, LINE_TOP)
        elif SPACE - distance < offsetx:
            return place.LinePlace(squarex+1, squarey, LINE_LEFT)
        elif SPACE - distance < offsety:
            return place.LinePlace(squarex, squarey+1, LINE_TOP)
        else:
            return False

    def highlight(self, prop):
        if prop == self.highlitprop: return
        self.remove_highlight()
        self.highlitprop = prop
        self.highlit = goocanvas.GroupModel()
        for g in self.props_drawn[prop].groups:
            r = self.bound_rect(self.get_item(g), line_width=1,
                                stroke_color_rgba=0x7777ffff,
                                fill_color_rgba=0x7777ff77)
            self.highlit.add_child(r, -1)
        self.props_drawn[prop].allgroup.add_child(self.highlit, -1)
        item = self.get_item(self.highlit)
        item.connect("leave-notify-event", self.on_highlight_leave_notify)

    def remove_highlight(self):
        if self.highlit: self.highlit.remove()
        self.highlitprop = self.highlit = None

    def bound_rect(self, groupitem, **kwargs):
        '''Creates a rect object that covers all the area a property does.'''
        b = goocanvas.Bounds()
        b = groupitem.get_bounds()
        #print "bounds:", b.x1, b.y1, b.x2, b.y2
        width = b.x2 - b.x1
        height = b.y2 - b.y1
        return goocanvas.RectModel(x=b.x1, y=b.y1, width=width, height=height,
                                   **kwargs)
        #print "rect:", b.x1, b.y1, width, height


    def emit_clicked(self, event, clicked):
        self.emit('clicked-place', event, clicked)

    def on_expose_event(self, canvas, event):
        #print 'expose', event.area
        assert (self == canvas)
        context = self.create_cairo_context()
        self.draw_grid(context, *event.area)

    def draw_grid(self, ctx, x1=0, y1=0, x2=0, y2=0):
        '''Draw grid lines in the area of ctx specified by [x1, y1, x2, y2].

        The area of ctx doesn't map to the same area of the canvas; we
        have to convert coordinate spaces first.

        '''
        w, h = ctx.get_target().get_width(), ctx.get_target().get_height()
        #print x1, y1, x2, y2
        #print canvas.get_bounds()
        #ctx.get_target().write_to_png("blah.png")
        left, top = self.convert_from_pixels(x1, y1)
        right, bottom = self.convert_from_pixels(x1+x2, y1+y2)
        #print left, top, right, bottom
        firstx = left-left%SPACE
        firsty = top-top%SPACE 
        #print "starting at", firstx, firsty
        floor = math.floor
        for i in range(int(firstx), int(right+SPACE), SPACE):
            if i%(SPACE*5)==0:
                ctx.set_source_rgb(1.0, 0, 0)
            else:
                ctx.set_source_rgb(0, 0, 1.0)
            x, y = self.convert_to_pixels(i+0.5, top)
            ctx.move_to(int(x)+0.5, int(y))
            x, y = self.convert_to_pixels(i+0.5, bottom)
            ctx.line_to(int(x)+0.5, int(y))
            ctx.set_line_width(1)
            ctx.stroke()

        for i in range(int(firsty), int(bottom+SPACE), SPACE):
            if i%(SPACE*5)==0:
                ctx.set_source_rgb(1.0, 0, 0)
            else:
                ctx.set_source_rgb(0, 0, 1.0)
            x, y = self.convert_to_pixels(left, i+0.5)
            ctx.move_to(int(x), int(y)+0.5)
            x, y = self.convert_to_pixels(right, i+0.5)
            ctx.line_to(int(x), int(y)+0.5)
            ctx.set_line_width(1)
            ctx.stroke()

    def on_scrolled(self, scrollbar, newv, (hscr, vscr)):
        '''Handler for hscrollbar and vscrollbar scrolling.

        Handles scrolling past the end of the adjustment.'''
        adj = scrollbar.get_adjustment()
        bounds = list(self.get_bounds())
        print 'scrolled to', newv, adj.lower, adj.upper
        newv = int(newv)
        resize = False
        if newv < adj.get_property('lower'):
            if isinstance(scrollbar, gtk.HScrollbar):
                bounds[0] += newv - adj.get_property('lower')
            else:
                bounds[1] += newv - adj.get_property('lower')
            self.set_bounds(*bounds)
            resize = True
            #adj.set_property('lower', newv)
            #adj.set_value(newv)
        elif newv > adj.get_property('upper')-adj.get_property('page-size'):
            if isinstance(scrollbar, gtk.HScrollbar):
                bounds[2] += newv-(adj.get_property('upper')-adj.get_property('page-size'))
            else:
                bounds[3] += newv-(adj.get_property('upper')-adj.get_property('page-size'))
            self.set_bounds(*bounds)
            resize = True
        else:
            # TODO: clamp bounds to min square, max square, margin, and newv
            pass
        # This doesn't work if you expand the window so that the canvas
        # isn't as big as the scrolledwindow containing it.
        # self.request_redraw(goocanvas.Bounds(*bounds))
        if resize:
            r = self.get_allocation()
            print "redraw all", r.x, r.y, r.width, r.height
            self.get_parent_window().invalidate_rect(self.get_allocation(),
                                                     True)

    def event_location(self, event):
        return event.x_root, event.y_root

    def on_root_button_press (self, group, target, event):
        self.click_start = (TARGET_EMPTY,
                            self.what_clicked(*self.event_location(event)))

    def on_root_button_release(self, group, target, event):
        self.release(TARGET_EMPTY, event,
                     self.what_clicked(*self.event_location(event)))

    def release(self, clicktype, event, data):
        if data == self.click_start[1]:
            # clicked on same thing; self.click_start[0] should be the same
            # as whatever it would be for here
            if isinstance(self.click_start[1], properties.Property):
                self.emit('clicked-property', data)
                return True
            else:
                self.emit_clicked(event, self.what_clicked(*self.event_location(event)))
                return True

        if self.select_mode == DRAG_EMIT_CONNECT:
            # Click and release on different things. Emit a connect signal.
            clicked = data
            oldclicked = self.click_start[1]
            p = place.ConnectPlace(oldclicked, clicked)
            self.emit('connect', event, p)

    def on_root_motion_notify(self, group, target, event):
        # We even notify if we're dragging. Is this good or bad?
        p = self.what_clicked(*self.event_location(event))
        self.emit('place-motion-notify', event, p)

    def on_property_button_press (self, group, target, event, prop):
        self.click_start = (TARGET_PROP, prop)
        return True

    def on_property_button_release (self, group, target, event, prop):
        return self.release(TARGET_PROP, event, prop)

    def on_property_motion_notify(self, group, target, event, prop):
        self.emit('property-motion-notify', event, prop)

    def on_property_enter_notify(self, group, target, event, prop):
        print 'entering', prop

    def on_property_leave_notify(self, group, target, event, prop):
        print 'leaving', prop

    def on_highlight_leave_notify(self, group, target, event):
        print "unhighlight"
        self.remove_highlight()

    def get_model(self):
        return self.model

    def serialize_stuff(self):
        return self.model.serialize_stuff()

    def read_stuff(self, filename):
        self.model.read_stuff(filename)
        #for square in self.model.propdict.values():
        #    self.draw_square(*square)

        for line in self.model.propdict.values():
            self.draw_property(line, line.place)

gobject.signal_new('clicked-place', GraphPaperView, gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_BOOLEAN,
                   (gtk.gdk.Event, place.Place))

gobject.signal_new('clicked-property', GraphPaperView, gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_BOOLEAN,
                   (properties.Property,))

gobject.signal_new('connect', GraphPaperView, gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_BOOLEAN,
                   (gtk.gdk.Event, place.Place))

gobject.signal_new('place-motion-notify', GraphPaperView, gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_BOOLEAN,
                   (gtk.gdk.Event, place.Place))

gobject.signal_new('property-motion-notify', GraphPaperView,
                   gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN,
                   (gtk.gdk.Event, properties.Property))
