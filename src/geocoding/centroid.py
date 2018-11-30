from geojson.utils import coords


def centroid2d(points):
    """
    Calculate the centroid of a finite set of 2D points.

    :param points: the set of points as an iterable. It's assumed to contain
        at least one point. Each point is assumed to be a list of exactly two
        numbers ``[x, y]``, respectively the x (first element) and y
        coordinate.
    :return: the centroid.
    :raise ZeroDivisionError: if the input is empty.
    :raise IndexError: if any point is an empty list.
    :raise TypeError: if the input is ``None`` or a point has a ``None`` coord
        or the coord isn't a number.
    """
    number_of_points = 0
    centroid = [0, 0]

    for p in points:
        centroid = (centroid[0] + p[0], centroid[1] + p[1])
        number_of_points += 1
    centroid = [centroid[0]/number_of_points, centroid[1]/number_of_points]

    return centroid
#
# NOTE. Performance.
# This function can compute the centroid of a few thousands points in
# microseconds but runtime goes up to millis on huge input lists---over
# 100,000 points.
# Even though we could use NumPy to bring the runtime back to microseconds on
# huge lists (see e.g. https://stackoverflow.com/questions/23020659), the time
# it takes to convert the input to a NumPy array is about 10 times what this
# function actually takes to compute the result.
#


def maybe_centroid2d(points):
    """
    Same as ``centroid2d`` but returns ``None`` instead of raising an exception
    if the input isn't in the expected format.
    """
    try:
        return centroid2d(points)
    except (ZeroDivisionError, TypeError, IndexError):
        return None


def geojson_centroid(obj):
    """
    Compute the centroid of the set of points that define the shapes in the
    input GeoJSON object.
    :param obj: a GeoJSON object.
    :return: the centroid if it could be calculated or ``None`` if there was
    an error---e.g. the input GeoJSON contains invalid points.
    """
    points = coords(obj)
    return maybe_centroid2d(points)
