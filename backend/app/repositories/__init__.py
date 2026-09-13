"""Canonical Data Repositories for GLG Assets.

Centralized source of truth for properties, policies, and contact configurations.
"""
from app.repositories.contact_repository import ContactRepository, contact_repository
from app.repositories.policy_repository import PolicyRepository, policy_repository
from app.repositories.property_repository import PropertyRepository, property_repository

__all__ = [
    "property_repository",
    "PropertyRepository",
    "policy_repository",
    "PolicyRepository",
    "contact_repository",
    "ContactRepository",
]
