

class QLError(Exception):
    """
    Error raised in QuantumLeap usage.
    """


class UnsupportedOption(QLError):
    """
    Used to flag usage of an unsupported/invalid option in any of the methods.
    """


class NGSIUsageError(QLError):
    """
    Errors due to wrong NGSI usage.
    """


class AmbiguousNGSIIdError(NGSIUsageError):
    """
    Examples include querying for an entity_id without specifying entity_type
    being entity_id not unique across entity_types.
    """
    def __init__(self, entity_id=''):
        msg = "There are multiple entities with the given entity_id {}. " \
              "Please specify entity_type."
        NGSIUsageError.__init__(self, msg.format(entity_id))

