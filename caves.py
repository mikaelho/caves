#coding: utf-8
import ui
import console, dialogs
import Image as pilImage
import io, os, json, time, math
import functools, contextlib
import dialogs
from vector import Vector
from EvenView import EvenView

#from composite import *
#import cornermenu
#from Image import Image as img

def inttuple(input_pair):
  return (int(input_pair[0]), int(input_pair[1]))

def pil_color(color):
  color = ui.parse_color(color)
  result_color = tuple()
  for band in color:
    result_color += (int(band*255),)
  return result_color

class ControlCenter():
  
  menu_color = '#888888'
  colors = ['green', 'red', 'blue', 'orange', 'violet']
  icon_names = [
    'emj:Snake',
    'emj:Octopus',
    'emj:Whale',
    'emj:Honeybee',
    'emj:Lady_Beetle'
  ]

#  icon_names = [
#    'spc:PlayerShip1Green',
#    'spc:PlayerShip2Red',
#    'spc:PlayerShip3Blue',
#    'spc:PlayerShip2Orange'
#  ]

  small_icon_names = [
    'spc:PlayerLife1Green',
    'spc:PlayerLife2Red',
    'spc:PlayerLife3Blue',
    'spc:PlayerLife2Orange',
    'spc:PlayerLife3Red'
    
  ]
  active_players = [True]*len(colors)
  
  def __init__(self, bg_view):
    self.bg = bg_view
    
    self.main_menu = self.create_main_menu()
    self.edit_view = self.create_edit_view()
    self.edit_menu = self.create_edit_menu()
    self.play_menu = self.create_play_menu()
    self.play_layers = self.create_play_layers()
    self.set_default_map()
    self.hide_all()
    self.show_main_menu()
    
  def set_default_map(self):
    playfield_path = 'playfields'
    files = os.listdir(playfield_path)
    for file in files:
      if file.endswith('.png'):
        filename = file
        break
    self.set_map_for_play(playfield_path+'/'+filename)
    
  def hide_all(self):
    self.hide_main_menu()
    self.hide_edit_view()
    self.hide_edit_menu()
    self.hide_play_menu()
    self.hide_play_layers()
    
  def create_main_menu(self):
    
    spec = [
      ('PLAY', self.play),
      ('NEW', self.map_new),
      ('EDIT', self.map_edit)
    ]
    
    main_menu = MenuView(self, spec, frame=self.bg.bounds)
    self.bg.add_subview(main_menu)
    return main_menu
    
  def hide_main_menu(self):
    self.main_menu.hidden = True
    
  def show_main_menu(self):
    self.bg.image = ui.Image.named("backgrounds/caves.jpg")
    self.main_menu.hidden = False
    self.main_menu.bring_to_front()
    
  def set_map_for_play(self, img_filename):
    self.filename = img_filename
    (name, _) = os.path.splitext(os.path.basename(img_filename))
    self.main_menu.map_btn.title = name
    
  def play(self, sender):
    self.hide_all()
    #self.show_play_menu() dialog
    self.show_edit_view()
    self.load_actual(burn_waypoints_in=True)
      
    with io.BytesIO(self.edit_view.img.to_png()) as fp:
      playfield = pilImage.open(fp).resize((int(self.bg.width), int(self.bg.height))).load()
#    for x in range(3000):
#      try:
#        pix = playfield[x, 400]
#        (pix[3])
#      except:
#        print(x)
#        break
    for layer in self.play_layers:
      layer.set_map(self.edit_view.waypoints, playfield, self.multiplier)
    self.show_play_layers()
    self.turn = -1
    self.next_turn()

  def next_turn(self, sender=None):
    self.turn += 1
    try:
      self.turn += self.active_players[self.turn:].index(True)
    except ValueError:
      winners = []
      for i, layer in enumerate(self.play_layers):
        if layer.waypoints_visited == len(layer.waypoints):
          winners.append(i)
      if len(winners) > 0:
        msg = ''
        for winner in winners:
          msg += ' ' + self.colors[winner].capitalize()
        console.alert('Winner', msg, button1='Ok', hide_cancel_button=True)
        self.hide_all()
        self.show_main_menu()
        return
      self.turn = self.active_players.index(True)

    self.hide_play_menu()
    if self.active_players.count(True) > 1:
      turn_button = ui.Button(frame=self.bg.bounds, background_color=(0, 0, 0, 0.9))
      turn_button.title = '  Tap to play'
      turn_button.tint_color = self.colors[self.turn]
      
      def turn_start_action(sender):
        self.bg.remove_subview(turn_button)
        self.play_layers[self.turn].start_turn()
        
      turn_button.action = turn_start_action
      self.bg.add_subview(turn_button)
      turn_button.image = self.main_menu.icons['player'+str(self.turn)]
    else:
      self.play_layers[self.turn].start_turn()

  def quit_game(self, sender):
    try:
      console.alert('Quit game?', button1='Ok')
    except KeyboardInterrupt:
      return
    self.hide_all()
    self.show_main_menu()

#  def play_multi(self, sender):
#    pass
#    
#  def load_and_play(self, img_filename):
#    self.load_actual(img_filename)
#    self.show_play_view()

  def map_new(self, sender):
    self.hide_all()
    self.filename = ''
    self.edit_view.fill()
    self.show_edit_view()
    self.show_edit_menu()

  def map_edit(self, sender):
    filename_safe = self.filename
    self.map_new(sender)
    self.filename = filename_safe
    self.load_actual()

  def load_map(self, path='playfields', extension='.png', next_func=None):
    # Get image filename
    next_func = next_func if next_func else self.load_actual
    playfield_path = path #os.path.abspath(path)
    files = os.listdir(playfield_path)
    spec = []
    for filename in files:
      if not extension or filename.endswith(extension):
        spec.append((filename[:-4], functools.partial(next_func, playfield_path+'/'+filename)))

    if len(spec) == 0:
      console.hud_alert('Nothing to load')
    elif len(spec) == 1:
      console.hud_alert('Loaded ' + filename[:-4])
      spec[0][1]()
    else:
      menu_view = MapPicker(spec)
    return True

  def load_actual(self, burn_waypoints_in=False):
    # Clear old waypoints
    for wp in self.edit_view.waypoints:
      self.edit_view.remove_subview(wp)
    self.edit_view.waypoints = []
    
    # Load image
    img_filename = self.filename
    iv = ui.ImageView(frame=self.bg.bounds)
    #iv.hidden = True
    #self.add_subview(iv)
    iv.image = ui.Image(img_filename)
    self.edit_view.img = snapshot(iv)
    self.multiplier = self.edit_view.img.size[1]/self.edit_view.height

    # Load settings
    json_filename = img_filename[:-3]+'json'
    if os.path.exists(json_filename):
      with open(json_filename) as fp:
        settings = json.load(fp)
      if isinstance(settings, dict):
        locations = settings['waypoint_locations']
        self.bg.image = ui.Image.named(settings['bg_filename'])
        self.edit_view.bg_filename = settings['bg_filename']
      else:
        locations = settings
        self.bg.image = ui.Image.named('backgrounds/caves.jpg')
        self.edit_view.bg_filename = None
      for loc in locations:
        wp = self.edit_view.add_waypoint()
        wp.center = loc
        
    if burn_waypoints_in:
      with ui.ImageContext(self.edit_view.width, self.edit_view.height) as ctx:
        self.edit_view.img.draw()
        ui.set_blend_mode(ui.BLEND_CLEAR)
        ui.set_color('black')
        for wp in self.edit_view.waypoints:
          (x,y) = wp.center
          path = ui.Path.oval(x-15, y-15, 30, 30)
          path.fill()
        self.edit_view.img = ctx.get_image()
  
  def create_edit_view(self):
    edit_view = MapView(self, frame=self.bg.bounds)
    self.bg.add_subview(edit_view)
    return edit_view
    
  def hide_edit_view(self):
    self.edit_view.hidden = True
  
  def show_edit_view(self):
    self.edit_view.hidden = False
    self.edit_view.bring_to_front()
    
  def create_edit_menu(self):
    buttons = [
      [ 'iow:close_24', self.quit_map ],
      [ 'iow:ios7_undo_24', self.edit_view.undo_last ],
      [ 'iow:ios7_redo_24', self.edit_view.redo_next ],
      [ 'iow:ios7_trash_24', self.edit_view.delete ],
      [ 'iow:image_24', self.edit_view.choose_background ],
      [ 'iow:beaker_24', self.edit_view.flood_fill ],
      [ 'iow:ios7_circle_outline_24', self.edit_view.toggle_digging ],
      [ 'iow:checkmark_24', self.save_map ]
    ]
    menu = self.setup_bottom_menu(buttons)
    return menu
    
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
      button.name = func.__name__
      button.tint_color = self.menu_color
      bottom_menu.add_subview(button)
    return bottom_menu
    
  def hide_edit_menu(self):
    self.edit_menu.hidden = True
    
  def show_edit_menu(self):
    self.edit_view.set_buttons()
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
      
    alpha_before = self.edit_view.alpha
    self.edit_view.alpha = 1.0
    
    snap = snapshot(self.edit_view)
    
    self.edit_view.alpha = alpha_before
    
    with open(self.filename + '.png', 'wb') as fp:
      fp.write(snap.to_png())

    for wp in self.edit_view.waypoints:
      wp.hidden = False

    waypoint_locations = [list(wp.center) for wp in self.edit_view.waypoints]
    
    if self.edit_view.bg_filename:
      settings = {
        'bg_filename': self.edit_view.bg_filename,
        'waypoint_locations': waypoint_locations
      }
    else:
      settings = waypoint_locations
      
    with open(self.filename + '.json', 'w') as fp:
      json.dump(settings, fp)

    self.quit_map(sender)

    #byte_file = io.BytesIO(self.iv.image.to_png())
    #pil = pilImage.open(byte_file)
    #pil = pil.resize(resize_5s)
    #pil.save(self.filename)
    
  def create_play_menu(self):
    play_menu = ui.View(frame=self.bg.bounds)
    self.bg.add_subview(play_menu)
    buttons = [
      [ 'iow:close_round_24', self.quit_game ],
      [ 'iow:arrow_right_b_32', self.next_turn ]
    ]
    return self.setup_bottom_menu(buttons)
#    (_,_,w,h) = play_menu.frame
#    def pick_map(sender):
#      self.load_map(next_func=self.set_map_for_play)
#    self.map_btn = ui.Button(title='Pick map', tint_color='black', background_color=self.menu_color, corner_radius=5, action=pick_map, frame=(0.1*w, 0.1*h, 0.8*w, 50))
#    play_menu.add_subview(self.map_btn)
#    return play_menu

  def hide_play_menu(self):
    self.play_menu.hidden = True
    
  def show_play_menu(self):
    self.play_menu.hidden = False
    self.play_menu.bring_to_front()
    
  def create_play_layers(self):
    layers = []
    for color in self.colors:
      layer = PlayingLayer(self, color=color, frame=self.bg.bounds)
      self.bg.add_subview(layer)
      layers.append(layer)
    return layers
    
  def hide_play_layers(self):
    for layer in self.play_layers:
      layer.hidden = True
    
  def show_play_layers(self):
    pass
#    for layer in self.play_layers:
#      layer.hidden = False
#      layer.bring_to_front()


#class PlayingView(ui.View):
#  
#  def __init__(self, players, waypoints, playfield):
#    self.players = players
#    for player in players:
#      player['current_location'] = waypoints[0].center
#      layer = PlayingLayer()
#      player['view'] 


class PlayingLayer(ui.View):

  def __init__(self, control, *args, color=(0, 0, 1), **kwargs):
    super().__init__(*args, **kwargs)

    self.control = control
    self.color = ui.parse_color(color)
    self.init_values()
    #self.start_turn(starting_point)
    
  def init_values(self):
    self.tracking = False
    self.previous_move = []
    self.current_move = []
    self.touch_stale = False
    self.animate_counter = -1
    self.waypoints_visited = 0
    
  def set_map(self, waypoints, playfield, multiplier=1.0):
    self.waypoints = waypoints
    self.playfield = playfield
    self.multiplier = multiplier  
    self.starting_point = self.waypoints[0].center
    self.init_values()

  def start_turn(self):
    starting_point = Vector(self.starting_point)
    (x,y) = starting_point
    #start_marker = ui.View(frame=(x,y,30,30), corner_radius=15, alpha=0.5, touch_enabled=False)
    #start_marker.background_color = '#ffc688'
    #self.add_subview(start_marker)
    self.start_area = self.flood_fill_start_marker(tuple(starting_point), self.color)
    #self.add_subview(self.start_area)
    #start_marker.center = tuple(starting_point)
    self.hidden = False
    self.bring_to_front()
    for layer in self.control.play_layers:
      layer.alpha = 0.5
    self.alpha = 1.0
    for i, wp in enumerate(self.waypoints):
      wp.background_color = '#6cd655' if i < self.waypoints_visited else '#a2c2ff'
    self.set_needs_display()

  def touch_began(self, touch):
    self.touch_stale = False
    #img_coord = (self.height - touch.location[0], touch

  def touch_moved(self, touch):
    #img_loc = (touch.location[0] * self.multiplier, touch.location[1] * self.multiplier)
    tl = touch.location
    img_loc = touch.location
    wall = self.playfield[tuple(tl)][3] > 200

    if not self.tracking:
      if not self.touch_stale and not wall:
        v = Vector(touch.location)
        v = v - self.starting_point
        int_tl = (int(tl[0]), int(tl[1]))
        if v.magnitude < 15 and self.start_area[int_tl][3] > 0:
          self.tracking = True
          self.background_color = 'black'
          for view in self.subviews:
            self.remove_subview(view)
          self.previous_move = self.current_move
          self.current_move = [self.previous_move[-1]] if len(self.previous_move) > 0 else [list(self.starting_point)]
          self.previous_move.append(tuple(touch.location))

    else:
      prev = Vector(touch.prev_location)
      for step in Vector(touch.prev_location).steps_to(Vector(touch.location)):
        pos = tuple(step)
        self.current_move.append(pos)
        close_to_waypoints = False
        pos_v = Vector(pos)
        for i, wp in enumerate(self.waypoints):
          if pos_v.distance_to(wp.center) < 15:
            close_to_waypoints = True
            if i == self.waypoints_visited:
              self.waypoints_visited += 1
        wall = self.playfield[pos][3] > 200
        if wall:
          if not close_to_waypoints:           
            self.end_touch(prev)
            break
        prev = Vector(pos)

  def touch_ended(self, touch):
    self.end_touch(Vector(touch.location))
    
  def end_touch(self, end_location):
    self.touch_stale = True
    if self.tracking:
      self.tracking = False
      self.background_color = 'transparent'
      self.starting_point = end_location
      for i, wp in enumerate(self.waypoints):
        wp.background_color = '#6cd655' if i < self.waypoints_visited else '#a2c2ff'
      self.control.show_play_menu()
      self.animate_counter = len(self.current_move)
      self.set_needs_display()
      
#  def animate_turn(self):
#    if self.animate_counter < len(self.current_move):
#      self.animate_counter += max(20, int(len(self.current_move)/40))
#      self.animate_counter = min(len(self.current_move)-1, self.animate_counter)
#      ui.delay(self.animate_turn, 0.05)
#      self.update_image()

  def draw(self):
    if self.tracking:
      ui.set_color('black')
      ui.fill_rect(0, 0, self.width, self.height)
    else:
      if self.animate_counter < len(self.current_move):
        self.animate_counter += max(20, int(len(self.current_move)/40))
        self.animate_counter = min(len(self.current_move)-1, self.animate_counter)
        #self.set_needs_display()
      base_color = tuple([self.color[i] for i in range(3)])
#      if len(self.previous_move) > 0:
      opacity_increment = 1.0/(len(self.current_move)+1) # 0.002
      alpha_incremental = 1.0 - self.animate_counter*opacity_increment
      if self.animate_counter > 0:
        for i in range(1, self.animate_counter):
          alpha_actual = max(0, alpha_incremental)
          self.draw_segment(base_color + (alpha_actual,), self.current_move[i-1], self.current_move[i])
          alpha_incremental += opacity_increment
#        pos1 = self.current_move[self.animate_counter - 2]
#        pos2 = self.current_move[self.animate_counter - 1]
#        angle = (Vector(pos2) - Vector(pos1)).degrees
        #print(self.animate_counter, angle)

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
    
  def flood_fill_start_marker(self, starting_point, base_color):
    marker_color = pil_color('#ffc688')
    #marker_color = pil_color(base_color)
    marker_color = tuple([min(marker_color[i], 255) for i in range(3)])
    start_area_view = ui.ImageView(frame=self.bounds)
    start_area_view.touch_enabled = False
    with io.BytesIO(snapshot(start_area_view).to_png()) as fp:
      pil = pilImage.open(fp).resize((int(self.width), int(self.height)))
      canvas = pil.load()
      starting_point = inttuple(starting_point)
      canvas[starting_point] = marker_color + (125,)
      edge = [starting_point]
      sp_vector = Vector(starting_point)
      while edge:
        newedge = []
        for (x, y) in edge:
          for candidate in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            distance = sp_vector.distance_to(candidate)
            if distance <= 15 and self.playfield[candidate][3] == 0 and canvas[candidate][3] == 0:
              ceil_dist = math.ceil(distance)
              if ceil_dist == 15:
                color = pil_color((1,1,1,0.9))
              elif ceil_dist == 14:
                color = pil_color((0.5,0.5,0.5,0.9))
              elif ceil_dist == 13:
                color = pil_color((0,0,0,0.9))
              elif ceil_dist == 12:
                color = pil_color((0.5,0.5,0.5,0.9))
              else:
                color = pil_color((1,1,1,0.01))
              canvas[candidate] = color
              #canvas[candidate] = marker_color + (125,) #(int(10+230/15*distance), )
              newedge.append(candidate)
        edge = newedge
      
    with io.BytesIO() as fp:
      pil.save(fp, 'PNG')
      start_area_view.image = ui.Image.from_data(fp.getvalue())
      
    self.add_subview(start_area_view)

    return canvas
        

class MapView(ui.View):

  def __init__(self, control, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.control = control
    self.multiplier = 1.0
    #self.iv = ui.ImageView(args, **kwargs)
    #self.filename = ''
    self.bg_filename = None # Default is caves.jpg
    #self.add_subview(self.iv)
    self.alpha = 0.9
    self.digging = True
    self.flood_filling = False
    self.touch_start = None
    self.target_size = (self.width, self.height)
    self.dragging_waypoint = False
    self.last_img = None
    self.waypoints = []
    self.history_capacity = 10
    self.fill()

  def fill(self):
    self.history = []
    self.future = []
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

  def touch_began(self, touch):
    (x,y) = touch.location
    if x < 20:
      self.dragging_waypoint = True
      self.w = self.add_waypoint()
    else:
      self.touch_start = tuple(touch.location)
      self.add_to_history()

  def touch_moved(self, data):
    if self.dragging_waypoint:
      self.w.center = data.location
      return
    if self.flood_filling:
      if Vector(data.location).distance_to(self.touch_start) < 10:
        return
      else:
        self.flood_fill(self.control.edit_menu['flood_fill'])
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
      path.line_width = 30 #* self.multiplier #if self.digging else 1
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
      wp['Label'].text=str(i+1)

  def undo_last(self, sender):
    self.future.insert(0, self.img)
    self.img = self.history.pop()
    self.set_buttons()
      
  def redo_next(self, sender):
    self.history.append(self.img)
    self.img = self.future[0]
    self.future = self.future[1:]
    self.set_buttons()
    
  def set_buttons(self):
    self.control.edit_menu['undo_last'].enabled = (len(self.history) > 0)
    self.control.edit_menu['redo_next'].enabled = (len(self.future) > 0)
      
  def delete(self, sender):
    if self.control.filename != '':
      (name, _) = os.path.splitext(os.path.basename(self.control.filename))
      try:
        console.alert('Delete', name, button1='Ok')
      except KeyboardInterrupt:
        return
      os.remove(self.control.filename)
      with contextlib.suppress(FileNotFoundError):
        os.remove(self.control.filename[:-4]+'.json')
      self.control.set_default_map()
    else:
      self.control.quit_map(sender)
      
  def choose_background(self, sender):
    self.control.load_map(path='backgrounds', extension=None, next_func=self.load_background)
    
  def load_background(self, bg_filename):
    self.control.bg.image = ui.Image.named(bg_filename)
    self.bg_filename = bg_filename
    
  def flood_fill(self, sender):
    self.flood_filling = self.flood_filling == False
    sender.tint_color = 'green' if self.flood_filling else self.control.menu_color
    
  def add_to_history(self):
    #self.last_img = self.img # snapshot(self)
    self.history.append(self.img)
    self.future = []
    if len(self.history) > self.history_capacity:
      self.history = self.history[-self.history_capacity]
    self.set_buttons()
    

class WayPointView(ui.View): #(Solid, Round, DefaultLabel):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.corner_radius = self.height/2
    l = ui.Label()
    self.add_subview(l)
    l.frame = self.bounds
    l.flex = 'WH'
    l.name = 'Label'
    l.alignment = ui.ALIGN_CENTER

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

  def __init__(self, control, spec, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.control = control
    img_view = ui.ImageView(frame=self.bounds)

    img_view.image = ui.Image.named("playfields/caves of soukka.png")
    self.add_subview(img_view)

    self.menu = ui.View(frame=(
      30, self.height/2.1, self.width - 60, self.height/2 - 30
    ), corner_radius=10)
    #self.menu.background_color=(0,0,0,0.7)
    self.add_subview(self.menu)
    
    (_,_,w,h) = self.menu.frame
    def pick_map(sender):
      self.control.load_map(next_func=self.control.set_map_for_play)
    self.map_btn = ui.Button(title='Pick map', tint_color='white', background_color=self.menu_color, corner_radius=5, action=pick_map)
    self.menu.add_subview(self.map_btn)
    self.map_btn.frame = (0.05*w, 0.05*h, 0.55*w, 50)
    
    (title, action) = spec[2]
    self.menu_button(title, action, 50, (0.7*w, 0.05*h+25))
    (title, action) = spec[1]
    self.menu_button(title, action, 50, (0.9*w, 0.05*h+25))
    
    self.icons = {}
    self.small_icons = {}
    for i in range(len(self.control.icon_names)):
      icon =   ui.Image.named(self.control.icon_names[i]).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
      small_icon = ui.Image.named(self.control.small_icon_names[i]).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
      name = 'player'+str(i)
      self.icons[name] = icon
      self.small_icons[name] = small_icon
      btn = self.menu_color_button(
        name, self.control.colors[i], icon,
        (0.05*w + i*51, 0.25*h))
      if i > 0:
        self.toggle(btn)
        
    (title, action) = spec[0]
    self.menu_button(title, action, 50, (0.9*w, 0.25*h+25))
    
    #btn = self.create_button
    #self.set_menu('main', spec)

  def menu_button(self, title, action, diameter, center):
    btn = ui.Button(
      title=title,
      action=action,
      tint_color='white',
      background_color=self.menu_color
    )
    btn.width = btn.height = diameter
    btn.corner_radius = diameter/2
    btn.center = center
    self.menu.add_subview(btn)
    
#  def menu_player_field(self, action, name, text, corner, width):
#    (x,y) = corner
#    fld = ui.TextField(
#      action=action,
#      name=name,
#      text=text,
#      tint_color='white',
#      corner_radius=5,
#      background_color=self.menu_color,
#      frame=(x, y, width, 30)
#    )
#    self.menu.add_subview(fld)
    
  def menu_color_button(self, name, color, icon, corner):
    (x,y) = corner
    #img = self.button_image('plf:AlienBlue_stand', 45)
    #img =  ui.Image.named(icon_name).with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)
    btn = ui.Button(
      name=name,
      action=self.toggle,
      background_color=color
    )
    btn.frame=(x, y, 50, 50)
    btn.corner_radius = 25
    btn.image=icon
    btn.background_color = tuple([btn.background_color[i] for i in range(3)]) + (0.8,)
    self.menu.add_subview(btn)
    return btn

#  def button_image(self, name, max_dim):
#    img = ui.Image.named(name)
#    with io.BytesIO(img.to_png()) as fp:
#      p_img = pilImage.open(fp)
#      scale = max_dim/max(p_img.size)
#      (w,h) = p_img.size
#      target = (int(w*scale), int(h*scale))
#      p_img = p_img.resize(target)
#    with io.BytesIO() as fp:
#      p_img.save(fp, 'PNG')
#      result_img = ui.Image.from_data(fp.getvalue())
#    return result_img.with_rendering_mode(ui.RENDERING_MODE_ORIGINAL)

  def toggle(self, sender):
    i = int(sender.name[-1])
    p = self.control.active_players
    p[i] = p[i] == False
    color = sender.background_color
    color = tuple([color[j] for j in range(3)])
    if not p[i]:
      color += (0.4,)
      sender.image = None
    else:
      color += (0.8,)
      sender.image = self.icons[sender.name]
    sender.background_color = color
    if not any(p):
      self.toggle(sender)

  def set_menu(self, menu_key, spec):
    menu_spec = spec[menu_key]
#    for v in self.menu.subviews:
#      self.menu.remove_subview(v)
    #top_y = 50
    x_increment = self.menu.width/(len(menu_spec)+1)
    dim = 0.55*x_increment
    for (i, (title, func)) in enumerate(menu_spec):
      btn = ui.Button()
      btn.title = title
      btn.action = func      
      btn.background_color = self.menu_color
      btn.tint_color = 'white'
      self.menu.add_subview(btn)
      btn.width = btn.height = dim
      btn.center = ((i+1)*x_increment, self.menu.height/4)
      btn.corner_radius = dim/2
      
#      label = list(section.keys())[0]
#      if isinstance(section[label], list):
#        l = ui.Label(text=label, text_color='black', background_color=(1,1,1,0.5), alignment=ui.ALIGN_CENTER, frame=(0, top_y, self.button_width, self.button_height))
#        #+self.button_gap)*(len(section[label])+1)))
#        self.menu.add_subview(l)
#        top_y += self.button_height + self.button_gap
#        for (title, action) in section[label]:
#          btn = self.menu_button(title, action, top_y)
#          self.menu.add_subview(btn)
#          btn.frame=(0, top_y, self.button_width, self.button_height)
#          top_y += self.button_height + self.button_gap
#      else:
#        btn = self.menu_button(label, section[label], top_y)
#        self.menu.add_subview(btn)
#        btn.frame=(0, top_y, self.button_width, self.button_height)
#        top_y += self.button_height + self.button_gap


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
  #v.image = ui.Image.named("underwater.jpg")
  v.image = ui.Image.named("backgrounds/caves.jpg")
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

