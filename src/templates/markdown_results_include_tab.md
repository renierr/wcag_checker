***Tabbings on page***

{%- if "error" in result -%}
- **Error:** {{ result.error }}
{%- else %}

There are {{ result | length }} tabbings on the Page.

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
