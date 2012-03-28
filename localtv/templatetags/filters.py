# Miro Community - Easiest way to make a video website
#
# Copyright (C) 2009, 2010, 2011, 2012 Participatory Culture Foundation
# 
# Miro Community is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# Miro Community is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with Miro Community.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import re
import lxml.html

from bs4 import BeautifulSoup, Comment, Tag
from django.template import Library
from django.utils.html import urlize
from django.utils.safestring import mark_safe


register = Library()


def simpletimesince(value, arg=None):
    """Formats a date as the time since that date (i.e. "4 days, 6 hours")."""
    from django.utils.timesince import timesince
    if not value:
        return u''
    try:
        if arg:
            return timesince(value, arg)
        return timesince(value, datetime.datetime.utcnow()).split(', ')[0]
    except (ValueError, TypeError):
        return u''


def sanitize(value, extra_filters=None):
    """
    Sanitize the given HTML.

    Based on code from:
    * http://www.djangosnippets.org/snippets/1655/
    * http://www.djangosnippets.org/snippets/205/
    """
    if value is None:
        return u''

    if '<' not in value and '&#' not in value and \
            re.search(r'&\w+;', value) is None: # no HTML
        # convert plain-text links into HTML
        return mark_safe(urlize(value,
                                nofollow=True,
                                autoescape=True).replace('\n', '<br/>'))

    js_regex = re.compile(r'[\s]*(&#x.{1,7})?'.join(list('javascript')),
                          re.IGNORECASE)
    allowed_tags = ('p i strong em b u a h1 h2 h3 h4 h5 h6 pre br img ul '
                    'ol li span').split()
    allowed_attributes = 'href src style'.split()

    whitelist = False
    extra_tags = ()
    extra_attributes = ()
    if isinstance(extra_filters, basestring):
        if '|' in extra_filters:
            parts = extra_filters.split('|')
        else:
            parts = [extra_filters.split()]
        if parts[0] == 'whitelist':
            whitelist = True
            parts = parts[1:]
        extra_tags = parts[0].split()
        if len(parts) > 1:
            extra_attributes = parts[1].split()
    elif extra_filters:
        extra_tags = extra_filters

    if whitelist:
        allowed_tags, allowed_attributes = extra_tags, extra_attributes
    else:
        allowed_tags = set(allowed_tags) - set(extra_tags)
        allowed_attributes = set(allowed_attributes) - set(extra_attributes)

    soup = BeautifulSoup(value)
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        # remove comments
        comment.extract()

    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.hidden = True
        else:
            tag.attrs = dict((key, js_regex.sub('', val))
                             for key, val in tag.attrs.iteritems()
                             if key in allowed_attributes)

    return mark_safe(unicode(soup))


def wmode_transparent(value):
    doc = lxml.html.fromstring('<div>' + value + '</div>')
    # Find any object tag
    tags = doc.cssselect('object')
    for object_tag in tags:
        WMODE_TRANSPARENT_PARAM = lxml.html.fragment_fromstring("""<param name="wmode" value="transparent"></param>""")
        object_tag.insert(0, WMODE_TRANSPARENT_PARAM)

    # Find any relevant flash embed
    embeds = doc.cssselect('embed')
    for embed in embeds:
        if embed.get('type') == 'application/x-shockwave-flash':
            embed.set('wmode', 'transparent')

    wrapped_in_a_div = lxml.html.tostring(doc)
    if (wrapped_in_a_div.startswith('<div>') and 
        wrapped_in_a_div.endswith('</div>')):
        start = len('<div>')
        end = - len('</div>')
        return mark_safe(wrapped_in_a_div[start:end])
    # else, uh, return the wrapped thing.
    return mark_safe(wrapped_in_a_div)


register.filter(simpletimesince)
register.filter(sanitize)
register.filter(wmode_transparent)
