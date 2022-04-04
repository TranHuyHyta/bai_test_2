import enum

class TypeEnumAccount(enum.Enum):
    Merchant = "merchant"
    Personal = "personal"
    Issuer = "issuer"

class TypeEnumTransaction(enum.Enum):
    Initialized = "initialized"
    Confirmed = "confirmed"
    Verified = "verified"
    Completed = "completed"
    Expired = "Expired"
    Canceled = "canceled"
    Failed = "Failed"