#
# PSP PREKALKULATION
#

class Auslastung:

    def __init__(self, name, stundensatz, auslastung_am_tag) -> None:
        self.name = name
        self.stundensatz = stundensatz
        self.auslastung_am_tag = auslastung_am_tag


class Ergebnishalter:

    def __init__(self, auslastung, prozentualer_anteil, stunden_im_projekt, umsatz_im_projekt, stunden_pro_at) -> None:
        self.auslastung = auslastung
        self.prozentualer_anteil = prozentualer_anteil
        self.stunden_im_projekt = stunden_im_projekt
        self.umsatz_im_projekt = umsatz_im_projekt
        self.stunden_pro_at = stunden_pro_at


ma1 = Auslastung("Markus", 140, 2)
ma2 = Auslastung("Marius", 115, 8)
ma3 = Auslastung("Thuy", 90, 8)
alleAuslastungen: [Auslastung] = [ma1, ma2, ma3]

budget = 60000

# 1. Summe der Stunden berechnen
summe_stunden = 0
for al in alleAuslastungen:
    summe_stunden += al.auslastung_am_tag

# 2. Berechne Summe der Kosten pro Tag pro MA
summe_kosten_tag_ma = 0
for al in alleAuslastungen:
    summe_kosten_tag_ma += al.auslastung_am_tag * al.stundensatz

# 3. Berechnung Durchschnittsstundensatz
durchschnitts_stundensatz = summe_kosten_tag_ma / summe_stunden

# 4. Stunden errechnen, die beim Budget zum Durchschnittsstundensatz möglich wären
projektstunden_bei_durchschnittswert = budget / durchschnitts_stundensatz


# 5. Funktion schreiben, die den Rest berechnet
def berechne_zeugs(auslastung, summe_stunden, projekttage):
    prozentualer_anteil = 100 / summe_stunden * auslastung.auslastung_am_tag
    stunden_im_projekt = (projektstunden_bei_durchschnittswert / 100) * prozentualer_anteil
    umsatz_im_projekt = stunden_im_projekt * auslastung.stundensatz
    stunden_pro_at = stunden_im_projekt / projekttage
    return Ergebnishalter(auslastung, prozentualer_anteil, stunden_im_projekt, umsatz_im_projekt, stunden_pro_at)


auslastungen: [Ergebnishalter] = []

for al in alleAuslastungen:
    eh = berechne_zeugs(al, summe_stunden, 220)
    auslastungen.append(eh)
    print(eh.auslastung.name, eh.stunden_im_projekt, eh.umsatz_im_projekt, eh.stunden_pro_at)

# Gegenrechnung
gegenrechnungssumme = 0
for al in auslastungen:
    gegenrechnungssumme += al.auslastung.stundensatz * al.stunden_pro_at * 220
