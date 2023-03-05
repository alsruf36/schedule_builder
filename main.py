from PIL import Image, ImageDraw, ImageFont
from collections import namedtuple
from fastapi import FastAPI
import uvicorn
from typing import Any, Dict, AnyStr, List, Union
import base64
from io import BytesIO


def position_tuple(*args):
  Position = namedtuple('Position', ['top', 'right', 'bottom', 'left'])
  if len(args) == 0:
    return Position(0, 0, 0, 0)
  elif len(args) == 1:
    return Position(args[0], args[0], args[0], args[0])
  elif len(args) == 2:
    return Position(args[0], args[1], args[0], args[1])
  elif len(args) == 3:
    return Position(args[0], args[1], args[2], args[1])
  else:
    return Position(args[0], args[1], args[2], args[3])


def draw_table(table,
               header=[],
               font=ImageFont.load_default(),
               cell_pad=(20, 10),
               margin=(10, 10),
               align=None,
               colors={},
               stock=False):
  """
    Draw a table using only Pillow
    table:    an 2d list, must be str
    header:   turple or list, must be str
    font:     an ImageFont object
    cell_pad: padding for cell, (top_bottom, left_right)
    margin:   margin for table, css-like shorthand
    align:    None or list, 'l'/'c'/'r' for left/center/right, length must be the max count of columns
    colors:   dict, as follows
    stock:    bool, set red/green font color for cells start with +/-
    """
  _color = {
    'bg': 'white',
    'cell_bg': 'white',
    'header_bg': 'gray',
    'font': 'black',
    'rowline': 'black',
    'colline': 'black',
    'red': 'red',
    'green': 'green',
  }
  _color.update(colors)
  _margin = position_tuple(*margin)

  table = table.copy()
  if header:
    table.insert(0, header)
  row_max_hei = [0] * len(table)
  col_max_wid = [0] * len(max(table, key=len))
  for i in range(len(table)):
    for j in range(len(table[i])):
      col_max_wid[j] = max(font.getsize(table[i][j])[0], col_max_wid[j])
      row_max_hei[i] = max(font.getsize(table[i][j])[1], row_max_hei[i])
  tab_width = sum(col_max_wid) + len(col_max_wid) * 2 * cell_pad[0]
  tab_heigh = sum(row_max_hei) + len(row_max_hei) * 2 * cell_pad[1]

  tab = Image.new('RGBA', (tab_width + _margin.left + _margin.right,
                           tab_heigh + _margin.top + _margin.bottom),
                  _color['bg'])
  draw = ImageDraw.Draw(tab)

  draw.rectangle([(_margin.left, _margin.top),
                  (_margin.left + tab_width, _margin.top + tab_heigh)],
                 fill=_color['cell_bg'],
                 width=0)
  if header:
    draw.rectangle([(_margin.left, _margin.top),
                    (_margin.left + tab_width,
                     _margin.top + row_max_hei[0] + cell_pad[1] * 2)],
                   fill=_color['header_bg'],
                   width=0)

  top = _margin.top
  for row_h in row_max_hei:
    draw.line([(_margin.left, top), (tab_width + _margin.left, top)],
              fill=_color['rowline'])
    top += row_h + cell_pad[1] * 2
  draw.line([(_margin.left, top), (tab_width + _margin.left, top)],
            fill=_color['rowline'])

  left = _margin.left
  for col_w in col_max_wid:
    draw.line([(left, _margin.top), (left, tab_heigh + _margin.top)],
              fill=_color['colline'])
    left += col_w + cell_pad[0] * 2
  draw.line([(left, _margin.top), (left, tab_heigh + _margin.top)],
            fill=_color['colline'])

  top, left = _margin.top + cell_pad[1], 0
  for i in range(len(table)):
    left = _margin.left + cell_pad[0]
    for j in range(len(table[i])):
      color = _color['font']
      if stock:
        if table[i][j].startswith('+'):
          color = _color['red']
        elif table[i][j].startswith('-'):
          color = _color['green']
      _left = left
      if (align and align[j] == 'c') or (header and i == 0):
        _left += (col_max_wid[j] - font.getsize(table[i][j])[0]) // 2
      elif align and align[j] == 'r':
        _left += col_max_wid[j] - font.getsize(table[i][j])[0]
      draw.text((_left, top), table[i][j], font=font, fill=color)
      left += col_max_wid[j] + cell_pad[0] * 2
    top += row_max_hei[i] + cell_pad[1] * 2

  return tab


JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]

app = FastAPI()
fnt = ImageFont.truetype('./malgun.ttf', 80)


@app.post("/")
async def generate(schedule: JSONStructure = None):
  data = []
  data.append(["시간", "과목", "비고"])

  for i, v in enumerate(schedule[b'schedule']):
    data.append([f"{i+1}교시", v, "                         "])

  d = draw_table(data, font=fnt, align=['c', 'c', 'c'])

  buffered = BytesIO()
  d.save(buffered, format="PNG")
  img_str = base64.b64encode(buffered.getvalue())
  img_str = img_str.decode('utf-8')

  return {'image': img_str}


uvicorn.run(app, port=8080, host="0.0.0.0")