from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.extraction_schema import ExtractionResult

class LiteratureScreenResult(BaseModel):
    article_title: str = Field(description="Title of the medical literature reprint")
    authors: str = Field(default="Not stated", description="Primary authors")
    journal: str = Field(default="Not stated", description="Journal citation")
    publication_year: str = Field(default="Not stated")
    is_reportable: bool = Field(description="True if article contains >= 1 identifiable human safety report")
    exclusion_reason: Optional[str] = Field(default=None, description="Regulatory justification if non-reportable (e.g., animal study, meta-analysis)")
    study_type: str = Field(description="Single Case Report, Multi-Patient Case Series, Preclinical Animal/In-Vitro, Systematic Review/Meta-Analysis")
    patient_cases_count: int = Field(default=0, description="Number of distinct identifiable patient cases found")
    individual_cases: List[ExtractionResult] = Field(default_factory=list, description="Independent ICSR records split from this paper")
    screening_summary: str = Field(description="10-15 sentence comprehensive regulatory literature screening summary")
