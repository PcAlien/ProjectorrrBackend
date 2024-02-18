import json
import random
import string

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.projector_backend.entities.Base import Base
from src.projector_backend.helpers import data_helper


class PspPackage(Base):
    __tablename__ = "PspPackages"
    id: Mapped[int] = mapped_column(primary_key=True)
    psp: Mapped[str] = mapped_column("psp")
    package_name: Mapped[str] = mapped_column("package_name", String(30))
    package_description: Mapped[str] = mapped_column("package_description", String(400))
    package_identifier: Mapped[str] = mapped_column("package_identifier", String(40))

    tickets_identifier: Mapped[str] = mapped_column("tickets_identifier", String(100))

    volumen: Mapped[float] = mapped_column("volumen")

    def __init__(self, psp: str, package_name: str, package_description: str, volumen: float,
                 tickets_identifier: str or [str],
                 ) -> None:
        self.psp = psp
        self.package_name = package_name
        self.package_description = package_description
        self.package_identifier = self.create_package_identifier()
        if type(tickets_identifier) == list:
            self.tickets_identifier = json.dumps(tickets_identifier, default=data_helper.serialize)
        else:
            self.tickets_identifier = tickets_identifier

        self.volumen = volumen

    def create_package_identifier(self):
        characters = string.ascii_letters + string.digits
        # Wählen Sie zufällige Zeichen aus der Zeichenfolge aus, um den Code zu generieren
        random_code = ''.join(random.choice(characters) for _ in range(30))
        return random_code
