"""Write-through persistence rows for the prayer + prophecy ledgers.

One JSON-document row per ledger record (see `prayer.enable_persistence`).
The in-process dicts in `backend/services/prayer.py` stay the read path;
these rows exist only so a restart/redeploy can rebuild them. Kept as JSON
documents rather than normalized columns because every query happens
in memory — the table is a durability log, not a query surface.
"""
from sqlalchemy import Column, String, Text

from backend.db.connection import Base


class LedgerRecord(Base):
    __tablename__ = "ledger_records"

    kind = Column(String, primary_key=True)      # prayer | intercession | prophecy | policy
    rec_id = Column(String, primary_key=True)    # record id (intercessions get a synthetic one)
    data = Column(Text, nullable=False)          # JSON document of the dataclass
