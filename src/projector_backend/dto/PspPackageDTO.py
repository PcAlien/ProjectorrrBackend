import json
from datetime import datetime

from src.projector_backend.entities.PspPackage import PspPackage
from src.projector_backend.helpers import data_helper


class PspPackageDTO:
    package_identifier: str
    psp: str
    package_name: str
    package_description: str
    volume: float
    tickets_identifier: [str]

    def __init__(self, psp: str, package_name: str, package_description: str, volume: float, tickets_identifier: [str] or str,
                 package_identifier: str = "00000", ) -> None:
        self.volume = volume
        self.package_name = package_name
        self.psp = psp
        self.package_identifier = package_identifier
        self.package_description = package_description
        if type(tickets_identifier) == str:
            self.tickets_identifier = json.loads(tickets_identifier)
        else:
            self.tickets_identifier = tickets_identifier
    @classmethod
    def create_from_db(cls, pspp_dto: PspPackage):
        return cls(pspp_dto.psp, pspp_dto.package_name, pspp_dto.package_description,pspp_dto.volumen, pspp_dto.tickets_identifier, pspp_dto.package_identifier)
