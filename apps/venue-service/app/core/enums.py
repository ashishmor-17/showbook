from enum import Enum

class ShowtimeStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    OPEN = "OPEN"
    SOLD_OUT = "SOLD_OUT"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class SeatStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"
