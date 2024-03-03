"""
Some utilities to plot the result of the exercises.
"""

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from mpl_toolkits.axes_grid1 import ImageGrid


# NDVI colormap

colors = [
    "#0c0c0c",
    "#bfbfbf",
    "#dbdbdb",
    "#eaeaea",
    "#fff9cc",
    "#ede8b5",
    "#ddd89b",
    "#ccc682",
    "#bcb76b",
    "#afc160",
    "#a3cc59",
    "#91bf51",
    "#7fb247",
    "#70a33f",
    "#609635",
    "#4f892d",
    "#3f7c23",
    "#306d1c",
    "#216011",
    "#0f540a",
    "#004400",
    # "#004400",
]

ndvi_ranges = [
    -1,
    -0.5,
    -0.2,
    -0.1,
    0,
    0.025,
    0.05,
    0.075,
    0.1,
    0.125,
    0.15,
    0.175,
    0.2,
    0.25,
    0.3,
    0.35,
    0.4,
    0.45,
    0.5,
    0.55,
    0.6,
    1,
    # 2,
]

# Create the colormap and norm
ndvi_cmap = ListedColormap(colors)
ndvi_norm = BoundaryNorm(ndvi_ranges, ndvi_cmap.N)


def plot_ndvi(tci_image, red_image, nir_image, ndvi_image):

    fig = plt.figure(figsize=(25, 8))
    ax = ImageGrid(fig, 111,
            nrows_ncols = (1,4),
            axes_pad = 0.15,
            cbar_location = "right",
            cbar_mode="single",
            cbar_size="5%",
            cbar_pad=0.05
            )

    title_dict = {"fontsize": 21, "fontweight": "bold"}
    ax[0].imshow(tci_image/255)
    ax[0].set_title("True Color Image", fontdict=title_dict)
    ax[0].axis("off")

    ax[1].imshow(red_image, cmap="Reds")
    ax[1].set_title("Red Band Image", fontdict=title_dict)
    ax[1].axis("off")

    ax[2].imshow(nir_image, cmap="Oranges")
    ax[2].set_title("Near-Infrared Band Image", fontdict=title_dict)
    ax[2].axis("off")

    im = ax[3].imshow(ndvi_image, cmap=ndvi_cmap, norm=ndvi_norm)
    ax[3].set_title("NDVI Image", fontdict=title_dict)
    ax[3].axis("off")

    cb = plt.colorbar(im, cax=ax.cbar_axes[0], ticks=[-1, -0.5, -0.2, -0.1, 0.0, 0.2, 0.6, 1.0])
    cb.set_label(label="NDVI", size=20)
    cb.ax.tick_params(labelsize=15)

    return fig, ax