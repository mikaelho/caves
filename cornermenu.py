#coding: utf-8
from ui import *
import time
import attr
from extend import Extender
from vector import Vector
from BlurView import BlurView

class CornerMenuView (View):
  
  base_dimension = 50 # Menu item diameter
  
  def __init__(self, menu_spec, start_mode, icon_closed = 'iob:ios7_more_32', icon_open = 'iob:close_round_24', close_extra_action = None, backplane = True, on_right = True):
    
    self.flex = 'WH'
    self.touch_enabled = False
    
    self.open = False
    self.effective_height = 0
    
    self.menu_spec = menu_spec
    self.mode = start_mode
    
    self.icon_closed = Image.named(icon_closed)
    self.icon_open = Image.named(icon_open)
    
    self.backplane = backplane
    self.on_right = on_right
    
    self.menu_items = {}
    self.actions = {}
    self.root = None
  
  def style_backplane(self):
    self.backplane.hidden = True
    self.backplane.flex = 'WH'
    self.backplane.background_color = 'white'
    self.backplane.alpha = 0.8
    
  def style_menu_item(self, item, icon):
    item.height = item.width = self.base_dimension
    item.corner_radius = item.height / 2
    item.image = icon
    item.background_color = (0.32, 0.32, 0.32)
    item.tint_color = 'white'
    item.touch_enabled = True
    
  def style_label(self, label):
    label.font = ('<system>', 14)
    label.background_color = 'white'
    
  def toggle_menu(self, sender = None):
    if self.open:
      self.close_menu()
    else:
      self.open_menu()      
    self.open = self.open == False
    
  def open_menu(self):
    self.root.image = self.icon_open
    self.root.background_color = 'darkgrey'
    if self.backplane:
      self.backplane.hidden = False
    #self.bring_to_front()
    center_locations = self.get_spread(self.root.center)
    for i, menu_item in enumerate(self.menu_items[self.mode]):
      (button, label) = menu_item
      (button_center, (label.x, label.y)) = center_locations[i]
      def reveal():
        button.center = button_center
        button.alpha = 1.0
      animate(reveal, 0.2, completion = self.show_labels)
      
  def show_labels(self):
    for (item, label) in self.menu_items[self.mode]:
      def reveal_label():
        label.alpha = 1.0
      animate(reveal_label, 0.2)
    
  def close_menu(self):
    self.root.image = self.icon_closed
    self.root.background_color = (.32, .32, .32)
    if self.backplane:
      self.backplane.hidden = True
    for menu_item in self.menu_items[self.mode]:
      (button, label) = menu_item
      label.alpha = 0.0
      def collapse():
        button.center = self.root.center
        button.alpha = 0.0
      animate(collapse, 0.2)
      
  def get_spread(self, root):
    center_locations = []
    menu_items = self.menu_items[self.mode]
    
    root_vector = Vector(root)
    increment = 90/(len(menu_items) - 1)
    if not self.on_right:
      increment = 0 - increment
    angle = -90 if len(menu_items) > 1 else -135
    displacement = Vector(0, 3 * self.base_dimension)
    label_displacement = Vector(0, 4 * self.base_dimension)
    
    for (menu_item, label) in menu_items:
      displacement.degrees = label_displacement.degrees = angle
      item_location = root_vector + displacement
      label_location = root_vector + label_displacement
      label.size_to_fit()
      label_x = label_location[0]
      if self.on_right: label_x -= label.width
      label_location = (label_x, label_location[1] - label.height/2)
      center_locations.append((item_location, label_location))
      angle -= increment
      
    return center_locations
    
  def layout(self):
    
    if self.root == None:
      if self.backplane:
        self.backplane = Button()
        self.backplane.action = self.toggle_menu
        self.style_backplane()
        self.superview.add_subview(self.backplane)
      
      for mode in self.menu_spec.keys():
        self.menu_items[mode] = []
        for spec in self.menu_spec[mode]:
          button = Button()
          button.action = self.menu_action
          self.actions[button] = spec[2]
          self.style_menu_item(button, Image.named(spec[0]))
          label = Label()
          button.alpha = label.alpha = 0.0
          label.text = spec[1]
          label.touch_enabled = False
          self.style_label(label)
          self.menu_items[mode].append((button, label))
          self.superview.add_subview(button)
          self.superview.add_subview(label)
    
      self.root = Button()
      self.style_menu_item(self.root, self.icon_closed)
      self.root.action = self.toggle_menu
      self.superview.add_subview(self.root)
    
    self.backplane.frame = (0, 0, self.width, self.height)
    
    use_height = self.effective_height if self.effective_height > 0 else self.height
    use_x = self.width - self.base_dimension if self.on_right else self.base_dimension
    
    self.root.center = (use_x, use_height - self.base_dimension)
    
    locations = self.get_spread(self.root.center)
    
    for i, (button, label) in enumerate(self.menu_items[self.mode]):
      if self.open:
        (button.center, (label.x, label.y)) = locations[i]
      else:
        button.center = self.root.center
        
  def menu_action(self, sender):
    if len(self.menu_items): self.toggle_menu()
    self.actions[sender]()
        
  def set_mode(self, mode):
    if self.open: self.toggle_menu()
    self.mode = mode
        
  def keyboard_frame_did_change(self, frame):
    if self.on_screen:
      self.effective_height = convert_point((0, frame[1]), None, self)[1]
      if self.superview: self.layout()

if __name__ == '__main__':
  
  import console
  
  v = TextView()
  v.text = """Lorem ipsum
  lsjjfd
  kfkdkd
  kfkdld
  kfkdkd
  kfkdkk
  kfkdkdk
  kdkfkfk
  """
  v.background_color = 'white'
  v.present('fullscreen')
  
  def no_op():
    console.hud_alert('', duration=0.5)
  
  c = CornerMenuView({
    'note_view': (
      ( 'iob:link_32', 'Get internal link', no_op ),
      ( 'iob:ios7_world_outline_32', 'Get public link', no_op ),
      ( 'iob:ios7_search_24', 'Search', no_op )
    ),
    'note_edit': (
      ('iob:ios7_compose_outline_24', 'Link to new note', no_op ),
      ('iob:ios7_arrow_thin_right_32', 'Link to a note', no_op ),
      ( 'iob:ios7_arrow_down_24', 'Close keyboard', v.end_editing, False )
    )
  }, 'note_view')
  
  class EditDelegate():
    def __init__(self, c):
      self.c = c
    def textview_did_begin_editing(self, textview):
      self.c.set_mode('note_edit')
    def textview_did_end_editing(self, textview):
      self.c.set_mode('note_view')
  
  v.delegate = EditDelegate(c)
  
  v.add_subview(c)
  c.frame = (0, 0, v.width, v.height)
  #c.place_to_corner()
