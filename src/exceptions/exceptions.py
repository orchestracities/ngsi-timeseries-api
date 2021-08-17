

class QLError(Exception):
    """
    Error raised in QuantumLeap usage.
    """

    def __init__(self, message="Quantum Leap Error"):
        self.message = message
        super().__init__(self.message)


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


class InvalidNGSIEntity(NGSIUsageError):
    """
    Examples include an entity without entity_id or entity_type.
    """

    def __init__(self, entity=None):
        msg = "The entity is not a valid {}. "
        NGSIUsageError.__init__(self, msg.format(entity))


class InvalidParameterValue(QLError):
    """
    Passed parameter value is not valid.
    """

    def __init__(self, par_value='', par_name=''):
        msg = "The parameter value '{}' for parameter {} is not valid."
        QLError.__init__(self, msg.format(par_value, par_name))


class InvalidHeaderValue(QLError):
    """
    Passed parameter value is not valid.
    """

    def __init__(self, header_value='', header_name='', message=''):
        msg = "The header value '{}' for header {} is not valid. {}"
        QLError.__init__(self, msg.format(header_value, header_name, message))
