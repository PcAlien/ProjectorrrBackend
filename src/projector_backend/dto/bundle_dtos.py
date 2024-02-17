from src.projector_backend.dto.erfassungsnachweise import ErfassungsnachweisDTO
from src.projector_backend.dto.ma_bookings_summary_dto import MaBookingsSummaryDTO
from src.projector_backend.dto.project_summary import ProjectSummaryDTO, UmsatzDTO
from src.projector_backend.dto.projekt_dto import ProjektDTO


class BundleSummary:
    monat_zu_umsatz :dict
    project_summaries: [ProjectSummaryDTO]



    def __init__(self, project_summaries: [ProjectSummaryDTO]) -> None:
        self.project_summaries = project_summaries
        self.monat_zu_umsatz = dict()


        prosum: ProjectSummaryDTO
        for prosum in project_summaries:
            for um in prosum.umsaetze:
                if um.monat in self.monat_zu_umsatz.keys():
                    self.monat_zu_umsatz[um.monat] += um.umsatz
                else:
                    self.monat_zu_umsatz[um.monat] = um.umsatz


class ProjectBundleDTO:
    bundle_name: str
    bundle_descripton: str
    bundle_summary: BundleSummary

    identifier: str

    budget: float =0
    umsatz: float = 0
    restbudget: float = 0

    project_summaries:[ProjectSummaryDTO]
    monthly_umsaetze: [MaBookingsSummaryDTO]

    nachweise:[ErfassungsnachweisDTO]

    def __init__(self, bundle_name:str,  bundle_descripton: str,project_summaries: [ProjectSummaryDTO] , identifier,  monthly_umsaetze: [MaBookingsSummaryDTO],nachweise:[ErfassungsnachweisDTO]) -> None:
        self.bundle_name = bundle_name
        self.bundle_descripton: str =  bundle_descripton
        self.bundle_summary = BundleSummary(project_summaries)
        self.identifier = identifier
        self.monthly_umsaetze = monthly_umsaetze
        self.nachweise = nachweise


        pro: ProjectSummaryDTO
        u: UmsatzDTO
        for pro in project_summaries:
            self.budget += pro.project.volumen
            self.umsatz += pro.spent
            self.restbudget += pro.restbudget



class ProjectBundleCreateDTO:
    bundle_name: str
    bundle_descripton: str
    psp_list :[ProjektDTO]

    def __init__(self, bundle_name: str, bundle_descripton: str, psp_list:[str]) -> None:
        self.bundle_descripton = bundle_descripton
        self.bundle_name = bundle_name
        self.psp_list = psp_list


