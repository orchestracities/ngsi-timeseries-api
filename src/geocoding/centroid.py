from numbers import Real
from typing import Sequence
from geojson.utils import coords


def centroid2d(points):
    """
    Calculate the centroid of a finite set of 2D points.

    :param points: the set of points as an iterable. Each point is assumed to
        be a sequence of (at least) two real numbers ``[x, y]``, respectively
        the x (first element) and y coordinate (second element).
    :return: the centroid or ``None`` if the input is empty.
    :raise IndexError: if any point is an empty list.
    :raise TypeError: if the input is ``None`` or a point has a ``None`` coord
        or the coord isn't a number.
    """
    number_of_points = 0
    centroid = [0, 0]

    for p in points:
        centroid = (centroid[0] + p[0], centroid[1] + p[1])
        number_of_points += 1

    centroid = [centroid[0] / number_of_points, centroid[1] /
                number_of_points] if number_of_points else None

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
# NOTE. Typing.
# Should we use complex numbers instead of lists?
#


def is_point(coords_list):
    return coords_list and \
        isinstance(coords_list, Sequence) and \
        len(coords_list) > 1 and \
        isinstance(coords_list[0], Real) and \
        isinstance(coords_list[1], Real)


def best_effort_centroid2d(points):
    """
    Calculate the centroid of the finite set of 2D points found in the input.
    A 2D point is assumed to be a list of at least two numbers, the first
    being the x coordinate and the second the y. This function first filters
    any non-2D point element out of the input and then computes the centroid
    of the remaining set of 2D points if such set isn't empty. If the filtered
    set is empty, then ``None`` is returned.

    :param points: the set of points as an iterable.
    :return: the centroid or ``None`` if it couldn't be computed.
    """
    ps = filter(is_point, points if points else [])
    return centroid2d(ps)


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
    return best_effort_centroid2d(points)
