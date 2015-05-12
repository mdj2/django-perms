from django.test import TestCase

from django.template import Context, Template

from permissions import PermissionsRegistry


class Model:

    pass


# we need a way to see if this function gets called in our unit tests, so we
# use a simple incrementor as a flag
side_effect_counter = 0
def can_do(user):
    global side_effect_counter
    side_effect_counter += 1
    return user is not None


def can_do_with_model(user, instance):
    return None not in (user, instance)


class TestTemplateTags(TestCase):

    def setUp(self):
        self.registry = PermissionsRegistry()
        self.registry.register(can_do)
        self.registry.register(can_do_with_model, model=Model)
        self.template = Template(
            '{% load permissions %}'
            '{% if user|can_do %}can_do{% endif %}'
            '{% if user|can_do_with_model:instance %}can_do_with_model{% endif %}'
        )

        global side_effect_counter
        side_effect_counter = 0

    def test_can_do(self):
        user = Model()
        user.is_authenticated = lambda: True
        context = Context({'user': user, 'instance': None})
        result = self.template.render(context)
        self.assertIn('can_do', result)

    def test_cannot_do(self):
        context = Context({'user': None, 'instance': None})
        result = self.template.render(context)
        self.assertNotIn('can_do', result)

    def test_can_do_with_model(self):
        user = Model()
        user.is_authenticated = lambda: True
        context = Context({'user': user, 'instance': object()})
        result = self.template.render(context)
        self.assertIn('can_do_with_model', result)

    def test_cannot_do_with_model(self):
        context = Context({'user': None, 'instance': object()})
        result = self.template.render(context)
        self.assertNotIn('can_do_with_model', result)

    def test_check_is_short_circuited_for_anonymous_users(self):
        user = Model()
        user.is_authenticated = lambda: False
        context = Context({'user': user, 'instance': object()})
        result = self.template.render(context)

        self.assertEqual(0, side_effect_counter)
        self.assertNotIn('can_do_with_model', result)

    def test_check_is_not_short_circuited_when_allow_anonymous_is_set(self):
        registry = PermissionsRegistry(allow_anonymous=True)
        registry.register(can_do)
        template = Template(
            '{% load permissions %}'
            '{% if user|can_do %}can_do{% endif %}'
        )

        user = Model()
        user.is_authenticated = lambda: False
        context = Context({'user': user, 'instance': object()})
        result = template.render(context)

        self.assertEqual(1, side_effect_counter)
        self.assertNotIn('can_do_with_model', result)
