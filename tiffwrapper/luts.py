
import numpy
import os
import glob
import matplotlib

from matplotlib import pyplot

class ColorMapper(object):
    """
    Class that implements the color mapping of certain colormaps to create a
    look up table that works with ImageJ
    """
    def __init__(self, dtype=numpy.uint8):
        """
        Inits the `ColorMapper` object
        """
        self.PYPLOT_CMAPS = list(matplotlib.colormaps.keys())
        self.USER_CMAPS = [
            'red', 'green', 'blue', 'yellow', 'magenta', 'cyan'
        ]
        self.FIJI_CMAPS = {
            os.path.splitext(os.path.basename(lut))[0] : lut for lut in glob.glob(os.path.join(os.path.dirname(__file__), "LUTs", "*.lut"))
        }

        self._dtype = dtype
        self._dtype_max = numpy.iinfo(dtype).max
        self._dtype_steps = 2 ** 0 if self._dtype == numpy.uint8 else 2 ** 8

        self.val_range = numpy.arange(0, self._dtype_max + 1, self._dtype_steps)

    def __getitem__(self, lut_name):
        """
        Surclasses the `__getitem__` method of an object. Retreives the look up
        table associated to the look up table name

        :param lut_name: A `string` of the look up table name

        :returns : A `numpy.ndarray` with shape (3, 256) of the look up table
        """
        assert (lut_name in self.PYPLOT_CMAPS) or (lut_name in self.USER_CMAPS) or (lut_name in self.FIJI_CMAPS),  "The specified colormap `{}` is not supported. ".format(lut_name) + \
                "We modifed it to be grey. Here's the list of supported look up tables.\n" + \
                "pyplot colormaps : {}\nuser colormaps : {}\nFIJI colormaps : {}".format(self.PYPLOT_CMAPS, self.USER_CMAPS, self.FIJI_CMAPS)
        if lut_name in self.FIJI_CMAPS:
            lut_name = self.FIJI_CMAPS[lut_name]
            lut = FijiLUTsConverter(self._dtype, self._dtype_max + 1).get_cmap(lut_name)
        elif lut_name in self.PYPLOT_CMAPS:
            cmap = pyplot.get_cmap(lut_name)
            lut = (cmap(numpy.arange(2 ** 8))[:, :3].T * self.val_range.max()).astype(self._dtype) # We do not keep the alpha channel
        elif lut_name in self.USER_CMAPS:
            lut = getattr(self, f"_{lut_name}")()
        return lut

    def _red(self):
        """
        Red lut
        """
        lut = numpy.zeros((3, 256), dtype=self._dtype)
        lut[0, :] = self.val_range
        return lut

    def _green(self):
        """
        Green lut
        """
        lut = numpy.zeros((3, 256), dtype=self._dtype)
        lut[1, :] = self.val_range
        return lut

    def _blue(self):
        """
        Blue lut
        """
        lut = numpy.zeros((3, 256), dtype=self._dtype)
        lut[2, :] = self.val_range
        return lut

    def _yellow(self):
        """
        Yellow lut
        """
        lut = numpy.zeros((3, 256), dtype=self._dtype)
        lut[[0, 1], :] = self.val_range
        return lut

    def _magenta(self):
        """
        Magenta lut
        """
        lut = numpy.zeros((3, 256), dtype=self._dtype)
        lut[[0, 2], :] = self.val_range
        return lut

    def _cyan(self):
        """
        Cyan lut
        """
        lut = numpy.zeros((3, 256), dtype=self._dtype)
        lut[[1, 2], :] = self.val_range
        return lut

class FijiLUTsConverter:
    """
    Implements a `FijiLUTsConverter` that allows a user to load Fiji Look-Up-Tables
    into a `numpy.ndarray`
    """
    def __init__(self, dtype, dtype_max):
        """
        Instantiates a `FijiLUTsConverter`

        :param dtype: A type of the colormap to generate
        """
        self.dtype = dtype
        self.dtype_max = dtype_max

    def get_cmap(self, lut):
        """
        Implements a `method` to extract a `numpy.ndarray` of the colormap

        :parma lut: A `str` of the path of a look-up-table file
        """
        with open(lut, "r") as file:
            luts = [list(map(int, line.rstrip().split(" "))) for line in file.readlines()]
        luts = numpy.array(luts).T
        luts = luts / 256. * self.dtype_max
        return luts.astype(self.dtype)
