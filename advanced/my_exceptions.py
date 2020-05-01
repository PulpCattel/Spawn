class MyException(Exception):
    """
    Base class for custom made exceptions
    """
    pass

class RpcDisabled(MyException):
    """
    Raised when the Wasabi RPC is disabled
    """
    pass

class AlreadyRunning(MyException):
    """
    Raised when Wasabi is already running
    """
    pass

class WalletMissing(MyException):
    """
    Raised when a wallet file is missing
    """
    pass

class WrongCredentials(MyException):
    """
    Raised when the wrong RPC credentials are provided
    """
    pass

class RpcError(MyException):
    """
    Raised when the RPC response includes an error
    """
    pass

class ProcessTimeout(MyException):
    """
    Raised when pexpect timeout
    """
    pass

class WrongPassword(MyException):
    """
    Raised when Wasabi is launched with a wrong password
    """
    pass

class WrongSelection(MyException):
    """
    Raised when the wrong wallet is selected
    """
    pass

class FailedLaunch(MyException):
    """
    Raised when Wasabi doesn't start
    """
    pass
