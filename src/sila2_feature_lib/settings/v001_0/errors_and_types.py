class ReloadStoreError(Exception):
    """Error reloading the data store"""

    pass


class RegisterKeyError(Exception):
    """Error registering a key in the data store"""

    pass


class ReadStoreError(Exception):
    """Error reading a key from the data store"""

    pass


class WriteStoreError(Exception):
    """Error writing a key-value pair to the data store"""

    pass
