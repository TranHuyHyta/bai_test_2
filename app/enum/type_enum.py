import enum

class AccountType(enum.Enum):
    Merchant = "merchant"
    Personal = "personal"
    Issuer = "issuer"

class TransactionType(enum.Enum):
    INITIALIZED = "initialized"
    CONFIRMED = "confirmed"
    VERIFIED = "verified"
    COMPLETED = "completed"
    CANCELED = "canceled"
    EXPIRED = 'expired'
    FAILED = "failed"