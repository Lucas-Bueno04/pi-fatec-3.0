from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator
from ..models.question import QuestionType, DifficultyLevel


class AlternativeCreate(BaseModel):
    id: str
    text: str
    alt_text: Optional[str] = None
    is_correct: bool = False
    image_id: Optional[str] = None  # set after image upload


class AlternativeResponse(BaseModel):
    id: str
    text: str
    image_id: Optional[str] = None
    alt_text: Optional[str] = None
    is_correct: Optional[bool] = None  # hidden in quiz context


class AssociationPairCreate(BaseModel):
    material_id: str
    material_name: str
    target_id: str
    target_text: str


class QuestionCreate(BaseModel):
    type: QuestionType
    difficulty: DifficultyLevel
    text: str
    image_alt_text: Optional[str] = None
    alternatives: List[AlternativeCreate] = []
    association_pairs: List[AssociationPairCreate] = []
    explanation: str = ""
    material_name: Optional[str] = None
    function_text: Optional[str] = None
    system_name: Optional[str] = None

    @model_validator(mode="after")
    def validate_by_type(self):
        if self.type == QuestionType.MULTIPLA_ESCOLHA:
            if len(self.alternatives) != 4:
                raise ValueError("Questões de múltipla escolha precisam ter exatamente 4 alternativas.")
            correct = [a for a in self.alternatives if a.is_correct]
            if len(correct) != 1:
                raise ValueError("Questões de múltipla escolha precisam ter exatamente 1 alternativa correta.")
        elif self.type in (QuestionType.ASSOCIACAO_FUNCAO, QuestionType.ASSOCIACAO_SISTEMA):
            if len(self.association_pairs) < 2:
                raise ValueError("Questões de associação precisam de pelo menos 2 pares.")
        return self


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    alternatives: Optional[List[AlternativeCreate]] = None
    explanation: Optional[str] = None
    is_active: Optional[bool] = None
    material_name: Optional[str] = None
    function_text: Optional[str] = None
    system_name: Optional[str] = None
    image_id: Optional[str] = None
    image_alt_text: Optional[str] = None


class QuestionResponse(BaseModel):
    id: str
    type: QuestionType
    difficulty: DifficultyLevel
    text: str
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_alt_text: Optional[str] = None
    alternatives: List[AlternativeResponse]
    explanation: str
    material_name: Optional[str] = None
    function_text: Optional[str] = None
    system_name: Optional[str] = None
    is_active: bool
    created_by: str


class QuestionFilter(BaseModel):
    type: Optional[QuestionType] = None
    difficulty: Optional[DifficultyLevel] = None
    is_active: Optional[bool] = True
