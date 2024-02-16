import string
from datetime import datetime
import random
from typing import Any

from sqlalchemy import String, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.projector_backend.entities.Base import Base


class ProjectBundlePSPElement(Base):
    __tablename__ = "project_bundles_psp_elements"
    id: Mapped[int] = mapped_column(primary_key=True)
    psp: Mapped[str] = mapped_column("psp")

    project_bundles_id = Column(Integer, ForeignKey("project_bundles.id"))
    project_bundle = relationship("ProjectBundle", back_populates="bundled_psps", lazy=False)

    def __init__(self, psp:str):
        self.psp = psp



class ProjectBundle(Base):
    __tablename__ = "project_bundles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("name")
    description : Mapped[str] = mapped_column("description")
    identifier : Mapped[str] = mapped_column("identifier")


    bundled_psps = relationship("ProjectBundlePSPElement", back_populates="project_bundle", lazy=False)

    uploadDatum: Mapped[datetime] = mapped_column("uploadDatum")


    def __init__(self, bundle_name: str,description: str, bundled_psps:[ProjectBundlePSPElement]) -> None:
        self.name = bundle_name
        self.description = description

        self.bundled_psps = bundled_psps
        self.identifier = self.create_identifier()
        self.uploadDatum = datetime.now()


    def create_identifier(self):
        characters = string.ascii_letters + string.digits
        # Wählen Sie zufällige Zeichen aus der Zeichenfolge aus, um den Code zu generieren
        random_code = ''.join(random.choice(characters) for _ in range(30))
        return random_code