import os
import gtk.glade
import goocanvas
import view
import place

class GraphPaperApp(object):
    def __init__(self):
        self.xml = gtk.glade.XML('graphpaperui.glade')
        scroll = self.xml.get_widget('canvasscroll')
        self.canvas = view.GraphPaperView(scroll)
##        if os.path.exists('input'):
##            self.canvas.read_stuff('input')
        scroll.add(self.canvas)
        self.canvas.set_size_request(600, 450)
        self.canvas.set_bounds(0, 0, 600, 450)
        self.canvas.show()
        self.canvas.connect('clicked-place', self.on_graph_clicked_place)
        self.canvas.connect('connect', self.on_graph_connect)
        self.canvas.connect('clicked-property', self.on_graph_clicked_property)
        self.canvas.connect('place-motion-notify', self.on_graph_place_motion_notify)
        self.canvas.connect('property-motion-notify', self.on_graph_property_motion_notify)
        #self.canvas.scroll_to(0, 0)
        self.xml.get_widget('mainwindow').show()

        self.statusbar = self.xml.get_widget('mainstatusbar')
        self.statusbarctx = self.statusbar.get_context_id("")
        self.statusbar.push(self.statusbarctx, "Welcome to graphpaper.")
        self.rightframe = self.xml.get_widget('rightframe')
        self.xml.signal_autoconnect(self)

        root = self.canvas.get_root_item_model()
        self.undostack = []
        self.redostack = []

    def on_mainwindow_delete_event(self, *args):
        gtk.main_quit()

    def on_gtk_open_activate(self, menuitem):
        d = gtk.FileChooserDialog(buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                           gtk.STOCK_OK, gtk.RESPONSE_OK),
                                  title="Open file")
        response = d.run()
        if response == gtk.RESPONSE_OK:
            f = d.get_filename()
            self.canvas.read_stuff(f)
        d.destroy()

    def on_gtk_save_activate(self, menuitem):
        self.on_gtk_save_as_activate(menuitem)

    def on_gtk_save_as_activate(self, menuitem):
        file('output', 'w').write(self.canvas.serialize_stuff())

    def on_gtk_undo_activate(self, menuitem):
        print "undo!"
        if self.undostack:
            ops = self.undostack.pop()
            self.canvas.act_operations(ops, True)
            self.redostack.append(ops)

    def on_gtk_redo_activate(self, menuitem):
        print "redo!"

    def on_graph_clicked_place(self, canvas, event, place):
        if event.button == 1:
            prop = 'present'
        elif event.button == 3:
            prop = 'not_present'
            
        ops = self.canvas.add_property(place, prop)
        self.undostack.append(ops)
        del self.redostack[:]

    def on_graph_clicked_property(self, canvas, prop):
        print "prop was clicked:", prop
        ops = self.canvas.del_property(prop)
        self.undostack.append(ops)
        del self.redostack[:]
        
    def on_graph_connect(self, canvas, event, places):
        self.canvas.add_property(places, 'one_way')

    def on_graph_place_motion_notify(self, canvas, event, place):
        self.statusbar.pop(self.statusbarctx)
        self.statusbar.push(self.statusbarctx, str(place.serialize()))

    def on_graph_property_motion_notify(self, canvas, event, prop):
        self.rightframe.remove(self.rightframe.get_child())
        t = gtk.Table(2, 4)
        def m(s): l = gtk.Label(); l.set_markup(s); return l
        args = {'xoptions': False, 'yoptions': False}
        t.attach(m("<b>Property</b>"), 0, 1, 0, 1, **args)
        t.attach(gtk.Label(prop.name), 1, 2, 0, 1, **args)
        t.attach(m("<b>At</b>"), 0, 1, 1, 2, **args)
        t.attach(gtk.Label(prop.place.serialize()), 1, 2, 1, 2, **args)
        t.show_all()
        self.rightframe.add(t)
        canvas.highlight(prop)

g = GraphPaperApp()
gtk.main()
