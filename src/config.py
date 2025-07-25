import json
from dataclasses import dataclass, field
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
    CHECK = "check"
    ACTIONS = "actions"

    def __str__(self):
        return self.value

class Runner(Enum):
    AXE = "axe"
    CONTRAST = "contrast"
    TAB = "tab"

    def __str__(self):
        return self.value

class ConfigEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


@dataclass
class Config:
    mode: Mode = Mode.CHECK
    debug: bool = False
    browser: str = "chrome"
    browser_visible: bool = False
    browser_leave_open: bool = False
    output: str = "output"

@dataclass
class ProcessingConfig(Config):
    runner: Runner = Runner.AXE
    login: str = ""
    inputs: list[str] = field(default_factory=list)
    json: bool = True
    markdown: bool = True
    html: bool = True
    simulate: str | None = None
    resolution: tuple[int, int] = (1920, 1080)
    resolution_width: int = field(init=False)
    resolution_height: int = field(init=False)
    axe_rules: str | None = "wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa"
    selector: str  | None = "a, button:not([disabled])"
    contrast_threshold: float = 4.5
    use_canny_edge_detection: bool = False
    use_antialias: bool = False
    report_level: ReportLevel = ReportLevel.INVALID
    alternate_color_suggestion: bool = False
    color_source: ColorSource = ColorSource.ELEMENT
    context: str | None = None
    missing_tab_check: bool = True

    def __post_init__(self):
        self.resolution_width, self.resolution_height = self.resolution
