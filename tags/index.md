---
layout: default
title: "Tags"
---

# Tags

<div class="tag-list">
  {% assign tags = site.tags | sort %}
  {% for tag in tags %}
  <a href="#{{ tag[0] }}">{{ tag[0] }}</a>
  {% endfor %}
</div>

{% for tag in site.tags %}
<h3 id="{{ tag[0] }}">{{ tag[0] }}</h3>
<ul>
  {% for post in tag[1] %}
  <li><a href="{{ post.url }}">{{ post.title }}</a> ({{ post.date | date: "%Y-%m-%d" }})</li>
  {% endfor %}
</ul>
{% endfor %}
