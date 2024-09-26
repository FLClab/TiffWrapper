
import numpy
import tifffile
import os, glob

from matplotlib import pyplot
from collections.abc import Iterable

from tiffwrapper.luts import FijiLUTsConverter, ColorMapper

def imwrite(file, data, composite=False, luts=None, ranges=None,
            metadata={}, *args, **kwargs):
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
    """
    # Verifies the data type
    assert data.dtype in [numpy.uint8, numpy.uint16, numpy.float32], "ImageJ does not support {} data type. ".format(data.dtype) + \
            "Here's the list of accepted data type : {}".format([numpy.uint8, numpy.uint16, numpy.float32])

    # Case of single channel image
    if (data.ndim == 2) or (data.shape[0] == 1):
        metadata, extratags = get_single_channel(data, luts, ranges)
    else:
        metadata, extratags = get_multi_channel(data, composite, luts, ranges)

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

    # Saves the image to file
    tifffile.imwrite(file, data=data, imagej=True, resolution=resolution, metadata=metadata, extratags=extratags, *args, **kwargs)

def get_single_channel(data, luts, ranges):
    """
    Creates the metadata and extratags required to save a single channel image
    in ImageJ that displays as expected

    :param luts: A `list` of lookup table names
    :param ranges: A `list` of `tuple` of display range [(min, max)]

    :returns : A `dict` of metadata
               A `dict` of extratags
    """
    metadata, extratags = {}, []

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

def get_multi_channel(data, composite, luts, ranges):
    """
    Creates the metadata and extratags required to save a multi channel image
    in ImageJ that displays as expected

    :param composite: A `bool` wheter the image should be a composite
    :param luts: A `list` of lookup table names
    :param ranges: A `list` of `tuple` of display range [(min, max)]

    :returns : A `dict` of metadata
               A `dict` of extratags
    """
    metadata, extratags = {}, []

    # If composite adds the mode to the metadata
    if composite:
        metadata["mode"] = "composite"

    # Creates the LUTs in metadata
    if isinstance(luts, (list, tuple)):
        assert len(luts) == data.shape[0], "Shape mismatch between number of channels ({}) and number of luts ({})".format(len(data), len(luts))
        colormapper = ColorMapper()
        metadata["LUTs"] = [colormapper[lut] for lut in luts]

    # Creates the Ranges in metadata
    if isinstance(ranges, (list, tuple)):
        if len(ranges) == 1:
            ranges = [ranges[0] for _ in range(data.shape[0])]
        assert len(ranges) == data.shape[0], "Shape mismatch between number of channels ({}) and number of ranges ({})".format(len(data), len(ranges))
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

def make_composite(ary, luts, ranges=None):
    """
    Makes a composite from a `numpy.ndarray` using the luts

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

if __name__ == "__main__":

    from skimage import filters

    numpy.random.seed(42)

    # Multi Channel Image
    data = numpy.random.rand(1, 256, 256)
    data[data < 0.99] = 0
    for i in range(data.shape[0]):
        data[i] = filters.gaussian(data[i], 4)
    data = (data * 100).astype(numpy.float32)

    ranges = [(0, 5)]
    composite = make_composite(data, luts=["magma"], ranges=ranges)
    tifffile.imwrite("./composite.tif", composite.astype(numpy.uint8))

    ranges = [(0, 5), (0, 10), (0, 3)]
    file = "./multi-channel.tif"
    imwrite(file=file, data=data, composite=True, luts=["cyan", "Green Hot", "Red Hot"], ranges=ranges,
            pixelsize=20e-3)

    # Single channel
    data = data[0]
    file = "./single-channel.tif"
    # Both ways can be used
    imwrite(file=file, data=data, luts="Cyan Hot", ranges=[0, 5])
    # imwrite(file=file, data=data, luts=["Cyan Hot"], ranges=[(0, 5)])
