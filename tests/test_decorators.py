from django.contrib.auth import models

from promise import Promise, is_thenable

from graphql_jwt import decorators, exceptions
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_token

from .compat import mock
from .testcases import UserTestCase


def info_mock(user):
    return mock.Mock(context=mock.Mock(user=user))


class DecoratorsTests(UserTestCase):

    def test_user_passes_test(self):

        @decorators.user_passes_test(lambda u: u.pk == self.user.pk)
        def wrapped(info):
            """Decorated function"""

        result = wrapped(info_mock(self.user))
        self.assertIsNone(result)

    def test_user_passes_test_permission_denied(self):

        @decorators.user_passes_test(lambda u: u.pk == self.user.pk + 1)
        def wrapped(info):
            """Decorated function"""

        with self.assertRaises(exceptions.PermissionDenied):
            wrapped(info_mock(self.user))

    def test_login_required(self):

        @decorators.login_required
        def wrapped(info):
            """Decorated function"""

        result = wrapped(info_mock(self.user))
        self.assertIsNone(result)

    def test_login_required_permission_denied(self):

        @decorators.login_required
        def wrapped(info):
            """Decorated function"""

        with self.assertRaises(exceptions.PermissionDenied):
            wrapped(info_mock(models.AnonymousUser()))

    def test_staff_member_required(self):

        @decorators.staff_member_required
        def wrapped(info):
            """Decorated function"""

        self.user.is_staff = True
        result = wrapped(info_mock(self.user))

        self.assertIsNone(result)

    def test_staff_member_required_permission_denied(self):

        @decorators.staff_member_required
        def wrapped(info):
            """Decorated function"""

        with self.assertRaises(exceptions.PermissionDenied):
            wrapped(info_mock(self.user))

    def test_permission_required(self):

        @decorators.permission_required('auth.add_user')
        def wrapped(info):
            """Decorated function"""

        perm = models.Permission.objects.get(codename='add_user')
        self.user.user_permissions.add(perm)

        result = wrapped(info_mock(self.user))
        self.assertIsNone(result)

    def test_permission_denied(self):

        @decorators.permission_required(['auth.add_user', 'auth.change_user'])
        def wrapped(info):
            """Decorated function"""

        with self.assertRaises(exceptions.PermissionDenied):
            wrapped(info_mock(self.user))

    def test_token_auth_already_authenticated(self):

        @decorators.token_auth
        def wrapped(cls, root, info, **kwargs):
            return Promise()

        info_mock = mock.MagicMock()
        token = get_token(self.user)

        type(info_mock.context).META = {
            jwt_settings.JWT_AUTH_HEADER: '{0} {1}'.format(
                jwt_settings.JWT_AUTH_HEADER_PREFIX,
                token),
        }

        result = wrapped(
            self,
            None,
            info_mock,
            password='dolphins',
            username=self.user.get_username())

        self.assertTrue(is_thenable(result))
        self.assertNotIn(jwt_settings.JWT_AUTH_HEADER, info_mock.context.META)
