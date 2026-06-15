# Peter's Review Manager

# General
This project consists of two programs that will facilitate access to the backlog of media reviews by Peter Rogers, all of which have been posted to LiveJournal over the last twenty years.

The first is the Scraper, a python program that scrapes LiveJournal posts to generate a CSV file with info about those reviews.

The second is the Viewer, a simple React SPA that displays data from the CSV file.

## The Scraper
The Scraper is a python application that generates `peter_reviews_data.csv`.

### Development Workflow
For ease of development and testing, the scraper uses localized HTML files stored in `/scraper/pages`.

#### Refreshing Data
To update the local cache of HTML pages, use the refresh tool:
```bash
cd scraper
source venv/bin/activate
python3 refresh_pages.py
```
This tool will:
1. Download all URLs from `unreachable review links.txt` into `/scraper/pages` (Historical Mode).
2. Download all tag-view pages (`skip=0, 30, ...`) into `/scraper/pages` until repetition is detected (Standard Mode).

#### Generating CSV
Once the pages are downloaded, run the scraper to process the local files and generate the CSV:
```bash
cd scraper
python3 scraper.py
```

### Operation
`peter_reviews_data.csv` is a CSV file with these fields:
1. title: the title of the media in question
2. link: the URL, with anchor, that goes directly to the review
3. media_type: the type of media in question.  One of these values: book, movie, TV, course, video game, other.
4. post_date: a timestamp of when the review was posted
5. parenthetical: explanatory text appended to the title


The scraper operates in two modes:
#### Historical Mode
It reads a list of URLs from `unreachable review links.txt`. These links point to older media updates (2006-2010) that are not easily accessible through standard tag pagination. The scraper uses a fallback parsing logic for these unstructured posts, identifying reviews via titles and category keywords.

Each page will have a single block at the top fo the page, formatted roughly like this:
```
<p>Movies:&nbsp; &lt;none&gt;<br>TV:&nbsp; <i>The Wire</i> (Season 2, Disc 5), <i>The Wire</i> (Season 4, Episode 1), <i>Arrested Development</i> (Season 3, Disc 1), <i>Buffy the Vampire Slayer</i> (Season 5, Disc 3)<br>Books:&nbsp; <i>Jimmy Corrigan, The Smartest Kid on Earth</i><br><br><a name="cutid1"></a></p>
```

You will set the fields as follows — we'll use _Buffy the Vampire Slayer_ from the above block as an example:
1. title: <i>Buffy the Vampire Slayer</i>.  This is the text in the last item on the comma-delimited list for "TV".
2. link: https://hujhax.livejournal.com/238052.html.  Typically in historical pages, the block has no links to reviews.  If the links are present, use the links.  If the links are missing, fall back on the link for the page itself.
3. media_type: 'TV'.  You get this value from the heading of the comma-delimited list.  (Note that in the rare cases where `media_type` is not one of the enumerated list above, you set it to 'Other'.)
4. post_date: "2006-09-08T19:29:00.000Z"  Note that we're storing timestamps as ISO standard UTC.  The block has its time string at the start of the page itself, and it is a naïve datetime.  If the date is before August 2021, it is Central time.  Otherwise it is Eastern time.
5. parenthetical: Season 5, Disc 3.  If there is non-italicized parenthetical text at the end of the title, we remove it, with its parentheses, from the title, and store it, without its parenthesis, here.

The page will include additional links below what's listed in this top of page block.  Ignore those links.  Generally, ignore any links that do not go to a livejournal page.

#### Standard Mode
It iterates through the `media update` tag view, incrementing `skip` by 30 until repetition is detected (via unique post IDs). This mode handles the modern structured "blocks" (`H3Holder`) and anchor-based deep linking.


To get the first batch of data, access this page:
https://hujhax.livejournal.com/?skip=0&tag=media%20update&style=mine

To get each subsequent batch of data, increment "skip" by 30.  For example:

https://hujhax.livejournal.com/?skip=30&tag=media%20update&style=mine
https://hujhax.livejournal.com/?skip=60&tag=media%20update&style=mine

Note that eventually, increasing the skip value will produce the same page over again (it will show posts from 2011).  At this point, you have all the available data and can stop iterating.

Each of these pages contains a series of "blocks".

Each block is formatted based on the mode.

In "Standard Mode", a block looks like this:

```
<div class="H3Holder"><div class="Picture" style="background-color: ;"><div><img src="https://l-userpic.livejournal.com/78221222/3805119"></div></div><h3><span>Monday (9/1/25) 4:51pm - <em>... wherein Peter posts a Weekly Media Update.</em></span> </h3><p>Books:&nbsp; <a href="http://hujhax.livejournal.com/1200700.html#abc" target="_blank"><i>American Born Chinese</i></a>, <a href="http://hujhax.livejournal.com/1200700.html#clue" target="_blank"><i>Clue: Candlestick</i></a>, <a href="http://hujhax.livejournal.com/1200700.html#coens" target="_blank"><i>The Coen Brothers</i></a><br>Movies:&nbsp; <a href="http://hujhax.livejournal.com/1200700.html#jeanne" target="_blank"><i>Jeanne Dielman, 23 quai du Commerce, 1080 Bruxelles</i></a><br>TV:&nbsp; <a href="http://hujhax.livejournal.com/1200700.html#severance" target="_blank"><i>Severance</i> (season 2)</a><br><br><b data-widget="ljcut" data-widget-options="{&quot;sticky&quot;:false,&quot;placeholders&quot;:0,&quot;cutid&quot;:1,&quot;journalid&quot;:3805119,&quot;ditemid&quot;:1200700}" class="ljcut-link lj-widget lj-widget-8" data-widget-id="8" data-inited="true"><span class="ljcut-brace">(&nbsp;</span><span class="ljcut-decor"><a href="https://hujhax.livejournal.com/1200700.html#cutid1" class="ljcut-link-expand" title="Details behind the cut.">Details behind the cut.</a><a href="https://hujhax.livejournal.com/1200700.html#cutid1" class="ljcut-link-collapse">Collapse</a></span><span class="ljcut-brace">&nbsp;)</span></b></p><div class="ljtags"><strong>Tags:</strong> <a rel="tag" href="https://hujhax.livejournal.com/tag/media%20update/">media update</a>, <a rel="tag" href="https://hujhax.livejournal.com/tag/weekly/">weekly</a></div><table width="100%"><tbody><tr><td align="left"><div class="CurrentStuff"><strong>Mood:</strong> <img src="https://stat.livejournal.com/img/mood/niaha/kitty/ankthinkg.gif" width="" height="" align="absmiddle" alt="[mood icon]"> contemplative · <strong>Music:</strong> None </div></td><td align="right"><div class="Comment"><a href="https://hujhax.livejournal.com/1200700.html?view=comments#comments?style=mine">Link</a>&nbsp;·&nbsp;<a href="https://hujhax.livejournal.com/1200700.html?mode=reply#add_comment&amp;style=mine">Leave a comment</a></div></td></tr></tbody></table></div>
```

The most important part of the block is the series of comma-delimited lists after the initial <p>; they are separated by <br> tags.  In this section, each line includes a media type, a colon, some number of spaces, and then a comma-delimited lists of links to reviews.

The general pseudocode for our approach is the following:
* For each page
	* For each block on the page
		* For each comma-delimited list in the block
			* For each item in the comma-delimited list
				* Generate a record in the CSV
				
You will set the fields as follows — we'll use _Severance_ from the above block as an example:
1. title: <i>Severance</i>.  This is the text in the first item on the comma-delimited list for "TV".
2. link: http://hujhax.livejournal.com/1200700.html#severance.  This is the `a href` link for the given text. (If an item in the comma-delimited list in the block links to wikipedia instead of livejournal, ignore that link, and use the livejournal link to the page itself instead.)
3. media_type: 'TV'.  You get this value from the heading of the comma-delimited list.  (Note that in the rare cases where `media_type` is not one of the enumerated list above, you set it to 'Other'.)
4. post_date: "2025-09-01T20:51:00.000Z"  Note that we're storing timestamps as ISO standard UTC.  The block has its time string at the start of the `h3 span`, and it is a naïve datetime.  If the date is before August 2021, it is Central time.  Otherwise it is Eastern time.
5. parenthetical: season 2.  If there is non-italicized parenthetical text at the end of the title, we remove it, with its parentheses, from the title, and store it, without its parenthesis, here.

Iterate through all the available pages, gather all the available blocks, and generate all the appropriate records.

### About Parentheticals
A general note for parentheticals: parentheticals can also be bracketed text at the end of a title.  If a title has multiple parentheticals, put them into the parenthetical field as a comma-delimited list.  For example, the string "Horseplay (season one) [spoilers]" produces the title "Horseplay" and the parenthetical "season one, spoilers".

## The Viewer
The Viewer is a React SPA that provides users a filtered view of the records in peter_reviews_data.csv.  It is a simple in-browser app that can be hosted in GitHub pages.  (Ergo it cannot run back-end server code.)  It will include its own copy of  `peter_reviews_data.csv` and serve that data to the user.

The app should have a dark, soothing, earth-toned color scheme.  For fonts, it should use [Inlander Rough](https://freefonts.co/fonts/inlander-rough) for headings and Garamond (or something similar) for body text.

The app should work on both mobile and desktop.

The screen has a title: "Peter's LJ Reviews".

It has filter fields for:
1. "Title": a text field. Searching by title should use fuzzy search.
2. "Media Type": a dropdown of the acceptable values for media_type.
3. "Date": this has calendar controls for a start date and an end date.

All of these fields are blank by default; if blank, the search algorithm ignores them.

Below the filters are a table of results.

The headers are "Title", "Subtitle", "Media Type", and "Date".

Each row includes the title (hyperlinked to the review link), the parenthetical (this is listed in the "Subtitle" column), the media type, and the date.  There is also a button for "copy link".  If the user clicks this, the app copies the review link to the clipboard.  (After this, flash a message that the link was copied to the clipboard.)

The results are paginated, 10 to a page, defaulting to page 1, with pagination info ("page [x] of [y]") and controls just below the table rows.

By default, results are sorted alphabetically, A to Z, by title.  The user can click the table headers to sort ascending or descending by "Title", "Media Type", and "Date".

When sorting by title, put the strings in "title order" — that is, ignore initial articles like "a", "an", or "the", and ignore initial punctuation.

If the user sorts by title, add a secondary sort by date (ascending).
If the user sorts by subtitle or media type, add a secondary sort by title (ascending) and a tertiary sort by date (ascending).

The app updates the table instantaneously when the user updates the media type or date search filters, or types anything into the title filter.

When the user types into the title field, the app provides a dropdown of autocompletes, picked out via fuzzy search, with the matched characters bolded in the autocomplete options.