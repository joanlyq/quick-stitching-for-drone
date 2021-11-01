# Quick Stitching drone images
A small project aims to georeference drone images and overlay them together without using orthorectify and feature detection (i.e. tie key points)

So far the tool involves [GDAL](https://gdal.org/) and [numpy](https://numpy.org/). The output is a merged tiff with all drone images after being georeferenced. Individual georeferenced drone images are also part of the output.

The next step is to speed up the whole process (skip the producing individual georeferenced images, and parallel the tiff merging steps if possible).  
