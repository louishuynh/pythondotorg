from django.core.management import call_command
from django.test import TestCase
from django.template import Template, Context
from django.utils.timezone import now

from boxes.models import Box

from ..templatetags.blogs import get_latest_blog_entries
from ..parser import _render_blog_supernav
from ..models import BlogEntry, Feed, FeedAggregate
from .utils import get_test_rss_path


class BlogTemplateTagTest(TestCase):

    def setUp(self):
        self.test_file_path = get_test_rss_path()
        box = Box.objects.create(label='supernav-python-blog')
        box.content.markup_type = 'html'
        box.save()

    def test_get_latest_entries(self):
        """
        Test our assignment tag, also ends up testing the update_blogs
        management command
        """
        Feed.objects.create(
            id=1, name='psf default', website_url='example.org',
            feed_url=self.test_file_path)
        entries = None
        call_command('update_blogs')
        entries = get_latest_blog_entries()

        self.assertEqual(len(entries), 5)
        self.assertEqual(
            entries[0].pub_date.isoformat(),
            '2013-03-04T15:00:00+00:00'
        )
        b = Box.objects.get(label='supernav-python-blog')
        rendered_box = _render_blog_supernav(BlogEntry.objects.latest())
        self.assertEqual(b.content.raw, rendered_box)

    def test_feed_list(self):
        f1 = Feed.objects.create(
            name='psf blog',
            website_url='psf.example.org',
            feed_url='feed.psf.example.org',
        )
        BlogEntry.objects.create(
            title='test1',
            summary='',
            pub_date=now(),
            url='path/to/foo',
            feed=f1
        )

        f2 = Feed.objects.create(
            name='django blog',
            website_url='django.example.org',
            feed_url='feed.django.example.org',
        )
        BlogEntry.objects.create(
            title='test2',
            summary='',
            pub_date=now(),
            url='path/to/foo',
            feed=f1
        )
        fa = FeedAggregate.objects.create(
            name='test',
            slug='test',
            description='testing',
        )
        fa.feeds.add(f1,f2)


        t = Template("""
        {% load blogs %}
        {% feed_list 'test' as entries %}
        {% for entry in entries %}
        {{ entry.title }}
        {% endfor %}
        """)

        rendered = t.render(Context())
        self.assertEqual(rendered.strip().replace(' ', ''), 'test2\n\ntest1')
