"""GLG real-estate sales engine: lead pipeline, unit inventory, site visits, follow-ups and the AI sales assistant.

Everything here reads and writes Postgres through SQLAlchemy; the AI assistant only touches data through the
governed tools in ``app.sales.tools``.
"""
