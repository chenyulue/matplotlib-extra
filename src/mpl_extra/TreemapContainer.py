
from matplotlib.container import Container

class TreemapContainer(Container):
    '''
    Container for the artist of treemap plots.

    The container contains a tuple of the *patches* themselves as well as some
    additoinal attributes.

    Attributes
    ----------
    patches: dict of list of :class:`~matplotlib.patches.Rectangle`
        The artists of the rectangles corresponding to different levels.
    
    texts: dict of list of str
        The artists of the label texts corresponding to different levels.
    
    handles: dict of list of Patches
        The artists of the patch handles corresponding to differnt levels.
        
    mappable: Mappable
        The mappable used in the treemap.
        
    datavalues: None or array-like
        The underlying data values corresponding to the Rectangles.

    '''
    def __init__(self, patches, texts, *, 
                 handles=None, mappable=None,
                 datavalues=None, **kwargs):
        self.patches = patches
        self.texts = texts
        self.handles = handles
        self.mappable = mappable
        self.datavalues = datavalues
        super().__init__(patches, **kwargs)