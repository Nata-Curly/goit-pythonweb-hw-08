from typing import List, Optional

from sqlalchemy import select, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import date, timedelta

from src.database.models import Contact
from src.schemas import ContactBase


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int) -> List[Contact]:
        stmt = select(Contact).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        stmt = select(Contact).filter_by(id=contact_id)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactBase) -> Contact:
        contact = Contact(**body.model_dump(exclude_unset=True))
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactBase
    ) -> Optional[Contact]:
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def get_birthdays(self) -> List[Contact]:
        today = date.today()
        next_week = today + timedelta(days=7)

        stmt = select(Contact).where(
            and_(
                Contact.birth_date.is_not(None),
                or_(
                    and_(
                        extract("month", Contact.birth_date) == today.month,
                        extract("day", Contact.birth_date) >= today.day,
                    ),
                    and_(
                        extract("month", Contact.birth_date) == next_week.month,
                        extract("day", Contact.birth_date) <= next_week.day,
                    ),
                ),
            )
        )

        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()
