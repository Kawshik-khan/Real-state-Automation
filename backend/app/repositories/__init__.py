"""Canonical Data Repositories for GLG Assets.

Centralized source of truth for properties, policies, and contact configurations.
"""
from app.repositories.property_repository import property_repository, PropertyRepository
from app.repositories.policy_repository import policy_repository, PolicyRepository
from app.repositories.contact_repository import contact_repository, ContactRepository

__all__ = [
    "property_repository",
    "PropertyRepository",
    "policy_repository",
    "PolicyRepository",
    "contact_repository",
    "ContactRepository",
]
