![Full Page Screenshot with Outlines]({{input_data.get('screenshot_outline','').replace(output + '/', '')}})

{% for result in input_data.results %}
<a name='el_{{input_data.index}} 0_{{result.element_index}}'></a>
#### {{result.element_index}}. Element of Page {{input_data.index}}
{%- if "error" in result -%}
- **Error:** {{ result.error }}
  {%- else -%}
  {%- set wcag_status = "✅ *Valid*" if result.meets_wcag else "❌ **Not Valid**" -%}
  {%- set color_spans = result.colors | join_color_span -%}
  {%- if result.element_text -%}
  {%- set element_text = "**Text:**\n```plaintext\n" + result.element_text | e + "\n```\n" -%}
  {%- else -%}
  {%- set element_text = "" -%}
  {%- endif %}
  | index | colors | contrast ratio | meets wcag |
  |-------|--------|----------------|------------|
  | {{ result.element_index }} | {{ color_spans }} | {{ "%.2f"|format(result.contrast_ratio) }} | {{ wcag_status }} |

**CSS Path:** `{{ result.element_path }}`

{{ element_text }}

{%- set suggestions = result.color_suggestions -%}
{%- if suggestions -%}
**Color Suggestions:** (that meets WCAG)

| Color 1 | Color 2 | Contrast |
|---------|---------|----------|
{% for suggestion in suggestions -%}
{%- set colors = suggestion.colors if suggestion.colors else [] -%}
{%- if colors|length == 2 -%}
{%- set color1, color2 = colors -%}
| {{ color1 | create_color_span }} | {{ color2 | create_color_span }} | {{ "%.2f"|format(suggestion.contrast) if suggestion.contrast is not none else "N/A" }} |
{% endif -%}
{%- endfor -%}
{%- endif %}

**Image reference:**

![Element Screenshot]({{result.screenshot.replace(output + '/', '')}})
{% endif %}

---
{% endfor %}
