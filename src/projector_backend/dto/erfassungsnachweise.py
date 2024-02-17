class ErfassungsnachweisDTO:
    name: str
    personalnummer: int
    # tage: [datetime]
    # stunden: [float]
    tage: [str]
    tage_zu_stunden: {str: float} = dict()
    tage_zu_abwesenheiten: {str: str} = dict()

    # def __init__(self, name: str, personalnummer: int, tage: [datetime], stunden: [float], ) -> None:
    #     self.stunden = stunden
    #     self.tage = tage
    #     self.name = name
    #     self.personalnummer = personalnummer

    def __init__(self, name: str, personalnummer: int,tage:[str], tage_zu_stunden: {str: float},
                 tage_zu_abwesenheiten: {str: str}) -> None:
        self.name = name
        self.personalnummer = personalnummer
        self.tage = tage
        self.tage_zu_stunden = tage_zu_stunden
        self.tage_zu_abwesenheiten = tage_zu_abwesenheiten
