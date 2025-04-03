
import numpy
import os
import glob
import matplotlib
import Levenshtein

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
                         OR A `tuple` of the RGB values
                         OR A `string` of the HEX value

        :returns : A `numpy.ndarray` with shape (3, 256) of the look up table
        """
        # We allow the user to specify the colormap as a HEX string or a RGB tuple
        if (isinstance(lut_name, str) and lut_name.startswith("#")) or (isinstance(lut_name, tuple)) :
            cmap = matplotlib.colors.LinearSegmentedColormap.from_list("custom", ["black", lut_name], N=2**8)
            lut = (cmap(numpy.arange(2 ** 8))[:, :3].T * self.val_range.max()).astype(self._dtype)
            return lut
        
        if lut_name not in self.PYPLOT_CMAPS and lut_name not in self.USER_CMAPS and lut_name not in self.FIJI_CMAPS:
            # Find the closest match in the available colormaps
            closest_matches = list(sorted(self.PYPLOT_CMAPS + self.USER_CMAPS + list(self.FIJI_CMAPS.keys()), key=lambda x: Levenshtein.distance(lut_name, x)))
            top_matches = ["'{}'".format(match) for match in closest_matches[:5]]
            raise ValueError(f"'{lut_name}' is not a valid colormap. Did you mean one of these? [{', '.join(top_matches)}]")

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
