import json
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

class ReportLevel(Enum):
    ALL = "all"
    INVALID = "invalid"

    def __str__(self):
        return self.value

class ColorSource(Enum):
    IMAGE = "image"
    ELEMENT = "element"

    def __str__(self):
        return self.value

class Mode(Enum):
    CONTRAST = "contrast"
    AXE = "axe"
    ACTIONS = "actions"

    def __str__(self):
        return self.value

class ConfigEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


@dataclass
class Config:
    mode: Mode
    debug: bool
    browser: str
    browser_visible: bool
    output: str

@dataclass
class ProcessingConfig(Config):
    login: str = ""
    inputs: List[str] = field(default_factory=list)
    json: bool = True
    markdown: bool = True
    html: bool = True
    simulate: Optional[str] = None
    resolution: Tuple[int, int] = (1920, 1080)
    resolution_width: int = field(init=False)
    resolution_height: int = field(init=False)

    def __post_init__(self):
        self.resolution_width, self.resolution_height = self.resolution

@dataclass
class AxeConfig(ProcessingConfig):
    axe_rules: Optional[str] = None

@dataclass
class ContrastConfig(ProcessingConfig):
    selector: Optional[str] = "a, button:not([disabled])"
    contrast_threshold: float = 4.5
    use_canny_edge_detection: bool = False
    use_antialias: bool = False
    report_level: ReportLevel = ReportLevel.INVALID
    alternate_color_suggestion: bool = False
    color_source: ColorSource = ColorSource.ELEMENT
