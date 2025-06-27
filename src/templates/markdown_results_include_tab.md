***Tabbings on page***

{%- if "error" in result -%}
- **Error:** {{ result.error }}
{%- else %}

- **Page Tabbings:** {{ result.tabbed_elements | length }}
{% if result.potential_elements | length > 0 %}
- **Potential Tabbings:** {{ result.potential_elements | length }}
{% endif %}


{% if config.debug %}
<section>
<details>
<summary>Show JSON</summary>

```json
{{ result | tojson(indent=2) }}
```

</details>
</section>
{% endif %}
{%- endif %}
