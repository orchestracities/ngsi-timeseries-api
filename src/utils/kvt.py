

# lifted from:
# - https://stackoverflow.com/questions/38987
def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class ToDict:
    """
    Conversion to dictionaries.
    """

    def to_dict(self):
        """
        :return: this object's data as a dictionary.
        """
        pass


class KVTree(ToDict):
    """
    A tree of key-value pairs to be converted to a dictionary.
    A node in this tree is either a leaf node (``KVLeaf``) containing a key
    and a plain value or is an inner node containing a key and child nodes
    (a ``KVForest`` or ``KVMergedForest``).
    We say a path on this tree has no content if the value of the path's tip
    node is ``None``.
    Conversion to a dictionary proceeds recursively from the root to the
    leaves, after pruning paths that have no content. Nodes get converted
    as follows:

        leaf(key, value) ~>
                { key: value }

        node(key, forest[t1,...,tn]) ~>
                { key: [ to_dict(t1), ..., to_dict(tn) ] }

        node(key, merged-forest[t1,...,tn]) ~>
                { key: to_dict(t1) + ... + to_dict(tn) }

    where the ``t``s stand for ``KVTree``s and ``+`` is merging of dictionaries
    """
    pass


class KVLeaf(KVTree):
    """
    Leaf node in a ``KVTree``.
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def to_dict(self):
        """
        Convert this node to a dictionary with our key-value pair if
        our value isn't ``None``; otherwise convert to ``None``.
        :return: either a dictionary or ``None``.
        """
        return {self.key: self.value} if self.value is not None else None


class KVNode(KVTree):
    """
    Inner node in a ``KVTree``.
    """

    def __init__(self, key, children):
        self.key = key
        self.children = children

    def to_dict(self):
        """
        Convert this node either to a dictionary with a single key-value or to
        ``None`` depending on whether the child nodes have content. Conversion
        happens as explained in the ``KVTree`` docs.
        :return: either a dictionary or ``None``.
        """
        converted = self.children.to_dict()
        return {self.key: converted} if converted is not None else None


class KVForest(ToDict):
    """
    Forest of ``KVTree``s.
    """

    def __init__(self, kv_trees):
        self.trees = kv_trees

    def to_dict(self):
        """
        Convert this forest to a list of dictionaries by converting each
        tree. Return ``None`` if all trees get converted to ``None``.
        :return: either a list of dictionaries or ``None``.
        """
        child_dicts = [t.to_dict() for t in self.trees]
        pruned = [d for d in child_dicts if d is not None]

        return pruned if pruned else None


class KVMergedForest(KVForest):
    """
    Forest of ``KVTree``s that gets merged into a single dictionary.
    """

    def __init__(self, kv_trees):
        super().__init__(kv_trees)

    def to_dict(self):
        """
        Convert this forest to a dictionary by converting each tree and
        merging them together into a single dictionary. Return ``None``
        if all trees get converted to ``None``.
        :return: either a dictionary or ``None``.
        """
        pruned = super().to_dict()
        return merge_dicts(*pruned) if pruned else None


def node(key, value):
    """
    Create a ``KVTree`` node. The node will be a leaf or inner node depending
    on whether the value is a ``KVForest``.
    :param key: the node key.
    :param value: the node content.
    :return: the new node.
    """
    if isinstance(value, KVForest):
        return KVNode(key, value)
    else:
        return KVLeaf(key, value)


def forest(*trees):
    """
    Create a ``KVForest`` from the given ``KVTree``s.
    :param trees: the trees that make up the forest.
    :return: the forest.
    """
    return KVForest(list(trees))


def mforest(*trees):
    """
    Create a ``KVMergedForest`` from the given ``KVTree``s.
    :param trees: the trees that make up the forest.
    :return: the forest.
    """
    return KVMergedForest(list(trees))
