#### Configuration
- **Mode:** {{input_data.config.mode}}
{% if input_data.config.mode|string == "axe" %}
- **Axe Rules:** {{input_data.config.axe_rules}}
{% elif input_data.config.mode|string == "contrast" %}
- **Contrast Threshold:** {{input_data.config.contrast_threshold}}
- **Selector:** `{{input_data.config.selector}}`
- **Alternate Color Suggestion:** {{"Enabled" if input_data.config.alternate_color_suggestion else "Disabled"}}
- **Use Canny Edge Detection:** {{"Enabled" if input_data.config.use_canny_edge_detection else "Disabled"}}
- **Use Antialias:** {{"Enabled" if input_data.config.use_antialias else "Disabled"}}
- **Report Level:** {{input_data.config.report_level}}
{% endif %}
- **Base Resolution:** {{input_data.config.resolution_width}}x{{input_data.config.resolution_height}}
