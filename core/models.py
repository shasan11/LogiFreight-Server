from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from actors.models import Customer, BookingAgency, Carrier, CustomsAgent
 
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username=username, email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    class UserType(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        BOOKING_AGENCY = "booking_agency", "Booking Agency"
        CARRIER = "carrier", "Carrier"
        CUSTOMS_AGENT = "customs_agent", "Customs Agent"

    profile = models.ImageField(upload_to="profile-images/", blank=True, null=True)
    user_type = models.CharField(max_length=50, choices=UserType.choices,blank=True, null=True)
    email = models.EmailField(unique=True)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name="user")
    booking_agency = models.OneToOneField(BookingAgency, on_delete=models.CASCADE, null=True, blank=True, related_name="user")
    carrier = models.OneToOneField(Carrier, on_delete=models.CASCADE, null=True, blank=True, related_name="user")
    customs_agent = models.OneToOneField(CustomsAgent, on_delete=models.CASCADE, null=True, blank=True, related_name="user")

    branch = models.ForeignKey(
       "master.Branch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="users",
    )

    objects = CustomUserManager()

    groups = models.ManyToManyField("auth.Group", blank=True, related_name="customuser_groups", related_query_name="customuser")
    user_permissions = models.ManyToManyField("auth.Permission", blank=True, related_name="customuser_permissions", related_query_name="customuser")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"] 
    def clean(self):
        super().clean()
        mapping = {
            self.UserType.CUSTOMER: "customer",
            self.UserType.BOOKING_AGENCY: "booking_agency",
            self.UserType.CARRIER: "carrier",
            self.UserType.CUSTOMS_AGENT: "customs_agent",
        }
        field = mapping.get(self.user_type)
        if not field:
            return
        for f in ("customer", "booking_agency", "carrier", "customs_agent"):
            if f != field:
                setattr(self, f, None)
        if getattr(self, field) is None:
            raise ValueError(f"user_type='{self.user_type}' requires `{field}` to be set.")

    def __str__(self):
        if self.branch:
            return f"{self.username} - {self.branch}"
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username
