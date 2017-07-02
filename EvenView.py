# coding: utf-8
import ui

class EvenView(ui.View):

  def __init__(self, *args, horizontal = True, margin = 0, align = 'stretched', **kwargs):
    super().__init__(*args, **kwargs)
    self.horizontal = horizontal
    self.margin = margin
    self.align = align

  def layout(self):
    item_count = len(self.subviews)
    if item_count == 0: return
    if item_count == 1:
      self.subviews[0].center = (self.width/2, self.height/2)
      return

    content_width = 0
    for view in self.subviews:
      content_width += view.width if self.horizontal else view.height
    free_half_per_item = (self.width - 2 * self.margin - content_width)/(item_count - 1)/2

    baseline = self.margin - free_half_per_item
    for view in self.subviews:
      if self.horizontal:
        view.x = baseline + int(free_half_per_item)
        view.y = int((self.height - view.height)/2)
        baseline += 2 * free_half_per_item + view.width
      else:
        view.y = baseline + int(free_half_per_item)
        view.x = int((self.width - view.width)/2)
        baseline += 2 * free_half_per_item + view.height

