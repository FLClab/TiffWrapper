
import numpy
import tifffile
import os, glob

from matplotlib import pyplot
from collections.abc import Iterable

from tiffwrapper.luts import FijiLUTsConverter, ColorMapper
from tiffwrapper.utils import get_default_metadata, reorder_axes

def imwrite(file, data, composite=False, luts=None, ranges=None,
            metadata=None, *args, **kwargs):
    """
    Wraps arround the imwrite function of tifffile

    :param file: A `string` of the output file
    :param data: A `numpy.ndarray` to save to the output file with shape (channel, height, width)
    :param composite: Wheter to save a composite image
    :param luts: (optional) If given should be a list of look up tables matching
                 the number of channels
    :param ranges: (optional) If given should be a list tuple of display ranges [(min, max)]
    :param metadata: (optional) A `dict` to parse to the imwrite method. If composite
                     is set True then the `mode` key is overwritten.

    Optional kwargs
    :param resolution: A `float` (or `tuple`) of the pixel size of the image in microns
    :param axes: A `str` of the axes of the data
    """
    # Verifies the data type
    assert data.dtype in [numpy.uint8, numpy.uint16, numpy.float32], "ImageJ does not support {} data type. ".format(data.dtype) + \
            "Here's the list of accepted data type : {}".format([numpy.uint8, numpy.uint16, numpy.float32])

    metadata, extratags = get_default_metadata(data, metadata, kwargs)
    func = get_multi_channel
    if (data.ndim == 2) or (data.shape[0] == 1):
        func = get_single_channel
    metadata, extratags = func(
        data=data, 
        metadata=metadata, 
        extratags=extratags, 
        composite=composite, 
        luts=luts,
        ranges=ranges,
        *args, **kwargs
    )

    # Verifies wheter a pixelsize was given
    pixelsize = kwargs.pop("pixelsize", None)
    if not isinstance(pixelsize, type(None)):
        if isinstance(pixelsize, float):
            # PixelSize is constant in both x,y
            resolution = (1 / pixelsize, ) * 2
        else:
            # Different pixel size in x, y
            resolution = tuple(1 / p for p in pixelsize)
        metadata["unit"] = "um"
    else:
        resolution = (1, ) * 2

    # makes sure the data is valid for ImageJ
    data = reorder_axes(data, metadata)

    # Saves the image to file
    tifffile.imwrite(file, data=data, imagej=True, resolution=resolution, metadata=metadata, extratags=extratags, *args, **kwargs)

def get_single_channel(data, metadata, extratags, luts, ranges, *args, **kwargs):
    """
    Creates the metadata and extratags required to save a single channel image
    in ImageJ that displays as expected

    :param data: A `numpy.ndarray` of data
    :param metadata: A `dict` of metadata
    :param extratags: A `dict` of extratags
    :param luts: A `list` of lookup table names
    :param ranges: A `list` of `tuple` of display range [(min, max)]

    :returns : A `dict` of metadata
               A `dict` of extratags
    """

    # Handles min/max displayed values
    if isinstance(ranges, (tuple, list)):
        ranges = flatten(ranges)
        metadata["min"] = ranges[0]
        metadata["max"] = ranges[1]

    # Handles luts
    if isinstance(luts, str):
        luts = [luts]
    if isinstance(luts, (list, tuple)):
        colormapper = ColorMapper(numpy.uint16)
        extratags = [
            (320, 3, None, colormapper[luts[0]].tobytes(), True)
        ]
    return metadata, extratags

def get_multi_channel(data, metadata, extratags, composite, luts, ranges, *args, **kwargs):
    """
    Creates the metadata and extratags required to save a multi channel image
    in ImageJ that displays as expected

    :param data: A `numpy.ndarray` of data
    :param metadata: A `dict` of metadata
    :param extratags: A `dict` of extratags
    :param composite: A `bool` to indicate if the image is a composite
    :param luts: A `list` of lookup table names
    :param ranges: A `list` of `tuple` of display range [(min, max)]

    :returns : A `dict` of metadata
               A `dict` of extratags
    """

    # If composite adds the mode to the metadata
    if composite:
        metadata["mode"] = "composite"

    # Creates the LUTs in metadata
    channel_axis = metadata["axes"].index("C")
    if isinstance(luts, (list, tuple)):
        assert len(luts) == data.shape[channel_axis], "Shape mismatch between number of channels ({}) and number of luts ({})".format(len(data), len(luts))
        colormapper = ColorMapper()
        metadata["LUTs"] = [colormapper[lut] for lut in luts]

    # Creates the Ranges in metadata
    if isinstance(ranges, (list, tuple)):
        if len(ranges) == 1:
            ranges = [ranges[0] for _ in range(data.shape[channel_axis])]
        assert len(ranges) == data.shape[channel_axis], "Shape mismatch between number of channels ({}) and number of ranges ({})".format(len(data), len(ranges))
        metadata["Ranges"] = [flatten(ranges)]
    return metadata, extratags

imsave = imwrite # Since tifffile uses imwrite by default

def flatten(mappable):
    """
    Helper function to recursively flatten an `Iterable`

    :param mappable: An `Iterable` object

    :returns : A `list` of the flatten `Iterable`
    """
    flattened = []
    for element in mappable:
        if isinstance(element, Iterable):
            flattened.extend(flatten(element))
        else:
            flattened.append(element)
    return flattened

if __name__ == "__main__":

    from skimage import filters

    numpy.random.seed(42)

    # Multi Channel Image
    data = numpy.random.rand(25, 10, 3, 256, 256)
    data[data < 0.99] = 0
    for i in range(data.shape[0]):
        data[i] = filters.gaussian(data[i], 4)
    data = (data * 100).astype(numpy.float32)

    ranges = [(0, 5)]
    composite = make_composite(data, luts=["magma"], ranges=ranges)
    tifffile.imwrite("./composite.tif", composite.astype(numpy.uint8))

    # multi-channel
    ranges = [(0, 5), (0, 10), (0, 3)]
    file = "./multi-channel.tif"
    imwrite(file=file, data=data, composite=True, luts=["cyan", "Green Hot", "Red Hot"], ranges=ranges,
            pixelsize=20e-3, axes="TZCYX")

    # Single channel
    data = data[0]
    file = "./single-channel.tif"
    # Both ways can be used
    imwrite(file=file, data=data, luts="Cyan Hot", ranges=[0, 5])
    # imwrite(file=file, data=data, luts=["Cyan Hot"], ranges=[(0, 5)])
