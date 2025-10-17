import colour
import numpy as np


class NearestNeighbourInterpolator(colour.KernelInterpolator):
    def __init__(self, *args, **kwargs):
        kwargs["kernel"] = colour.kernel_nearest_neighbour
        super(NearestNeighbourInterpolator, self).__init__(*args, **kwargs)


def generate_square_waves(samples):
    square_waves = []
    square_waves_basis = np.tril(np.ones((samples, samples)))[0:-1, :]
    for i in range(samples):
        square_waves.append(np.roll(square_waves_basis, i))
    return np.vstack(
        (np.zeros(samples), np.vstack(square_waves), np.ones(samples))
    )


def XYZ_outer_surface(samples):
    XYZ = []
    wavelengths = np.linspace(360, 780, samples)

    for wave in generate_square_waves(samples):
        spd = colour.SpectralPowerDistribution(wave, wavelengths).align(
            colour.DEFAULT_SPECTRAL_SHAPE,
            interpolator=NearestNeighbourInterpolator,
        )
        XYZ.append(colour.spectral_to_XYZ(spd))
    return XYZ
