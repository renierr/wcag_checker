***Tabbings on page***

<style>
  .tabbing-path-image {
    display: block;
    background-repeat: no-repeat;
    background-size: contain;
  }
  .toggle-bg-checkbox:not(:checked) ~ .tabbing-path-image {
    background-image: none !important;
  }
</style>

{% for result in input_data.results %}

{% set tab_image_svg = result.get('tab_path_svg','').replace(output + '/', '') %}
{% set tab_image_background = input_data.get('screenshot','').replace(output + '/', '') %}
<div class="tab-image-container">
  <input type="checkbox" checked="checked" id="toggle-bg-{{ loop.index }}" class="toggle-bg-checkbox">
  <label for="toggle-bg-{{ loop.index }}">Show Page Background</label>
  {% if tab_image_svg %}
<img src="{{ tab_image_svg }}" style="background-image: url('{{ tab_image_background }}')" alt="Tab Path SVG" class="tabbing-path-image">
  {% else %}
    {% set tab_image_outline = input_data.get('screenshot_outline','').replace(output + '/', '') %}
![Tab Path Image]({{ tab_image_outline }})
  {% endif %}
</div>

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

{% if miss_el.location %}
**Location:** 
{{ miss_el.location }}
{%- endif %}

{% if miss_el.tag_name %}
**Tag Name:** 
{{ miss_el.tag_name }}
{%- endif %}

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

---
{% endfor %}
