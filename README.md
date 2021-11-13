# Quick Stitching drone images
A small project aims to georeference drone images and overlay them together without using orthorectify and feature detection (i.e. tie key points)

So far the tool involves [GDAL](https://gdal.org/) and [numpy](https://numpy.org/). The output is a merged tiff with all drone images after being georeferenced. Individual georeferenced drone images are also part of the output.

The next step is to speed up the whole process (skip the producing individual georeferenced images, and parallel the tiff merging steps if possible).  

This project is inspired by [alexhagiopol.orthomosaic](https://github.com/alexhagiopol/orthomosaic)

## Installation (Windows)
1. Clone repository to your local directory: `git clone https://github.com/joanlyq/quick-stitching-for-drone.git`
2. Checkout the Windows branch: `git checkout windows`
3. Change directory to inside repo: `cd quick-stitching-for-drone/`
4. Create conda environment from yml file: `conda create -n environment.yml`
5. Activate the conda environment: `conda activate geonadir`
6. Install additional required dependencies with pip: `pip install -r requirements.txt`
7. Finally, run the code: `python main.py`