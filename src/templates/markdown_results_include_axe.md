***Axe findings***

![Full Page Screenshot with Outlines]({{input_data.get('screenshot_outline','').replace(output + '/', '')}})

{% for result in input_data.results %}
{% if result.violations | length == 0 %}
No violations found.
{% endif -%}

{%- for violation in result.violations %}
#### {% if violation.impact == "critical" %}🔥{% elif violation.impact == "serious" %}⚠️{% elif violation.impact == "moderate" %}🔶{% elif violation.impact == "minor" %}ℹ️{% endif %} {{ violation.id }} - {{ violation.impact | capitalize }}

{{ violation.description }}
{{ violation.help }}
{%- if violation.help_url %}
[Learn more]({{ violation.help_url }})
{% endif %}
{%- if violation.nodes %}

{% for node in violation.nodes %}
*Element {{ node.element_info.index }}*     
`{{ node.target | join(', ') }}` 

{{ node.failureSummary.replace("Fix any of the following:\n  ", "") }}

{% if node.any and node.any[0] -%}
{% if node.any[0].data.fgColor -%}Foreground: {{ node.any[0].data.fgColor | create_color_span }}, {% endif -%}
{% if node.any[0].data.bgColor -%}Background: {{ node.any[0].data.bgColor | create_color_span }} {% endif %}
{% endif %}

{% if node.element_info.screenshot -%}
![Element Screenshot]({{node.element_info.screenshot.replace(output + '/', '')}})
{% endif %}

{% endfor %}
{% endif %}

{% if config.debug %}
<section>
<details>
<summary>Show JSON</summary>

```json
{{ violation | tojson(indent=2) }}
```

</details>
</section>
{% endif %}

{% endfor -%}

---
{% endfor %}
