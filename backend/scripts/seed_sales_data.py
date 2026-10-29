"""Load the sales engine's starting data.

    python scripts/seed_sales_data.py                          # projects + default follow-up sequences
    python scripts/seed_sales_data.py --units-csv units.csv    # also load the unit inventory
    python scripts/seed_sales_data.py --slots "5,6,0,1,2,3@11:00,15:00"   # visit slots: weekdays@times, every project

Projects come from ``CANONICAL_PROPERTIES`` (only missing ones are added). Units are NOT invented: they come only
from a CSV with the columns in ``docs/sales/units_template.csv``. Visit slots are created only when ``--slots`` is
given, because which days and times sales staff can host visits is a business decision.
Weekdays: 0 = Monday … 6 = Sunday (Bangladesh week Sat–Thu = 5,6,0,1,2,3).
"""

import argparse
import asyncio
import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.models import ProjectRecord  # noqa: E402
from app.repositories.property_repository import CANONICAL_PROPERTIES  # noqa: E402
from app.sales import followups, units, visits  # noqa: E402
from app.sales.db import session_scope  # noqa: E402
from app.sales.errors import SalesError  # noqa: E402
from app.sales.models import PropertyUnit  # noqa: E402

INT_FIELDS = ("floor", "bedrooms", "bathrooms", "size_sqft", "list_price_bdt")


async def seed_projects() -> int:
    added = 0
    async with session_scope() as session:
        for prop in CANONICAL_PROPERTIES:
            if await session.get(ProjectRecord, prop["id"]):
                continue
            pricing = prop.get("pricing", {})
            facts = prop.get("facts", {})
            session.add(ProjectRecord(
                project_id=prop["id"],
                name=prop["name"],
                location=prop["location"]["formatted"],
                price=pricing.get("display_en", ""),
                price_val=pricing.get("amount"),
                bedrooms=facts.get("bedrooms"),
                description=prop.get("description", ""),
                features={"amenities": facts.get("amenities", []), "handover_date": facts.get("handover_date")},
            ))
            added += 1
    return added


async def seed_units(path: str, tenant_id: str) -> tuple[int, int, list[str]]:
    created, updated, errors = 0, 0, []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for line_no, row in enumerate(rows, start=2):
        fields = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items() if v not in (None, "")}
        try:
            for key in INT_FIELDS:
                if key in fields:
                    fields[key] = int(str(fields[key]).replace(",", ""))
            fields.setdefault("status", "AVAILABLE")
            async with session_scope() as session:
                existing = (
                    await session.execute(
                        select(PropertyUnit).where(
                            PropertyUnit.tenant_id == tenant_id,
                            PropertyUnit.project_id == fields["project_id"],
                            PropertyUnit.unit_code == fields["unit_code"],
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    await units.update_unit(session, tenant_id, existing.unit_id, fields, "seed:csv")
                    updated += 1
                else:
                    await units.create_unit(session, tenant_id, fields, "seed:csv")
                    created += 1
        except (KeyError, ValueError, SalesError) as exc:
            errors.append(f"line {line_no}: {exc}")
    return created, updated, errors


async def seed_slots(spec: str, tenant_id: str) -> int:
    days_part, times_part = spec.split("@", 1)
    weekdays = [int(d) for d in days_part.split(",") if d.strip()]
    times = [t.strip() for t in times_part.split(",") if t.strip()]
    created = 0
    async with session_scope() as session:
        existing = {(s["project_id"], s["weekday"], s["start_time"]) for s in await visits.list_slots(session, tenant_id) if s["active"]}
        for project in await units.list_projects(session):
            for day in weekdays:
                for start in times:
                    if (project["project_id"], day, start) in existing:
                        continue
                    await visits.create_slot(session, tenant_id, {"project_id": project["project_id"], "weekday": day, "start_time": start})
                    created += 1
    return created


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tenant", default=settings.default_tenant_id)
    parser.add_argument("--units-csv")
    parser.add_argument("--slots", help='weekdays@times, e.g. "5,6,0,1,2,3@11:00,15:00"')
    args = parser.parse_args()

    print(f"Projects added: {await seed_projects()}")
    async with session_scope() as session:
        created = await followups.install_default_sequences(session, args.tenant)
    print(f"Follow-up sequences added: {len(created)}")
    if args.units_csv:
        created_units, updated_units, errors = await seed_units(args.units_csv, args.tenant)
        print(f"Units created: {created_units}, updated: {updated_units}")
        for err in errors:
            print(f"  skipped {err}")
    if args.slots:
        print(f"Visit slots added: {await seed_slots(args.slots, args.tenant)}")


if __name__ == "__main__":
    asyncio.run(main())
