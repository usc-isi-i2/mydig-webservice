# mydig-webservice

## Configuration File

### Fields

| Attribute     | Possible Values | Explanation  |
| ------------- |---------------| -----|
| name          | alphanumeric and underscore | the name of a field, cannot be changed |
| description   | text          |   A description of the field |
| screen_label  | text        | The text to display the field in DIG |
| screen_label_plural | text | Label when a field contains multiple values |
| icon | see below | The icon to decorate the field in DIG |
| color | see below | The color used to display the field in DIG |
| show_as_link | `entity`, `text`| Specifies the appearance of the field: `entity` (default) shows a link that opens an entity page, `text` shows the value as a text string (no link) |
| show_in_facets | false, true | When true, the field appears in the facets section |
| show_in_result | `title`, `description`, `detail`, `header`, `no` | Location where the field appears in the results page: `title` what does this do?, `description` what does this do?, `detail` in the accordion, `header` in the search tile, `no` not present in the results page|
| show_in_search | false, true | When true, the field appears in the query form |
| glossaries | array of glossary names | The names of glossaries used to extrace values for the field |
| search_importance | Integer, range(1, 10) | High numbers make results matching in a field push documents up in the ranking |
| type | `date`, `email`, `hyphenated`, `image`, `location`, `phone`, `string`, `username` | Affects the appearance as well as search behavior: `date` value must be in ISO format, `email`, `hyphenated`, `image`, `location` must have a DIG key with lat and long, `phone`, `string` the default, `username` |
| use_in_network_search | false, true | support network creation using the values from a field |
| predefined_extractor | one of `social_media`, `review_id`, `city`, `posting_date`, `phone`, `email`, `address`, `country`, `website`, `none` | specifies a default extractor to use for a field |
| rule_extractor_enabled | false, true | When true, use the custom rule extractor for this field, if one is defined |

### Icons



### Colors
