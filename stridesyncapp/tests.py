from datetime import date, time
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .models import User, StepRecord

# Create your tests here.
class BasicAppTests(TestCase):
    """
    Test suite for basic application functionality including user signup, authentication, step entry, and validation.
    Test Cases:
    - test_signup_view: Ensures the signup page is accessible via GET request.
    - test_user_creation: Verifies that a new user can be created via POST to the signup page and is redirected to login.
    - test_home_view_requires_login: Checks that unauthenticated access to the home page redirects to the login page.
    - test_manual_step_entry: Confirms that a logged-in user can manually enter steps, resulting in a StepRecord creation.
    - test_negative_step_validation: Validates that negative step counts raise a ValidationError.
    - test_step_entry_summation: Ensures that multiple StepRecords for the same user and date are correctly summed.
    """
    def setUp(self):
        """
        Set up test environment by initializing a test client and creating a test user.
        This method is called before each test to ensure a clean state.
        """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_signup_view(self):
        """Tests 'GET on signup page should return 200'."""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_user_creation(self):
        """Tests 'POST on signup page should create a new user and redirect to login'."""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        })
        # Check that the user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Check for redirect to login page after signup
        self.assertRedirects(response, reverse('login'))

    def test_home_view_requires_login(self):
        """Tests 'GET on home page should redirect to login if not authenticated'."""
        url = reverse('home')
        response = self.client.get(url)
        expected = f"{reverse('login')}?next={url}"
        self.assertRedirects(response, expected)

    def test_manual_step_entry(self):
        """Tests 'POST on manual step entry should create a StepRecord'."""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('manual_step_entry'), {
            'date': date.today().isoformat(),
            'step_count': 1234
        })
        # Check that the StepRecord was created
        self.assertTrue(StepRecord.objects.filter(user=self.user, date=date.today(), step_count=1234).exists())
        # Optionally check for redirect or success status
        self.assertIn(response.status_code, [302, 200])

    def test_negative_step_validation(self):
        """Tests 'Negative step count should raise ValidationError'."""
        record = StepRecord(user=self.user, date=date(2025, 7, 15), step_count=-1000)
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_step_entry_summation(self):
        """Tests 'Multiple StepRecords for the same day should sum steps'."""
        # Create multiple StepRecords for the same day
        StepRecord.objects.create(user=self.user, date=date.today(), step_count=1000)
        StepRecord.objects.create(user=self.user, date=date.today(), step_count=2000)
        StepRecord.objects.create(user=self.user, date=date.today(), step_count=500)
        # Calculate the total steps for today
        total_steps = StepRecord.objects.filter(user=self.user, date=date.today()).aggregate(total_steps_sum=Sum('step_count'))['total_steps_sum']
        self.assertEqual(total_steps, 3500)
