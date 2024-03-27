from datetime import datetime

from src.projector_backend.dto.PspPackageDTO import PspPackageDTO
from src.projector_backend.entities.projekt import Projekt, ProjektMitarbeiter
from src.projector_backend.services.tempclasses import Ma_Identifier_DTO


class ProjektmitarbeiterDTO(Ma_Identifier_DTO):
    psp_bezeichnung: str
    stundensatz: int
    stundenbudget: int
    laufzeit_von: str
    laufzeit_bis: str
    uploaddatum: datetime


    def __init__(self, personalnummer: str, name: str, psp_bezeichnung: str, psp_element: str, stundensatz: int,
                 stundenbudget: int, laufzeit_von: str, laufzeit_bis: str, dbID=0, ) -> None:
        self.stundenbudget = stundenbudget
        self.laufzeit_bis = laufzeit_bis
        self.psp_bezeichnung = psp_bezeichnung
        self.laufzeit_von = laufzeit_von
        self.stundensatz = stundensatz
        self.dbID = dbID
        super().__init__(name, personalnummer, psp_element)

    @classmethod
    def create_from_db(cls, pma: ProjektMitarbeiter):
        return cls(pma.personalnummer, pma.name, pma.psp_bezeichnung, pma.psp_element, pma.stundensatz,
                   pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis, pma.id, )


class ProjektDTO:
    psp: str
    projekt_name: str
    projektmitarbeiter: [ProjektmitarbeiterDTO]
    volumen: int
    laufzeit_von: str
    laufzeit_bis: str
    psp_packages: [PspPackageDTO]
    uploaddatum: datetime
    archiviert: bool

    project_master_id: int

    def __init__(self, projekt_name: str, psp: str, volumen: int, laufzeit_von: str, laufzeit_bis: str,
                 projektmitarbeiter: [ProjektmitarbeiterDTO], psp_packages: [PspPackageDTO], project_master_id: int = 0, dbID=0,
                 uploaddatum=datetime.today(),  archiviert=False) -> None:
        self.volumen = volumen
        self.projekt_name = projekt_name
        self.laufzeit_bis = laufzeit_bis
        projektmitarbeiter_updated: [ProjektmitarbeiterDTO] = []
        if (projektmitarbeiter):
            if type(projektmitarbeiter[0]) != ProjektmitarbeiterDTO:
                for pma in projektmitarbeiter:
                    projektmitarbeiter_updated.append(ProjektmitarbeiterDTO(**pma))
            else:
                projektmitarbeiter_updated = projektmitarbeiter

        self.projektmitarbeiter: [ProjektmitarbeiterDTO] = projektmitarbeiter_updated
        if psp_packages:
            self.psp_packages: [PspPackageDTO] = psp_packages
        else:
            self.psp_packages: [PspPackageDTO] = []
        self.psp = psp
        self.laufzeit_von = laufzeit_von
        self.dbID = dbID
        self.uploaddatum = uploaddatum
        self.archiviert = archiviert
        self.project_master_id = project_master_id

    @classmethod
    def create_from_db(cls, projekt: Projekt, psp_packages: [PspPackageDTO]):
        projektmitarbeiter: [ProjektmitarbeiterDTO] = []
        pma: ProjektMitarbeiter
        for pma in projekt.projektmitarbeiter:
            projektmitarbeiter.append(
                ProjektmitarbeiterDTO(pma.personalnummer, pma.name, pma.psp_bezeichnung, pma.psp_element,
                                      pma.stundensatz, pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis, pma.id))

        return cls(projekt.projekt_name, projekt.psp, projekt.volumen, projekt.laufzeit_von, projekt.laufzeit_bis,
                   projektmitarbeiter, psp_packages,  projekt.project_master_id, projekt.id, uploaddatum=projekt.uploadDatum,
                   )
