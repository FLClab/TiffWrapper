
import numpy

from tiffwrapper.luts import FijiLUTsConverter, ColorMapper

DEFAULT_AXES_ORDER = "TZCYX"

def reorder_axes(data, metadata):
    """
    Reorders the axes of the data. This is required because the axes order
    in the metadata is not the same as the order in the data.
    The axes order in the metadata is updated inplace to match the 
    requirements of the data.

    :param data: A `numpy.ndarray` of data
    :param metadata: A `dict` of metadata

    :returns : A `numpy.ndarray` of data
    """
    order = []
    for axis in DEFAULT_AXES_ORDER:
        idx = metadata["axes"].find(axis)
        if idx >= 0:
            order.append(idx)
    metadata["axes"] = "".join([metadata["axes"][i] for i in order])
    return data.transpose(order)

def get_axes(data):
    """
    Returns the axes of the data

    :param data: A `numpy.ndarray` of data

    :returns : A `str` of the axes
    """
    ndim = data.ndim
    if ndim < 6:
        return DEFAULT_AXES_ORDER[-1 * ndim:]
    raise ValueError("Data has an unsupported number of dimensions")

def get_default_metadata(data, metadata, kwargs):
    """
    Returns the default metadata for the data

    :param data: A `numpy.ndarray` of data
    :param metadata: A `dict` of metadata
    :param kwargs: A `dict` of keyword arguments

    :returns : A `dict` of metadata
               A `list` of extratags
    """
    if metadata is None:
        metadata = {}
    extratags = []

    # Handles axes
    axes = kwargs.pop("axes", None)
    if axes is None:
        axes = get_axes(data)
    assert len(axes) == data.ndim, f"Axes `{axes}` do not match the data shape {data.shape}"
    metadata["axes"] = axes.upper()

    return metadata, extratags

def make_composite(ary, luts, ranges=None):
    """
    Makes a composite from a `numpy.ndarray` using the luts. This 
    function will only work on 3D `numpy.ndarray` with shape (C, H, W).

    :param ary: A 3D `numpy.ndarray`
    :param luts: A list of look up tables
    :param ranges: The dynamic range of the image

    :returns : A 3D `numpy.nadrray` with shape (H, W, C)
    """
    cmapper = ColorMapper() # Creation of the ColorMapper instance
    if isinstance(ranges, (type(None))): # Creates drange if not given
        ranges = [(m, M) for m, M in zip(ary.min(axis=(-2, -1)), ary.max(axis=(-2, -1)))]
    else:
        assert len(ranges) == len(ary), "drange should be the same length as img.shape[0]"

    # Scales intensity according to drange
    ary = scale_intensity(ary, ranges) * 255
    ary = ary.astype(numpy.uint8)

    layers = []
    for arr, lut in zip(ary, luts):
        layer = cmapper[lut].T[arr]
        layers.append(layer)
    return numpy.clip(numpy.sum(layers, axis=0), 0, 255).astype(numpy.uint8)

def scale_intensity(image, ranges):
    """
    Scales intensity of an image

    :param image: A `numpy.ndarray` of image data
    :param ranges: A `list` of (min, max) value to scale the image to

    :returns : A `numpy.ndarray` of the rescaled intensity in range [0, 1]
    """
    ranges = numpy.array(ranges)

    m, M = ranges.T
    if numpy.all(m == M):
        return image / (M[:, numpy.newaxis, numpy.newaxis] + 1e-6)
    scaled = (image - m[:, numpy.newaxis, numpy.newaxis]) / (M - m)[:, numpy.newaxis, numpy.newaxis]
    return numpy.clip(scaled, 0, 1)