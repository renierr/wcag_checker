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

class ConfigEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value  # Enum-Wert als String zurückgeben
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
            # mode specific - could be not set
            self.selector = getattr(namespace, "selector", None)
            self.contrast_threshold = getattr(namespace, "contrast_threshold", None)
            self.use_canny_edge_detection = getattr(namespace, "use_canny_edge_detection", False)
            self.use_antialias = getattr(namespace, "use_antialias", False)
            self.report_level = ReportLevel(getattr(namespace, "report_level", ReportLevel.INVALID))
            self.alternate_color_suggestion = getattr(namespace, "alternate_color_suggestion", False)
            self.color_source = ColorSource(getattr(namespace, "color_source", ColorSource.ELEMENT))
            self.axe_rules = getattr(namespace, "axe_rules", None)
        else:
            # initialise directly with keyword arguments
            self.mode = Mode(kwargs.get("mode", Mode.CONTRAST))
            self.browser = kwargs.get("browser")
            self.login = kwargs.get("login")
            self.inputs = kwargs.get("inputs")
            self.selector = kwargs.get("selector")
            self.contrast_threshold = kwargs.get("contrast_threshold")
            self.output = kwargs.get("output")
            self.use_canny_edge_detection = kwargs.get("use_canny_edge_detection")
            self.use_antialias = kwargs.get("use_antialias")
            self.debug = kwargs.get("debug")
            self.json_output = kwargs.get("json_output", True)
            self.markdown_output = kwargs.get("markdown_output", True)
            self.html_output = kwargs.get("html_output", True)
            self.youtrack_output = kwargs.get("youtrack_output", True)
            self.simulate = kwargs.get("simulate")
            self.report_level = ReportLevel(kwargs.get("report_level", ReportLevel.INVALID))
            self.resolution = resolution_split(kwargs.get("resolution", "1920x1080"))
            self.resolution_width = self.resolution[0]
            self.resolution_height = self.resolution[1]
            self.alternate_color_suggestion = kwargs.get("alternate_color_suggestion", False)
            self.color_source = ColorSource(kwargs.get("color_source", ColorSource.ELEMENT))
            self.axe_rules = kwargs.get("axe_rules", None)

    def __str__(self):
        attributes = vars(self)
        return "Config(\n" + "\n".join(f"  {key}={value}" for key, value in attributes.items()) + "\n)"

    def __repr__(self):
        return self.__str__()
