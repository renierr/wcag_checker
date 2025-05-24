import json
from enum import Enum

class ReportLevel(Enum):
    ALL = "all"
    INVALID = "invalid"

class ColorSource(Enum):
    IMAGE = "image"
    ELEMENT = "element"

class Mode(Enum):
    CONTRAST = "contrast"
    AXE = "axe"
    ACTIONS = "actions"

class ConfigEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class Config:
    def __init__(self, *args, **kwargs):
        def resolution_split(resolution: str) -> tuple:
            try:
                width, height = map(int, resolution.split("x"))
                return width, height
            except ValueError:
                raise ValueError("Resolution must be in the format <width>x<height>")

        if len(args) == 1 and hasattr(args[0], '__dict__'):
            # initialize with argparse.Namespace
            namespace = args[0]
            self.mode = Mode(namespace.mode)
            self.browser = namespace.browser
            self.browser_visible = namespace.browser_visible
            self.login = namespace.login
            self.inputs = namespace.inputs
            self.output = namespace.output
            self.debug = namespace.debug
            self.json_output = namespace.json
            self.markdown_output = namespace.markdown
            self.html_output = namespace.html
            self.youtrack_output = namespace.youtrack
            self.simulate = namespace.simulate
            self.resolution = resolution_split(namespace.resolution)
            self.resolution_width = self.resolution[0]
            self.resolution_height = self.resolution[1]
        else:
            raise ValueError("Config must be initialized with an argparse.Namespace.")

    def __str__(self):
        attributes = vars(self)
        return "Config(\n" + "\n".join(f"  {key}={value}" for key, value in attributes.items()) + "\n)"

    def __repr__(self):
        return self.__str__()


class AxeConfig(Config):
    def __init__(self, *args, axe_rules=None, **kwargs):
        super().__init__(*args, **kwargs)
        namespace = args[0]
        self.axe_rules = getattr(namespace, "axe_rules", None)

class ContrastConfig(Config):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        namespace = args[0]
        self.selector = getattr(namespace, "selector", None)
        self.contrast_threshold = getattr(namespace, "contrast_threshold", None)
        self.use_canny_edge_detection = getattr(namespace, "use_canny_edge_detection", False)
        self.use_antialias = getattr(namespace, "use_antialias", False)
        self.report_level = ReportLevel(getattr(namespace, "report_level", ReportLevel.INVALID))
        self.alternate_color_suggestion = getattr(namespace, "alternate_color_suggestion", False)
        self.color_source = ColorSource(getattr(namespace, "color_source", ColorSource.ELEMENT))
