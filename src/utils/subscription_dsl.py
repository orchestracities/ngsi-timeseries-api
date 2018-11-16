from utils.kvt import node, forest, mforest


def subscription(*children):
    return mforest(*children)


def description(value):
    return node('description', value)


def subject(*children):
    return node('subject', mforest(*children))


def entities(*children):
    return node('entities', forest(*children))


def entity(*children):
    return mforest(*children)


def entity_type(etype):
    return node('type', etype if etype else None)


def entity_id(eid, id_pattern):  # TODO: rather add choice operator to KVTree?
    if eid:
        return node('id', str(eid))
    else:
        return node('idPattern', id_pattern if id_pattern else '.*')


def condition(*children):
    return node('condition', mforest(*children))


def attrs(csv):
    return node('attrs', csv.split(',') if csv else None)


def notification(*children):
    return node('notification', mforest(*children))


def url(value):
    return node('http', mforest(node('url', value)))


def metadata(value):
    return node('metadata', value)


def throttling(value):
    return node('throttling', value if value else 1)
