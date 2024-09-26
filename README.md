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