import textwrap
import re

import matplotlib as mpl
import matplotlib.patches as mpatches
import matplotlib.text as mtext
from matplotlib.font_manager import findfont, get_font
from matplotlib.backends.backend_agg import get_hinting_flag


class AutoFitText(mtext.Text):
    def __repr__(self):
        return f'AutoFitText(({self._x}, {self._y}), {self._width}, {self._height}, {self._origin_text})'
    
    def __init__(
        self, 
        x, y, 
        width, height, 
        text='', 
        *,
        pad=0.0, 
        wrap=False, 
        grow=False, 
        max_fontsize=None,
        min_fontsize=None,
        show_rect=False,
        **kwargs):
        """Create a `.AutoFitText` instance at *x*, *y* with the string *text*
        autofitting into the box with the size of *width* x *height*.

        Parameters
        ----------
        x : float
            The x coordinates
        y : float
            The y coordinates
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
        wrap : bool, optional
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
        super().__init__(x, y, text, **kwargs)
        self._origin_text = text    # Keep the original, unwrapped text
        self._width = width
        self._height = height
        self._pad = pad
        self._wrap = wrap
        self._grow = grow
        self._max_fontsize = max_fontsize
        self._min_fontsize = min_fontsize
        self._show_rect = show_rect
        self._kwargs = kwargs
        self._validate_text()
        
    def _validate_text(self):
        ''' Validate the `.AutoFitText` instance to make sure that *width* and *height* 
        are positive. If wrap = `True`, it only supports the horizontal text object for simplicity.
        '''        
        if self._width < 0 or self._height < 0:
            raise ValueError('`width` and `height` should be a number >= 0.')
        if self._wrap and super().get_rotation():
            raise ValueError('`wrap` option currently only supports the horizontal text object.')
        
    def __call__(self, event):
        ''' An `.AutoFitText` instance is callable when some events, such 
        as *draw_event*, *resize_event* etc, happens. This is used to update 
        the `.AutoFitText` instance.
        '''
        # todo: This callback needs to be improved and be more efficient.
        text_with_autofit(
            self, self._width, self._height,
            pad=self._pad,
            wrap=self._wrap,
            grow=self._grow,
            max_fontsize=self._max_fontsize,
            min_fontsize=self._min_fontsize,
            transform=self.get_transform(),
            show_rect=self._show_rect)
    
    def auto_fit(self, axes):
        """Auto-fit the instance into the axes

        Parameters
        ----------
        axes : Axes
            The axes where the text will be drawn

        Returns
        -------
        The instance of `.AutoFitText` with the text auto-fitted into the box.
        """        
        txtobj = axes.add_artist(self)
        
        ##### todo: draw_event Interactive needs to be improved and be more efficient.       
        self._cid = axes.get_figure().canvas.mpl_connect('draw_event', self)
        #axes.get_figure().canvas.mpl_connect('resize_event', self)
        
        return txtobj
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        self._width = value
        self.stale = True   # So that the figure will re-render the text.
        
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        self._height = value
        self.stale = True
        
    @property
    def wrap(self):
        return self._wrap
        
    @wrap.setter
    def wrap(self, value):
        self._wrap = value
        self.stale = True
        
    @property
    def grow(self):
        return self._grow
    
    @grow.setter
    def grow(self, value):
        self._grow = value
        self.stale = True
        
    @property
    def max_fontsize(self):
        return self._max_fontsize
    
    @max_fontsize.setter
    def max_fontsize(self, value):
        self._max_fontsize = value
        self.stale = True
        
    @property
    def min_fontsize(self):
        return self._min_fontsize
    
    @min_fontsize.setter
    def min_fontsize(self, value):
        self._min_fontsize = value
        self.stale = True



def text_with_autofit(
    txtobj,
    width, 
    height,
    *,
    pad=0.0,
    wrap=False,
    grow=False,
    max_fontsize=None,
    min_fontsize=None,
    transform=None,
    show_rect=False,
):
    """Auto fitting the text object into a box of width x height by adjusting
    the fontsize automaticaly.

    Parameters
    ----------
    txtobj : Text 
        The Text object to be auto-fitted.
    width : float
        The width of the box, which should be positive.
    height : float
        The height of the box, which should be positive.
    pad : float, a 2-tuple or a 4-tuple, optional
        The surrounding padding in points from the box edges, by default 0.0. A 2-tuple
        of `(padx, pady)` specifies the horizontal and vertical paddings
        respectively, while a 4-tuple of (`padleft, padright, padtop, padbottom)` 
        the padding from the corresponding four edges.
    wrap : bool, optional
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
    transform : Transform, optional
        The transformer for the width and height. When default to None, 
        it takes the transformer of txtobj.
    show_rect : bool, optional
        If True, show the box edge for the debug purpose. Default to False.
        
    Returns
    -------
    Text or (Text, Rectangle)
        The auto-fitted Text object. If show_rect = True, the Rectangle box will
        also be returned.
    """
    if width < 0 or height < 0:
        raise ValueError('`width` and `height` should be a number >= 0.')
    
    if wrap and txtobj.get_rotation():
        raise ValueError('`wrap` option only supports the horizontal text object.')

    if transform is None:
        # The default transformer is same as the textobj.
        transform = txtobj.get_transform()
    
    # Get the width and height of the box in pixels.
    width_in_pixels, height_in_pixels = dist2pixels(transform, width, height)
    
    render = txtobj.axes.get_figure().canvas.get_renderer()
    fontsize = mpl.rcParams['font.size']  # txtobj.get_fontsize()
    dpi = txtobj.axes.get_figure().get_dpi()
    try:
        # Update always autofit the original text, used with AutoFitText instance.
        original_txt = txtobj._origin_text  
    except AttributeError:
        # Works with the default Text instance.
        original_txt = txtobj.get_text()     
    
    pad_left, pad_right, pad_top, pad_bottom = get_pad(pad)
    padleft_in_pixels = render.points_to_pixels(pad_left)
    padright_in_pixels = render.points_to_pixels(pad_right)
    padtop_in_pixels = render.points_to_pixels(pad_top)
    padbottom_in_pixels = render.points_to_pixels(pad_bottom)
    width_in_pixels -= padleft_in_pixels + padright_in_pixels
    height_in_pixels -= padtop_in_pixels + padbottom_in_pixels
    
    bbox = txtobj.get_window_extent(render)
    
    if bbox.width == 0 or bbox.height == 0:     # For empty string case
        adjusted_fontsize = 1
    else:
        adjusted_fontsize = min(fontsize * width_in_pixels / bbox.width,
                                fontsize * height_in_pixels / bbox.height)
    adjusted_fontsize = adjust_fontsize(adjusted_fontsize,
                                        max_fontsize,
                                        min_fontsize) 
    
    if wrap:
        # Split the string into English words and CJK single characters
        words = split_words(original_txt)
        fontsizes = []
        
        # The wrapped text has at least two lines.
        for line_num in range(2, len(words) + 1):
            adjusted_size_txt = get_wrapped_fontsize(
                original_txt, height_in_pixels, width_in_pixels, 
                line_num, txtobj._linespacing, dpi, txtobj.get_fontproperties()
                )
            fontsizes.append(adjusted_size_txt)
        
        if fontsizes:
            # grow = True, the fontsize will be as large as possible    
            if grow:
                adjusted_size, wrap_txt, _ = max(fontsizes, key=lambda x: x[0])
            # grow = False, the text will be as wide as the box
            else:
                adjusted_size, wrap_txt, _ = min(fontsizes, key=lambda x: x[2])
            
            adjusted_size = adjust_fontsize(adjusted_size,
                                            max_fontsize,
                                            min_fontsize) 
            # Choose the larger fontsize between the wrapped and unwrapped texts.    
            if adjusted_fontsize < adjusted_size:
                adjusted_fontsize = adjusted_size
                txtobj.set_text('\n'.join(wrap_txt))
         
    txtobj.set_fontsize(adjusted_fontsize)
    
    # The box region, only for debug usgage.
    if show_rect: 
        # Get the position of the text bounding box in pixels.    
        x0, y0, *_ = txtobj.get_window_extent(render).bounds
        
        # Transform the box position into the position in the current coordinates.
        x0, y0 = transform.inverted().transform((x0, y0))
        
        rect = mpatches.Rectangle(
            (x0, y0), 
            width, 
            height, 
            fill=False, ls='--', transform=transform)
        txtobj.axes.add_patch(rect)
        
        return txtobj, rect
        
    return txtobj


def adjust_fontsize(size, max_size, min_size):
    ''' Make sure the adjusted fontsize is between min_size and max_size.
    '''
    if max_size is not None:
        size = min(max_size, size)
    if min_size is not None:
        size = max(min_size, size)
    return size


def get_pad(pad):
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


def get_wrapped_fontsize(txt, height, width, n, linespacing, dpi, fontprops):
    """Get the fontsize according to the wrapped text, which makes the longest
    line to fit into the box.

    Parameters
    ----------
    txt : str
        A string of text
    height : float
        The height of the box in pixels
    width : float
        The width of the box in pixels
    n : int
        The line numbers
    linespacing : float
        The line spacing between the wrapped text
    dpi : float
        The dpi used to calculate the fontsize.
    fontprops : FontProperties
        The font properties used to calculate the fontsize.

    Returns
    -------
    a tuple of (float, str, float)
        returns a tuple of fontsize, the corresponding wrapped text, and the 
        gap between the wrapped text and the box edge.
    """    
    words = split_words(txt)
    min_length = max(map(len, words))
    # Keep the longest word not to be broken
    wrap_length = max(min_length, len(txt) // n)
    wrap_txt = textwrap.wrap(txt, wrap_length)
    w_fontsize = calc_fontsize_from_width(
        wrap_txt, width, dpi, fontprops
        )
    
    h_fontsize = calc_fontsize_from_height(
            height, len(wrap_txt), linespacing, dpi
            )
    
    adjusted_fontsize = min(h_fontsize, w_fontsize)
    delta_w = get_line_gap_from_boxedge(wrap_txt, adjusted_fontsize, width, dpi, fontprops)
    
    return adjusted_fontsize, wrap_txt, delta_w


def get_line_gap_from_boxedge(lines, fontsize, width, dpi, fontprops):
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
    

def split_words(txt):
    """Split a hybrid sentence with some CJK characters into a list of words,
    keeping the English words not to be broken.

    Parameters
    ----------
    txt : str
        A sentence to be splitted.

    Returns
    -------
    list of str
        a list of splitted words
    """    
    regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
    matches = re.findall(regex, txt, re.UNICODE)
    return matches


def calc_fontsize_from_width(lines, width, dpi, fontprops):
    """Calculate the fontsize according to the ling width

    Parameters
    ----------
    lines : list of str
        A list of lines.
    width : float
        The box width in pixels.
    dpi : float
        The dpi used to calculate the fontsize.
    fontprops : FontProperties
        The font properties used to calculate the fontsize.

    Returns
    -------
    float
        returns the fontsize that fits all the lines into the box.
    """    
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


def calc_fontsize_from_height(height, n, linespacing, dpi):
    """Calculate the fontsize according to the box height and wrapped line numbers.

    Parameters
    ----------
    height : float
        The height of the box
    n : int
        The number of wrapped lines
    linespacing : float
        The line spacing of the text.

    Returns
    -------
    float
        The fontsize
    """    
    h_pixels =  height / (n * linespacing - linespacing + 1)
    
    return pixels2points(dpi, h_pixels)
        
        
def dist2pixels(transform, dist, *dists):
    """Get the distance in pixels for a specific distance with the transformer
    specified by tranform.

    Parameters
    ----------
    transform : Transform
        The transformer to use.
    dist : float
        The distance between two points.
    
    Other Parameters
    ----------------
    *dists: float
    
    Returns
    -------
    list of float, corresponding to the arguments passed into the function.
    """    
    params = (dist,) + dists
    start_point = transform.transform((0,0))
    results = []
    
    for i in range(0, len(params), 2):
        point = params[i:i+2]
        end_point = point + (0,) if len(point) == 1 else point
        end_point = transform.transform(end_point)
        results.extend((end_point - start_point)[:-1] if len(point) == 1 else (end_point - start_point))
         
    return results


def pixels2dist(transform, dist, *dists):
    """The inverse function of dist2pixels.

    Parameters
    ----------
    transform : Transform
        The transformer to use
    dist : float
        The distance in pixels
        
    Other Parameters
    ----------------
    *dists: float
    
    Returns
    -------
    list of float, corresponding to the arguments passed into the function.
    """
    return dist2pixels(transform.inverted(), dist, *dists)


def pixels2points(dpi, pixels):
    """Convert display units in pixels to points

    Parameters
    ----------
    dpi : float
        The figure dpi
    pixels : float
        The pixel numbers

    Returns
    -------
    float
        The points for fontsize, linewidth, etc.
    """    
    inch_per_point = 1 / 72
    return pixels / dpi / inch_per_point  