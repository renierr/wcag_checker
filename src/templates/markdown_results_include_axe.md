***Axe findings***
{% if result.violations | length == 0 %}
No violations found.
{% endif -%}

{%- if "error" in result -%}
- **Error:** {{ result.error }}
  {%- else -%}
  {%- for violation in result.violations %}
#### {% if violation.impact == "critical" %}🔥{% elif violation.impact == "serious" %}⚠️{% elif violation.impact == "moderate" %}🔶{% elif violation.impact == "minor" %}ℹ️{% endif %} {{ violation.id }} - {{ violation.impact | capitalize }}

{{ violation.description }}
{{ violation.help }}
{%- if violation.help_url %}
[Learn more]({{ violation.help_url }})
{% endif %}
{%- if violation.nodes %}

**Affected Elements:**
{% for node in violation.nodes %}
Element {{ node.element_info.index }} [ `{{ node.target | join(', ') }}` ]

{{ node.failureSummary.replace("Fix any of the following:\n  ", "") }}

{% if node.any and node.any[0] and node.any[0].data.fgColor -%}_Foreground Color:_ {{ node.any[0].data.fgColor | create_color_span }}    {% endif %}
{% if node.any and node.any[0] and node.any[0].data.bgColor -%}_Background Color:_ {{ node.any[0].data.bgColor | create_color_span }}    {% endif %}

{% if node.element_info.screenshot -%}
![Element Screenshot]({{node.element_info.screenshot.replace(output + '/', '')}})
{% endif -%}

---

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
{%- endif %}
