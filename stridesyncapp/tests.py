from django.test import TestCase, Client
from django.urls import reverse

from .models import User, StepRecord

# Create your tests here.
class BasicAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    # GET on sigup page should return 200
    def test_signup_view(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    # POST to signup should create new user & redirect to login
    def test_user_creation(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        })
        # Check that the user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Check for redirect to login page after signup
        self.assertRedirects(response, reverse('login'))

    # User fails to access home view when not logged in
    def test_home_view_requires_login(self):
        url = reverse('home')
        response = self.client.get(url)
        expected = f"{reverse('login')}?next={url}"
        self.assertRedirects(response, expected)

    # Authenticated POST to manual_step_entry should save new StepRecord
    def test_manual_step_entry(self):
        self.client.login(username='testuser', password='testpassword')
        from datetime import date
        response = self.client.post(reverse('manual_step_entry'), {
            'date': date.today().isoformat(),
            'steps': 1234
        })
        # Check that the StepRecord was created
        self.assertTrue(StepRecord.objects.filter(user=self.user, date=date.today(), steps=1234).exists())
        # Optionally check for redirect or success status
        self.assertIn(response.status_code, [302, 200])

    # Negative step count entries fail due to data validation
    def test_negative_step_validation(self):
        from django.core.exceptions import ValidationError
        from datetime import date
        record = StepRecord (user=self.user, date=date(2025, 7, 15), steps =-1000)

        with self.assertRaises(ValidationError):
            record.full_clean()
        return
    
    # Multiple step count entries for a day is displayed as a total step count
    def test_step_entry_summation(self):
        from datetime import date
        # Create multiple StepRecords for the same day
        StepRecord.objects.create(user=self.user, date=date.today(), steps=1000)
        StepRecord.objects.create(user=self.user, date=date.today(), steps=2000)
        StepRecord.objects.create(user=self.user, date=date.today(), steps=500)
        # Calculate the total steps for today
        total_steps = StepRecord.objects.filter(user=self.user, date=date.today()).aggregate_sum = StepRecord.objects.filter(user=self.user, date=date.today()).aggregate(total_steps_sum=('steps'))['total_steps_sum']
        self.assertEqual(total_steps, 3500)
