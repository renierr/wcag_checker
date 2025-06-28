***Tabbings on page***

{% if "error" in result %}
**Error:** {{ result.error }}
{%- else %}

- **Page Tabbings:** {{ result.tabbed_elements | length }}
{% if result.potential_elements | length > 0 %}
- **Potential Tabbings:** {{ result.potential_elements | length }}
{%- endif -%}
{% if result.missed_elements | length > 0 %}
- **Missed Tabbing Elements:** {{ result.missed_elements | length }}

{% for miss_el in result.missed_elements %}
#### 🔥 Missed Tabbing Element X{{ miss_el.index }}

**ID:**    
`{{ miss_el.id }}`
{% if miss_el.text %}
**Text:**
```plaintext
 {{ miss_el.text | e }}
```
{%- endif %}
{% endfor %}
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
