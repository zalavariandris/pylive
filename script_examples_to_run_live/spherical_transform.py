import numpy as np
import cv2
import matplotlib.pyplot as plt

def lat_long_to_mirrorball(image, x_offset=0, y_offset=0):
    # Take the left half of the image
    image = cv2.resize(image, (256, 256))
    height, width, channels = image.shape

    # Create meshgrid of normalized coordinates
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    X, Y = np.meshgrid(x, y)

    # Calculate spherical coordinates
    R = np.sqrt(X**2 + Y**2)
    phi = R * np.pi  # Latitude
    theta = np.arctan2(Y, X)  # Longitude

    # Convert spherical coordinates to Cartesian
    # Ensure the mapping covers the full sphere
    theta+=x_offset
    phi+=y_offset
    x_sphere = np.sin(phi) * np.cos(theta)
    y_sphere = np.sin(phi) * np.sin(theta)
    z_sphere = np.cos(phi)

    # Map back to image coordinates
    # Use arctan2 to handle the inverse mapping correctly
    longitude = np.arctan2(y_sphere, x_sphere)
    latitude =  np.arcsin(z_sphere)

    # Normalize back to image coordinates
    map_x = ((longitude + np.pi) / (np.pi*2) * (width - 1)).astype(np.float32)
    map_y = ((latitude + np.pi/2) / (np.pi) * (height - 1)).astype(np.float32)

    # Remap the image
    remapped_image = cv2.remap(image, map_x, map_y, 
                                interpolation=cv2.INTER_LINEAR, 
                                borderMode=cv2.BORDER_CONSTANT)

    return image, remapped_image
if __name__ == "__main__":
    # Assuming 'frame' is your input image
    image = frame[:, :frame.shape[1] // 2]
    image = cv2.imread('earth_latlong.jpg')
    print(image.shape)
    image, remapped_image = lat_long_to_mirrorball(image, 0, 0)

    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))
    axes[0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0].set_title('Original Image')
    axes[1].imshow(cv2.cvtColor(remapped_image, cv2.COLOR_BGR2RGB))
    axes[1].set_title('Remapped Mirrorball')
    plt.tight_layout()
    plt.show()