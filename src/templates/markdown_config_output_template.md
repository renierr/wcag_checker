#### Configuration

- **Mode:** {{config.mode}}
{% if config.mode|string == "axe" %}
- **Axe Rules:** {{config.axe_rules}}
{% elif config.mode|string == "contrast" %}
- **Contrast Threshold:** {{config.contrast_threshold}}
- **Selector:** `{{config.selector}}`
- **Alternate Color Suggestion:** {{"Enabled" if config.alternate_color_suggestion else "Disabled"}}
- **Use Canny Edge Detection:** {{"Enabled" if config.use_canny_edge_detection else "Disabled"}}
- **Use Antialias:** {{"Enabled" if config.use_antialias else "Disabled"}}
- **Report Level:** {{config.report_level}}
{% endif %}
- **Base Resolution:** {{config.resolution_width}}x{{config.resolution_height}}
