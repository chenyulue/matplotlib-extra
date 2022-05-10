import textwrap
import re

import matplotlib as mpl
import matplotlib.artist as artist
import matplotlib.transforms as trans
import matplotlib.patches as mpatches
import matplotlib.text as mtext
from matplotlib.font_manager import findfont, get_font
from matplotlib.backends.backend_agg import get_hinting_flag

class AutofitText(mtext.Text):
    def __repr__(self):
        return f'AutofitText(({self._x}, {self._y}), {self._width}, {self._height}, {self._origin_text})'
    
    def __init__(
        self, 
        xy, 
        width, height, 
        text='', 
        *,
        pad=0.0, 
        reflow=False, 
        grow=False, 
        max_fontsize=None,
        min_fontsize=None,
        show_rect=False,
        **kwargs):
        """Create a `.AutoFitText` instance at *x*, *y* with the string *text*
        autofitting into the box with the size of *width* x *height*.

        Parameters
        ----------
        xy : (float, float)
            The x, y coordinates
        width : float, 
            The width of the box, which should be positive.
        height : float
            The height of the box, which should be positive.
        text : str, optional
            The string that needs to be auto-fitted, by default ''
        pad : float, a 2-tuple or a 4-tuple, optional
            The surrounding padding in points from the box edges, by default 0.0. A 2-tuple
            of `(padx, pady)` specifies the horizontal and vertical paddings
            respectively, while a 4-tuple of (`padleft, padright, padtop, padbottom)` 
            the padding from the corresponding four edges.
        reflow : bool, optional
            If `True`, then the text will be auto-wrapped to fit into the box, by default False
        grow : bool, optional
            If `True`, then the auto-wrapped text will be as large as possible, by default False.
            This option takes effect only when `wrap = True`.
        max_fontsize : float, optional
            The maximum fontsize in points, by default None. This option makes sure that
            the auto-fitted text won't have a fontsize larger than *max_fontsize*.
        min_fontsize : float, optional
            The minimum fontsize in points, by default None. This option makes sure that 
            the auto-fitted text won't have a fontsize smaller than *min_fontsize*.
        show_rect : bool, optional
            If True, show the box edge for the debug purpose. Default to False, 
            and usually you won't need it to be `True`.
        **kwargs : 
            Additional kwargs are passed to `~matplotlib.text.Text`.
        """ 
        x, y = xy
        super().__init__(x, y, text, **kwargs)
        self._origin_text = text    # Keep the original, unwrapped text
        self._width = width
        self._height = height
        self._pad = pad
        self._reflow = reflow
        self._grow = grow
        self._max_fontsize = max_fontsize
        self._min_fontsize = min_fontsize
        self._show_rect = show_rect
        self._kwargs = kwargs
        self._validate_text()
        
    def _validate_text(self):
        ''' Validate the `.AutoFitText` instance to make sure that *width* and *height* 
        are positive. If reflow = `True`, it only supports the horizontal text object for simplicity.
        '''        
        if self._width < 0 or self._height < 0:
            raise ValueError('`width` and `height` should be a number >= 0.')
        if self._reflow and super().get_rotation():
            raise ValueError('`reflow` option currently only supports the horizontal text object for simplicity.')
        
    @artist.allow_rasterization
    def draw(self, renderer):
        if renderer is not None:
            self._renderer = renderer
        if not self.get_visible():
            return
        if self._origin_text == '' or self._text == '':
            return
        
        transform = self.get_transform()
        
        # Get the width and height of the box in pixels.
        width_in_pixels, height_in_pixels = self._dist2pixels(transform, self._width, self._height)
        
        fontsize = self.get_fontsize()
        # Get the renderer's dpi, otherwise get the default dpi
        dpi = renderer.dpi  # Todo: This only support RendererAgg. Needs to be improved if a different renderer are chosen.
        original_txt = self._origin_text
        # Auto fit the original text
        self._text = original_txt
        
        pad_left, pad_right, pad_top, pad_bottom = self._get_pad(self._pad)
        padleft_in_pixels = renderer.points_to_pixels(pad_left)
        padright_in_pixels = renderer.points_to_pixels(pad_right)
        padtop_in_pixels = renderer.points_to_pixels(pad_top)
        padbottom_in_pixels = renderer.points_to_pixels(pad_bottom)
        width_in_pixels -= padleft_in_pixels + padright_in_pixels
        height_in_pixels -= padtop_in_pixels + padbottom_in_pixels
        
        bbox = self.get_window_extent(renderer, dpi=dpi)
        
        if bbox.width == 0 or bbox.height == 0:     # For empty string case
            adjusted_fontsize = 1
        else:
            adjusted_fontsize = min(fontsize * width_in_pixels / bbox.width,
                                    fontsize * height_in_pixels / bbox.height)
        
        adjusted_fontsize = self._adjust_fontsize(
            adjusted_fontsize,
            self._max_fontsize,
            self._min_fontsize)
        
        if self._reflow:
            # Split the string into English words and CJK single characters
            words = self._split_words(original_txt)
            fontsizes = []
            
            # The wrapped text has at least two lines.
            for line_num in range(2, len(words) + 1):
                adjusted_size_txt = self._get_wrapped_fontsize(
                    original_txt, height_in_pixels, width_in_pixels, 
                    line_num, self._linespacing, dpi, self.get_fontproperties()
                    )
                fontsizes.append(adjusted_size_txt)
            
            if fontsizes:
                # grow = True, the fontsize will be as large as possible    
                if self._grow:
                    adjusted_size, wrap_txt, _ = max(fontsizes, key=lambda x: x[0])
                # grow = False, the text will be as wide as the box
                else:
                    adjusted_size, wrap_txt, _ = min(fontsizes, key=lambda x: x[2])
                
                adjusted_size = self._adjust_fontsize(
                    adjusted_size,
                    self._max_fontsize,
                    self._min_fontsize) 
                # Choose the larger fontsize between the wrapped and unwrapped texts.    
                if adjusted_fontsize < adjusted_size:
                    adjusted_fontsize = adjusted_size
                    self._text = '\n'.join(wrap_txt)
                    
        self._fontproperties.set_size(adjusted_fontsize)
        
        # The box region, only for debug usgage.
        if self._show_rect: 
            # Get the position of the text bounding box in pixels.    
            x0, y0, *_ = self.get_window_extent(renderer).bounds
            
            # Transform the box position into the position in the current coordinates.
            x0, y0 = transform.inverted().transform((x0, y0))
            rect = mpatches.Rectangle(
                (x0, y0), 
                self._width, 
                self._height, 
                fill=False, ls='--', transform=transform)
            rect.draw(renderer)
            self._rect = rect
            
        super().draw(renderer)
            
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        if value != self._width:
            self._width = value
            self.stale = True   # So that the figure will re-render the text.
        
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        if value != self._height:
            self._height = value
            self.stale = True
        
    @property
    def reflow(self):
        return self._reflow
        
    @reflow.setter
    def reflow(self, value):
        if value != self._reflow:
            self._reflow = value
            self.stale = True
        
    @property
    def grow(self):
        return self._grow
    
    @grow.setter
    def grow(self, value):
        if value != self._grow:
            self._grow = value
            self.stale = True
        
    @property
    def max_fontsize(self):
        return self._max_fontsize
    
    @max_fontsize.setter
    def max_fontsize(self, value):
        if value != self._max_fontsize:
            self._max_fontsize = value
            self.stale = True
        
    @property
    def min_fontsize(self):
        return self._min_fontsize
    
    @min_fontsize.setter
    def min_fontsize(self, value):
        if value != self._min_fontsize:
            self._min_fontsize = value
            self.stale = True
        
    @property
    def show_rect(self):
        return self._show_rect
    
    @show_rect.setter
    def show_rect(self, value):
        if value != self._show_rect:
            self._show_rect = value
            self.stale = True
    
    def _get_wrapped_fontsize(self, txt, height, width, n, linespacing, dpi, fontprops):
        words = self._split_words(txt)
        min_length = max(map(len, words))
        # Keep the longest word not to be broken
        wrap_length = max(min_length, len(txt) // n)
        wrap_txt = textwrap.wrap(txt, wrap_length)
        w_fontsize = self._calc_fontsize_from_width(
            wrap_txt, width, dpi, fontprops
            )
        
        h_fontsize = self._calc_fontsize_from_height(
                height, len(wrap_txt), linespacing, dpi
                )
        
        adjusted_fontsize = min(h_fontsize, w_fontsize)
        delta_w = self._get_line_gap_from_boxedge(wrap_txt, adjusted_fontsize, width, dpi, fontprops)
        
        return adjusted_fontsize, wrap_txt, delta_w
    
    def _get_line_gap_from_boxedge(self, lines, fontsize, width, dpi, fontprops):
        '''Get the minimum gap between the wrapped text and the right edge.
        '''
        props = fontprops
        font = get_font(findfont(props))
        font.set_size(fontsize, dpi)
        gaps = []
        for line in lines:
            font.set_text(line, 0, flags=get_hinting_flag())
            w, _ = font.get_width_height()
            w = w / 64.0 # Divide the subpixels
            gaps.append(abs(w - width))
            
        return min(gaps)
    
    def _calc_fontsize_from_width(self, lines, width, dpi, fontprops):
        props = fontprops
        font = get_font(findfont(props))
        font.set_size(props.get_size_in_points(), dpi)
        fontsizes = []
        for line in lines:
            font.set_text(line, 0, flags=get_hinting_flag())
            w, _ = font.get_width_height()
            w = w / 64.0 # Divide the subpixels
            adjusted_size = props.get_size_in_points() * width / w 
            fontsizes.append(adjusted_size)     
        return min(fontsizes)
    
    def _calc_fontsize_from_height(self, height, n, linespacing, dpi):
        h_pixels =  height / (n * linespacing - linespacing + 1)
        return self._pixels2points(dpi, h_pixels)
    
    def _pixels2points(self, dpi, pixels):
        """Convert display units in pixels to points
        """    
        inch_per_point = 1 / 72
        return pixels / dpi / inch_per_point 
        
    def _split_words(self, txt):
        """Split a hybrid sentence with some CJK characters into a list of words,
        keeping the English words not to be broken.
        """
        regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
        matches = re.findall(regex, txt, re.UNICODE)
        return matches
    
    def _adjust_fontsize(self, size, max_size, min_size):
        ''' Make sure the adjusted fontsize is between min_size and max_size.
        '''
        if max_size is not None:
            size = min(max_size, size)
        if min_size is not None:
            size = max(min_size, size)
        return size
        
    def _dist2pixels(self, transform, width, height):
        box = trans.Bbox([[0,0],[width, height]])
        _, _, width_in_pixels, height_in_pixels = box.transformed(transform).bounds
        return width_in_pixels, height_in_pixels
    
    def _get_pad(self, pad):
        ''' Get the padding between the text and the edges.
        '''
        if isinstance(pad, (int, float)):
            pad_left, pad_right, pad_top, pad_bottom = pad, pad, pad, pad
        elif isinstance(pad, tuple) and (len(pad) == 2):
            pad_left, pad_top = pad
            pad_right, pad_bottom = pad
        elif isinstance(pad, tuple) and (len(pad) == 4):
            pad_left, pad_right, pad_top, pad_bottom = pad
        else:
            raise ValueError('`pad` can only be a number, or a tuple of two or four numbers.')
        return pad_left, pad_right, pad_top, pad_bottom
    
    