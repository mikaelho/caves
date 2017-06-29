#coding: utf-8
import ui
import console
import Image as pilImage
import io, os, json, time
import functools
import dialogs
from vector import Vector
from EvenView import EvenView

from composite import *
import cornermenu
#from Image import Image as img

class ControlCenter():
  
  menu_color = '#888888'
  
  def __init__(self, bg_view):
    self.bg = bg_view
    
    self.main_menu = self.create_main_menu()
    self.edit_view = self.create_edit_view()
    self.edit_menu = self.create_edit_menu()
    
    self.hide_all()
    self.show_main_menu()
    
  def hide_all(self):
    self.hide_main_menu()
    self.hide_edit_view()
    self.hide_edit_menu()
    
  def create_main_menu(self):
    
    spec = {
      'main': [
        { 'Play':
          [ ('Solo', self.play_solo),
            ('Multiplayer', self.play_multi)
          ]
        },
        { 'Maps':
          [ ('New', self.map_new),
            ('Edit', self.map_edit)
          ]
        }
      ]
    }
    
    main_menu = MenuView(spec, frame=self.bg.bounds)
    self.bg.add_subview(main_menu)
    return main_menu
    
  def hide_main_menu(self):
    self.main_menu.hidden = True
    
  def show_main_menu(self):
    self.main_menu.hidden = False
    self.main_menu.bring_to_front()
    
  def play_solo(self, sender):
    pass

  def play_multi(self, sender):
    pass
    
  def map_new(self, sender):
    self.hide_all()
    self.edit_view.fill()
    self.show_edit_view()
    self.show_edit_menu()

  def map_edit(self, sender):
    self.map_new(sender)
    self.load_map()

  def load_map(self):
    # Get image filename
    playfield_path = os.path.abspath('playfields')
    files = os.listdir(playfield_path)
    spec = []
    for filename in files:
      if filename.endswith('.png'):
        spec.append((filename[:-4], functools.partial(self.load_actual, playfield_path+'/'+filename)))

    if len(spec) == 0:
      console.hud_alert('Nothing to load')
    elif len(spec) == 1:
      console.hud_alert('Loaded ' + filename[:-4])
      spec[0][1]()
    else:
      menu_view = MapPicker(spec)
    return True

  def load_actual(self, img_filename):
    # Load image
    self.filename = img_filename
    iv = ui.ImageView(frame=self.bg.bounds)
    #iv.hidden = True
    #self.add_subview(iv)
    iv.image = ui.Image(img_filename)
    self.edit_view.img = snapshot(iv)

    # Clear old waypoints
    for wp in self.edit_view.waypoints:
      self.edit_view.remove_subview(wp)
    self.edit_view.waypoints = []

    # Load waypoints
    json_filename = img_filename[:-3]+'json'
    if os.path.exists(json_filename):
      with open(json_filename) as fp:
        locations = json.load(fp)
      for loc in locations:
        wp = self.edit_view.add_waypoint()
        wp.center = loc
  
  def create_edit_view(self):
    edit_view = MapView(frame=self.bg.bounds)
    self.bg.add_subview(edit_view)
    return edit_view
    
  def hide_edit_view(self):
    self.edit_view.hidden = True
  
  def show_edit_view(self):
    self.edit_view.hidden = False
    self.edit_view.bring_to_front()
    
  def create_edit_menu(self):
    buttons = [
      [ 'iow:ios7_undo_24', self.edit_view.undo_last ],
      [ 'iow:ios7_circle_outline_24', self.edit_view.toggle_digging ],
      [ 'iow:close_24', self.quit_map ],
      [ 'iow:checkmark_24', self.save_map ]
    ]
    return self.setup_bottom_menu(buttons)
    
  def setup_bottom_menu(self, buttons):
    bottom_menu_height = 40
    (_, _, w, h) = self.bg.bounds
    bottom_menu = EvenView(margin = 20)
    bottom_menu.flex = 'WT'
    bottom_menu.frame = (0, h - bottom_menu_height, w, bottom_menu_height)
    bottom_menu.background_color = 'white'
    self.bg.add_subview(bottom_menu)
    for icon, func in buttons:
      button = ui.Button(image = ui.Image.named(icon))
      button.action = func
      button.tint_color = self.menu_color
      bottom_menu.add_subview(button)
      
    return bottom_menu
    
  def hide_edit_menu(self):
    self.edit_menu.hidden = True
    
  def show_edit_menu(self):
    self.edit_menu.hidden = False
    self.edit_menu.bring_to_front()

  def quit_map(self, sender):
    self.hide_all()
    self.show_main_menu()

  def save_map(self, sender):
    try:
      (name, _) = os.path.splitext(os.path.basename(self.filename))
    except AttributeError:
      name = ''
    try:
      # Get filename
      filename = console.input_alert('Filename', '', name)
    except KeyboardInterrupt:
      return
    (name, _) = os.path.splitext(os.path.basename(filename))
    self.filename = 'playfields/' + name
    # Resize to 5s size
    #resize_5s = (640, 1136)

    for wp in self.edit_view.waypoints:
      wp.hidden = True

    snap = snapshot(self.edit_view)
    with open(self.filename + '.png', 'wb') as fp:
      fp.write(snap.to_png())

    for wp in self.edit_view.waypoints:
      wp.hidden = False

    waypoint_locations = [list(wp.center) for wp in self.edit_view.waypoints]
    with open(self.filename + '.json', 'w') as fp:
      json.dump(waypoint_locations, fp)

    self.quit_map(sender)

    #byte_file = io.BytesIO(self.iv.image.to_png())
    #pil = pilImage.open(byte_file)
    #pil = pil.resize(resize_5s)
    #pil.save(self.filename)

class PlayingView(ui.View):

  def __init__(self, starting_point, cave, multiplier):
    super().__init__()

    self.cave = cave
    self.multiplier = multiplier
    self.tracking = False
    self.previous_move = []
    self.current_move = []
    self.color = (0,0,1)
    #self.touch_stale = False

    self.start_turn(starting_point)

  def start_turn(self, starting_point):
    self.starting_point = Vector(starting_point)
    (x,y) = starting_point
    start_marker = ui.View(frame=(x,y,30,30), corner_radius=15, alpha=0.5, touch_enabled=False)
    start_marker.background_color = '#ffc688'
    self.add_subview(start_marker)
    start_marker.center = starting_point
    self.set_needs_display()

  def touch_began(self, touch):
    self.touch_stale = False
    #img_coord = (self.height - touch.location[0], touch

  def touch_moved(self, touch):
    img_loc = (touch.location[0] * self.multiplier, touch.location[1] * self.multiplier)
    img_loc = tuple(touch.location)
    wall = self.cave[img_loc][3] == 255

    if not self.tracking:
      if not self.touch_stale and not wall:
        v = Vector(touch.location)
        v = v - self.starting_point
        if v.magnitude < 15:
          self.tracking = True
          self.background_color = 'black'
          for view in self.subviews:
            self.remove_subview(view)
          self.previous_move = self.current_move
          self.current_move = [self.previous_move[-1]] if len(self.previous_move) > 0 else [list(self.starting_point)]
          self.previous_move.append(tuple(touch.location))

    else:
      self.current_move.append(tuple(touch.location))
      if wall:
        self.touch_ended(touch)

  def touch_ended(self, touch):
    self.touch_stale = True
    if self.tracking:
      self.tracking = False
      self.background_color = 'transparent'
      self.start_turn(touch.location)

  def draw(self):
    if self.tracking:
      ui.set_color('black')
      ui.fill_rect(0, 0, self.width, self.height)
    else:
      if len(self.previous_move) > 0:
        opacity_increment = 1.0/len(self.previous_move)
      path = self.new_path(self.color)
      alpha_actual = 0
      for i in range(1, len(self.previous_move)):
        alpha_actual += opacity_increment
        self.draw_segment(self.color + (alpha_actual,), self.previous_move[i-1], self.previous_move[i])
      for i in range(1, len(self.current_move)):
        self.draw_segment(self.color + (0.9,), self.current_move[i-1], self.current_move[i])

  def draw_segment(self, color, from_xy, to_xy):
    base_alpha = color[3]
    base_color = color[0:3]
    for (width, alpha) in [(1, base_alpha), (4, base_alpha-0.4), (7, base_alpha-0.8)]:
      color_actual = base_color + (alpha,)
      p = self.new_path(color_actual, width)
      p.move_to(*from_xy)
      p.line_to(*to_xy)
      p.stroke()

  def new_path(self, path_color, line_width=3):
    ui.set_color(path_color)
    path = ui.Path()
    path.line_width = line_width
    path.line_cap_style = ui.LINE_CAP_ROUND
    return path

class MapView(ui.View):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.multiplier = 1.0
    #self.iv = ui.ImageView(args, **kwargs)
    self.filename = ''
    #self.add_subview(self.iv)
    self.alpha = 0.9
    self.digging = True
    self.target_size = (self.width, self.height)
    self.dragging_waypoint = False
    self.last_img = None
    self.waypoints = []
    self.fill()

  def fill(self):
    with ui.ImageContext(self.width, self.height) as ctx:
      ui.set_color('black')
      ui.fill_rect(0, 0, self.width, self.height)
#      iv = ui.ImageView(frame=self.bounds)
#      iv.image = ui.Image('playfields/origami.png')
#
#      img = snapshot(iv)
#      blend_mode = ui.B
#      ui.set_blend_mode(blend_mode)
      #iv.image.draw()
#      img.draw()
      self.img = ctx.get_image()

  @property
  def img(self):
    return self._img

  @img.setter
  def img(self, value):
    self._img = value
    self.set_needs_display()

  def draw(self):
    self.img.draw()

  def toggle_digging(self, sender):
    self.digging = self.digging == False
    if self.digging:
      sender.image=ui.Image.named('iow:ios7_circle_outline_24')
    else:
      sender.image=ui.Image.named('iow:ios7_circle_filled_24')

#  def show_menu(self, sender):
#    spec = [
#      ('Play', self.play),
#      ('Save', self.save_map),
#      ('Load', self.load_map)
#    ]
#
#    menu_view = MenuView(spec)

  def play(self):
    if len(self.waypoints) > 0:
      starting_point = self.waypoints[0].center
    else:
      console.hud_alert('Cannot play - No waypoints on map')
      return

    img = pilImage.open(io.BytesIO(self.img.to_png()))
    img = img.resize((int(self.width), int(self.height))).load()
    v = PlayingView(starting_point, img, self.multiplier)
    self.superview.add_subview(v)
    v.frame = self.superview.bounds

  def touch_began(self, data):
    (x,y) = data.location
    if x < 20:
      self.dragging_waypoint = True
      self.w = self.add_waypoint()
    else:
      self.last_img = self.img #snapshot(self)

  def touch_moved(self, data):
    if self.dragging_waypoint:
      self.w.center = data.location
      return
    (w, h) = self.img.size
    with ui.ImageContext(w,h) as ctx:
      self.img.draw()
      blend_mode = ui.BLEND_CLEAR if self.digging else ui.BLEND_NORMAL
      ui.set_blend_mode(blend_mode)
      ui.set_color('black')
      (x, y) = data.location #* self.multiplier
      (px, py) = data.prev_location #* self.multiplier
      path = ui.Path()
      path.move_to(px, py)
      path.line_to(x, y)
      path.line_width = 20 #* self.multiplier #if self.digging else 1
      path.line_cap_style = ui.LINE_CAP_ROUND
      path.stroke()
      self.img = ctx.get_image()
    #self.set_needs_display()

  def touch_ended(self, data):
    self.dragging_waypoint = False

  def add_waypoint(self):
    w = WayPointView(frame=(0,0,30,30))
    l = w['Label']
    self.waypoints.append(w)
    l.text=str(len(self.waypoints))
    l.text_color = 'black'
    l.font=('Arial Black', 16)
    w.background_color = '#a2c2ff' #
    self.add_subview(w)
    return w

  def remove_waypoint(self, wp_view):
    i = self.waypoints.index(wp_view)
    self.remove_subview(wp_view)
    del self.waypoints[i]
    for (i, wp) in enumerate(self.waypoints):
      wp.text=str(i+1)

  def undo_last(self, sender):
    if self.last_img is not None:
      self.img = self.last_img
      

class WayPointView(Solid, Round, DefaultLabel):

  def touch_moved(self, touch):
    (x, y) = ui.convert_point(touch.location, self, self.superview)
    self.center = (x-20,y-20)

  def touch_ended(self, touch):
    (x, y) = ui.convert_point(touch.location, self, self.superview)
    if x < 20:
      self.superview.remove_waypoint(self)

def snapshot(view):
  with ui.ImageContext(view.width, view.height) as ctx:
    view.draw_snapshot()
    return ctx.get_image()


class MenuView(ui.View):

  button_height = 30
  button_gap = 5
  button_width = 200
  menu_max_height = 300
  menu_color = '#888888'

  start_menu = 'main'

  def __init__(self, spec, *args, **kwargs):
    super().__init__(*args, **kwargs)

    img_view = ui.ImageView(frame=self.bounds)

    img_view.image = ui.Image.named("playfields/caves of soukka.png")
    self.add_subview(img_view)

    self.menu = ui.View(frame=(
      (self.width - self.button_width)/4,
      self.height/12*7,
      self.button_width,
      self.height/2
    ))
    self.add_subview(self.menu)
    self.set_menu('main', spec)

  def set_menu(self, menu_key, spec):
    menu_spec = spec[menu_key]
    for v in self.menu.subviews:
      self.menu.remove_subview(v)
    top_y = 50
    for section in menu_spec:
      label = list(section.keys())[0]
      if isinstance(section[label], list):
        l = ui.Label(text=label, text_color='black', background_color=(1,1,1,0.5), alignment=ui.ALIGN_CENTER, frame=(0, top_y, self.button_width, self.button_height))
        #+self.button_gap)*(len(section[label])+1)))
        self.menu.add_subview(l)
        top_y += self.button_height + self.button_gap
        for (title, action) in section[label]:
          btn = self.menu_button(title, action, top_y)
          self.menu.add_subview(btn)
          btn.frame=(0, top_y, self.button_width, self.button_height)
          top_y += self.button_height + self.button_gap
      else:
        btn = self.menu_button(label, section[label], top_y)
        self.menu.add_subview(btn)
        btn.frame=(0, top_y, self.button_width, self.button_height)
        top_y += self.button_height + self.button_gap

  def menu_button(self, title, action, top_y):
    return ui.Button(
      title=title,
      action=action,
      tint_color='black',
      background_color='white',
      corner_radius=5
    )


class MapPicker(ui.View):
  
  button_height = 30
  button_gap = 5
  button_width = 200
  menu_max_height = 300
  menu_color = '#a2a2a2'
  
  def __init__(self, spec):
    super().__init__()
    self.present('full_screen', hide_title_bar=True)
    
    spec.append(('Cancel', None))
    menu_content_height = len(spec) * (self.button_height + self.button_gap)
    self.menu_height = min(menu_content_height, self.menu_max_height)

    self.btns = []

    for (i, (action_title, action_func)) in enumerate(spec):
      action_wrapper = functools.partial(self.func_wrapper, action_func)

      bg_color = '#e9e1e1' if action_func else '#4e4b4b'
      tnt_color = 'black' if action_func else 'white'
      btn = ui.Button(
        title=action_title,
        action=action_wrapper,
        tint_color=tnt_color,
        background_color=bg_color,
        corner_radius=5
      )
      self.add_subview(btn)
      self.btns.append(btn)


  def layout(self):
    (_,_,w,h) = self.frame
    for (i, btn) in enumerate(self.btns):
      btn.frame=(
        (w - self.button_width)/2,
        (h - self.menu_height)/2 + i*(self.button_height + self.button_gap),
        self.button_width,
        self.button_height
      )

  def exit(self, sender):
    self.superview.close()

  def func_wrapper(self, func, sender):
    if func:
      func()
    self.close()


if __name__ == '__main__':
  v = ui.ImageView()
  v.image = ui.Image.named("caves.jpg")
  v.name = 'Caves of Soukka'

  v.present('full_screen', hide_title_bar=True, orientations=['portrait'])

  #(w,h) = ui.get_screen_size()
  #s5 = ((w-320)/2, (h-568)/2, 320, 568)

  c = ControlCenter(v)

  #menu_color = '#4f4f4f'

#  menu_button = ui.ButtonItem(image=ui.Image.named('iow:drag_24'), tint_color=menu_color, action=c.show_menu)
#
#  save_button = ui.ButtonItem(image=ui.Image.named('iow:archive_24'), tint_color=menu_color, action=c.save_map)
#
#  toggle_button = ui.ButtonItem(image=ui.Image.named('iow:ios7_circle_outline_24'), tint_color=menu_color, action=c.toggle_digging)
#
#  undo_button = ui.ButtonItem(image=ui.Image.named('iow:ios7_undo_32'), tint_color=menu_color, action=c.undo_last)


#  v.right_button_items = [menu_button, toggle_button]
#
#  v.left_button_items = [undo_button]

