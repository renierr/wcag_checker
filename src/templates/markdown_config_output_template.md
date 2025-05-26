#### Configuration
- **Mode:** {{input_data.config.mode}}
{% if input_data.config.runner|string == "axe" %}
- **Axe Rules:** {{input_data.config.axe_rules}}
{% elif input_data.config.runner|string == "contrast" %}
- **Contrast Threshold:** {{input_data.config.contrast_threshold}}
- **Selector:** `{{input_data.config.selector}}`
- **Alternate Color Suggestion:** {{"Enabled" if input_data.config.alternate_color_suggestion else "Disabled"}}
- **Canny Edge Detection:** {{"Enabled" if input_data.config.use_canny_edge_detection else "Disabled"}}
- **Antialias:** {{"Enabled" if input_data.config.use_antialias else "Disabled"}}
- **Report Level:** {{input_data.config.report_level}}
{% endif %}
- **Resolution:** {{input_data.config.resolution_width}}x{{input_data.config.resolution_height}} (Base), {{input_data.browser_width}}x{{input_data.browser_height}} (Browser)
