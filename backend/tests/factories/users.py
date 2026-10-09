import factory

from src.dto.auth import UserRegisterDTO

TEST_PASSWORD = "TestPass123!@#"


class UserRegisterFactory(factory.Factory):
    class Meta:
        model = UserRegisterDTO

    fullname = factory.Faker("name")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = TEST_PASSWORD
