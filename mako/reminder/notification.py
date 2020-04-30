import logging
import json
from dataclasses import dataclass, asdict
from datetime import datetime

from pytz import utc

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    guild_id: str
    author_id: str
    date: datetime

    def serialize(self):
        hm = asdict(self)
        hm["date"] = hm["date"].astimezone(utc).isoformat()
        return json.dumps(hm)

    @classmethod
    def deserialize(cls, j):
        hm = json.loads(j)
        hm["date"] = datetime.fromisoformat(hm["date"])
        return cls(**hm)
