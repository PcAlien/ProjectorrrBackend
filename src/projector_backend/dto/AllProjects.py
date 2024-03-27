from src.projector_backend.dto.projekt_dto import ProjektDTO


class AllProjectsDTO:

    projects: [ProjektDTO]
    active_ids: [int]

    def __init__(self, projects, active_ids) -> None:
        self.projects = projects
        self.active_ids = active_ids

