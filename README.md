# TiffWrapper

Package wrapping tifffile with utility functions

## Installation

### Github 

```bash
pip install git+https://github.com/FLClab/TiffWrapper.git
```

### From source

```bash
git clone https://github.com/FLClab/TiffWrapper.git
pip install -e TiffWrapper
``` 

## Usage

`tiffwrapper` enables writing of multi-channel tiff files with different look-up tables (LUTs) and ranges for each channel. It also supports writing of composite images with a single LUT and range. `tiffwrapper` also provides a function `make_composite` that generates a composite image from a list of images.

```python
import numpy
import tifffile
import tiffwrapper

from skimage import filters

# Generate some data
data = numpy.random.rand(2, 256, 256)
data[data < 0.99] = 0
for i in range(data.shape[0]):
    data[i] = filters.gaussian(data[i], 4)
data = (data * 100).astype(numpy.float32)

ranges = [(0, 5)]
composite = tiffwrapper.make_composite([data[0]], luts=["magma"], ranges=ranges)
tifffile.imwrite("./composite.tif", composite.astype(numpy.uint8))
```

`tiffwrapper` also provides a function `imwrite` that writes a multi-channel tiff file with different LUTs and ranges for each channel. The function also supports writing of composite images with a single LUT and range.
```python
ranges = [(0, 5), (0, 10), (0, 3)]
file = "./multi-channel.tif"
tiffwrapper.imwrite(file=file, data=data, composite=True, luts=["cyan", "Green Hot", "Red Hot"], ranges=ranges,
        pixelsize=20e-3)
```

`tiffwrapper` also provides a function `imwrite` that writes a single-channel tiff file with a LUT and range.

```python
# Single channel
data = data[0]
file = "./single-channel.tif"
# Both ways can be used
tiffwrapper.imwrite(file=file, data=data, luts="Cyan Hot", ranges=[0, 5])
# imwrite(file=file, data=data, luts=["Cyan Hot"], ranges=[(0, 5)])
```

### N-dimensional data

`tiffwrapper` also supports handling n-dimensional data with the `imwrite` function. The function will automatically handle the data and write it to a tiff file. Optionally, the function can take as input an `axes` parameters specifying the order of the axes in the data. The `axes` parameter is a string with the following characters: `T` (time), `Z` (z), `C` (channel), `Y` (x), `Y` (y). The default value is `TZCYX`. When specifying the `axes` parameter, the `data` parameter should be a numpy array with the same number of dimensions as the `axes` parameter. The order of the `axes` parameter can be any permutation of the default value.

```python
data = numpy.random.rand(10, 5, 2, 256, 256)
imwrite("ndim.tif", data, luts=["red Hot", "Cyan Hot"], ranges=[(0, 1), (0, 0.5)], axes="TZCYX")
```

### Image and masks

`tiffwrapper` also provides ways to combine and image with a mask (possibly multi-channel).

```python
cmaps = [
    "#ff0000", (1.0, 1.0, 0.0)
]
imwrite("composite.tif", mask, composite=True, luts=cmaps, ranges=[(0, 1) for _ in range(mask.shape[0])])
```

Optionally, when the number of masks is large (>8, Fiji only allows for 8 channels in composite) it is possible to directly generate the composite image from the masks and an input image.

```python
stack = numpy.concatenate([image, mask], axis=0)
cmaps = ["gray"] + cmaps
ranges = [(image.min(), numpy.quantile(image, 0.99))] + [(0, 1.0) for _ in range(mask.shape[0])]
composite = make_composite(stack, luts=cmaps, ranges=ranges)

tifffile.imwrite("composite-rgb.tif", composite)
```