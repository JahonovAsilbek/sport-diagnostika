import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    phone = factory.Sequence(lambda n: f"+9989{n:07d}")
    # Persists a hashed password so `check_password('password123')` works.
    password = factory.django.Password("password123")
