from datetime import datetime

from entities.projekt import Projekt, ProjektMitarbeiter


class ProjektmitarbeiterDTO:
    personalnummer: int
    name: str
    psp_bezeichnung: str
    psp_element: str
    stundensatz: int
    stundenbudget: int
    laufzeit_von: str
    laufzeit_bis: str
    uploaddatum: datetime

    def __init__(self, personalnummer: int, name: str, psp_bezeichnung: str, psp_element: str, stundensatz: int,
                 stundenbudget: int, laufzeit_von: str, laufzeit_bis: str, dbID= 0,  uploaddatum = datetime.today()) -> None:
        self.stundenbudget = stundenbudget
        self.psp_element = psp_element
        self.laufzeit_bis = laufzeit_bis
        self.name = name
        self.psp_bezeichnung = psp_bezeichnung
        self.personalnummer = personalnummer
        self.laufzeit_von = laufzeit_von
        self.stundensatz = stundensatz
        self.dbID=dbID
        self.uploaddatum = uploaddatum

    @classmethod
    def create_from_db(cls, pma: ProjektMitarbeiter):
        return cls(pma.personalnummer, pma.name, pma.psp_bezeichnung, pma.psp_element, pma.stundensatz,
                   pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis, pma.id, uploaddatum=pma.uploadDatum)


class ProjektDTO:
    volumen: int
    projekt_name: str
    laufzeit_bis: str
    projektmitarbeiter: [ProjektmitarbeiterDTO]
    psp: int
    laufzeit_von: str
    uploaddatum: datetime

    def __init__(self, projekt_name: str, psp: int, volumen: int, laufzeit_von: str, laufzeit_bis: str,
                 projektmitarbeiter: [ProjektmitarbeiterDTO], dbID=0, uploaddatum = datetime.today()) -> None:
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
        self.psp = psp
        self.laufzeit_von = laufzeit_von
        self.dbID = dbID
        self.uploaddatum = uploaddatum

    @classmethod
    def create_from_db(cls, projekt: Projekt):
        projektmitarbeiter: [ProjektmitarbeiterDTO] = []
        pma: ProjektMitarbeiter
        for pma in projekt.projektmitarbeiter:
            projektmitarbeiter.append(
                ProjektmitarbeiterDTO(pma.personalnummer, pma.name, pma.psp_bezeichnung, pma.psp_element,
                                      pma.stundensatz, pma.stundenbudget, pma.laufzeit_von, pma.laufzeit_bis, pma.id))
        return cls(projekt.projekt_name, projekt.psp, projekt.volumen, projekt.laufzeit_von, projekt.laufzeit_bis,
                   projektmitarbeiter, projekt.id, uploaddatum=projekt.uploadDatum)
