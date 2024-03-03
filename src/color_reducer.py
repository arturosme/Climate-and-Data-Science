import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

class ColorReducer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = plt.imread(image_path)

    def aggregate_colors(self, method='kmeans', n_colors=8):
        if method == 'kmeans':
            return self._kmeans_clustering(n_colors)
        elif method == 'median_cut':
            n_color_param = int(np.log2(n_colors))
            return self._median_cut_quantize(n_color_param)
        else:
            raise ValueError("Invalid method. Available methods: 'kmeans', 'median_cut'")

    def _kmeans_clustering(self, n_colors):
        # Reshape the image data to fit KMeans input
        h, w, d = self.image.shape
        reshaped_image = self.image.reshape(h * w, d)

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=n_colors, random_state=42)
        kmeans.fit(reshaped_image)
        labels = kmeans.predict(reshaped_image)
        centers = kmeans.cluster_centers_

        # Assign each pixel to its cluster center
        clustered_image = np.zeros_like(reshaped_image)
        for i in range(n_colors):
            clustered_image[labels == i] = centers[i]

        return clustered_image.reshape(h, w, d)

    def _median_cut_quantize(self, n_colors):
        # Initialize sample_img array
        sample_img = self.image.copy()

        # Convert image to flattened array
        flattened_img_array = []
        for rindex, rows in enumerate(sample_img):
            for cindex, color in enumerate(rows):
                flattened_img_array.append([color[0], color[1], color[2], rindex, cindex])
        flattened_img_array = np.array(flattened_img_array)

        # Split into buckets using median cut algorithm
        self._split_into_buckets(sample_img, flattened_img_array, n_colors)

        return sample_img

    def _split_into_buckets(self, img, img_arr, depth):
        if len(img_arr) == 0:
            return
        if depth == 0:
            self._median_cut_quantize_helper(img, img_arr)
            return

        # Calculate color ranges
        r_range = np.max(img_arr[:, 0]) - np.min(img_arr[:, 0])
        g_range = np.max(img_arr[:, 1]) - np.min(img_arr[:, 1])
        b_range = np.max(img_arr[:, 2]) - np.min(img_arr[:, 2])

        # Determine the color space with the highest range
        space_with_highest_range = np.argmax([r_range, g_range, b_range])

        # Sort the image pixels by color space with the highest range
        img_arr = img_arr[img_arr[:, space_with_highest_range].argsort()]
        median_index = len(img_arr) // 2

        # Split the array into two buckets along the median
        self._split_into_buckets(img, img_arr[:median_index], depth - 1)
        self._split_into_buckets(img, img_arr[median_index:], depth - 1)

    def _median_cut_quantize_helper(self, img, img_arr):
        r_average = np.mean(img_arr[:, 0])
        g_average = np.mean(img_arr[:, 1])
        b_average = np.mean(img_arr[:, 2])

        for data in img_arr:
            img[data[3]][data[4]] = [r_average, g_average, b_average]

    def plot_image(self, image_data, title):
        plt.imshow(image_data)
        plt.title(title)
        plt.axis('off')
        plt.show()
