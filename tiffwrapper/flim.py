
import numpy
import tifffile
import matplotlib
import numpy
from scipy import ndimage
from matplotlib import pyplot, colors

from tiffwrapper.luts import ColorMapper

def mean_filter(array, footprint=(3,3)):
    """
    Smooths an `numpy.ndarray` by applying a mean filter

    :param ary: A `numpy.ndarray`
    :param footprint: A `tuple` of the mean filter size
    """
    kernel = numpy.ones(footprint)
    return ndimage.convolve(array, kernel) / kernel.sum()

class LifetimeOverlayer:
    """
    Creates a `LifetimeOverlayer`. This allows a user to map a lifetime image
    with an intensity image. At each position, the color is weighted by its
    intensity in an intensity image.
    """
    def __init__(self, lifetime, intensity=None, cname="rainbow"):
        """
        Instantiates the `LifetimeOverlayer`

        :param lifetime: A 2D `numpy.ndarray` of the lifetime
        :param intensity: A 2D/3D `numpy.ndarray` of the intensity image
        :param cname: A `str` of the colormap name
        """
        self.lifetime = lifetime
        if isinstance(intensity, type(None)):
            intensity = numpy.ones_like(self.lifetime)
        else:
            intensity = intensity
        self.intensity = self.verify_intensity(intensity)
        self.cname = cname

    def get_overlay(self, lifetime_minmax=(0., 5.), intensity_minmax=None):
        """
        Computes the lifetime overlay

        :param lifetime_minmax: A `tuple` of the lifetime minimum and maximum
        :param intensity_minmax: A `tuple` of the intensity minimum and maxium

        :returns : A `numpy.ndarray` of the weighted colors
        """
        # Normalize intensity image
        if isinstance(intensity_minmax, type(None)):
            intensity_minmax = (self.intensity.min(), self.intensity.max())
        _min, _max = intensity_minmax
        intensity = numpy.clip(
            (self.intensity - _min) / (_max - _min), 0, 1
        )

        # Normalize lifetime image
        _min, _max = lifetime_minmax
        norm = colors.Normalize(vmin=_min, vmax=_max)

        colormap = colors.LinearSegmentedColormap.from_list(
            None, ColorMapper()[self.cname].T / 255.
        )
        cmap = matplotlib.cm.ScalarMappable(norm, colormap)
        lifetime_rgb = cmap.to_rgba(self.lifetime)[:, :, :3]

        # Convert to hsv and applies intensity mapping
        lifetime_hsv = colors.rgb_to_hsv(lifetime_rgb)
        lifetime_hsv[:, :, -1] = intensity

        lifetime_rgb = colors.hsv_to_rgb(lifetime_hsv)
        return lifetime_rgb, cmap
    
    def get_overlay_RGB(self, lifetime_minmax=(0., 5.), intensity_minmax=(0., 1.)):
        """
        Computes the fraction map overlay on the instensity. 
        Fraction map given as
        :param self.lifetime : 3 channel image (R,G,B) where each channel is the fraction of the lifetime in the corresponding channel

        :param lifetime_minmax: A `tuple` of the lifetime minimum and maximum
        :param intensity_minmax: A `tuple` of the intensity minimum and maxium

        :returns : A `numpy.ndarray` of the weighted colors
        """
        # Normalize intensity image
        _min, _max = intensity_minmax
        intensity = numpy.clip(
            (self.intensity - _min) / (_max - _min), 0, 1
        )
    
        # Normalize lifetime image
        _min, _max = lifetime_minmax
        norm = colors.Normalize(vmin=_min, vmax=_max)
       

        red=self.lifetime[:,:,1]+self.lifetime[:,:,2]
        green=self.lifetime[:,:,0]+self.lifetime[:,:,2]
        blue=self.lifetime[:,:,1]+self.lifetime[:,:,0]
        
        lifetime_rgb =numpy.dstack((red,green,blue))
        lifetime_rgb=numpy.where(lifetime_rgb>1, 1,lifetime_rgb)

        # Convert to hsv and applies intensity mapping
        lifetime_hsv = colors.rgb_to_hsv(lifetime_rgb)
        lifetime_hsv[:, :, -1] = intensity

        lifetime_rgb = colors.hsv_to_rgb(lifetime_hsv)
        return lifetime_rgb
    
    def verify_intensity(self, intensity):
        """
        Ensures that the intensity minimum value is 0.

        :param intensity: A `numpy.ndarray` of the intensity

        :returns : A `numpy.ndarray` of the intensity map
        """
        assert intensity.ndim == 2, f"Intensity image should be 2D, but given `{intensity.shape}`"
        if intensity.min() == 0:
            return intensity
        #elif intensity.dtype == numpy.float8:
        #    return intensity - 2**8 / 2
        elif intensity.dtype == numpy.float16:
            return intensity - 2**16 / 2
        elif intensity.dtype == numpy.float32:
            return intensity - 2**32 / 2
        else:
            return intensity

if __name__ == "__main__":

    import os

    from matplotlib.widgets import Slider, Button

    lifetime = tifffile.imread("../data/Tubuline_STAR635p-Bassoon_ATTO647N-2_10_30percentSTED__BiIntensity.tiff")
    intensity = tifffile.imread("../data/Tubuline_STAR635p-Bassoon_ATTO647N-2_10_30percentSTED_MixedIntensity.tiff")

    lifetime_init, intensity_init = 0.7, 0.55
    overlayer = LifetimeOverlayer(lifetime, intensity/intensity.max(), cname="CET-I3")
    lifetime_rgb, cmap = overlayer.get_overlay(
        lifetime_minmax=(0, lifetime_init),
        intensity_minmax=(0., intensity_init)
    )

    fig, ax = pyplot.subplots()
    ax.imshow(lifetime_rgb)
    # cbar = pyplot.colorbar(cmap, ax=ax)
    # cbar.set_label("Lifetime (ns)")

    # adjust the main plot to make room for the sliders
    fig.subplots_adjust(left=0.25, bottom=0.25, right=0.85)

    # Make a horizontal slider to control the frequency.
    lifetime_ax = fig.add_axes([0.25, 0.1, 0.65, 0.03])
    lifetime_slider = Slider(
        ax=lifetime_ax,
        label="Lifetime",
        valmin=0.,
        valmax=5.0,
        valinit=0.5,
    )

    # Make a vertically oriented slider to control the amplitude
    intensity_ax = fig.add_axes([0.1, 0.25, 0.0225, 0.63])
    intensity_slider = Slider(
        ax=intensity_ax,
        label="Intensity",
        valmin=0.0,
        valmax=1.0,
        valinit=0.5,
        orientation="vertical"
    )

    # Colorbar ax
    cbarax = fig.add_axes([0.9, 0.25, 0.0225, 0.63])
    cbar = pyplot.colorbar(cmap, cax=cbarax)
    cbar.set_label("Lifetime (ns)")

    # The function to be called anytime a slider's value changes
    def update(val):
        global cbar
        lifetime_rgb, cmap = overlayer.get_overlay(
            lifetime_minmax=(0, lifetime_slider.val),
            intensity_minmax=(0., intensity_slider.val)
        )
        ax.clear()
        ax.imshow(lifetime_rgb)
        cbar = pyplot.colorbar(cmap, cax=cbarax)
        cbar.set_label("Lifetime (ns)")
        fig.canvas.draw_idle()

    # register the update function with each slider
    lifetime_slider.on_changed(update)
    intensity_slider.on_changed(update)

    pyplot.show()
