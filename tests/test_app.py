import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture providing a TestClient for the FastAPI app."""
    return TestClient(app)


class TestRoot:
    """Tests for the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root path redirects to /static/index.html."""
        # Arrange - no setup needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned."""
        # Arrange - no setup needed

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields."""
        # Arrange - no setup needed

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for name, details in activities.items():
            assert isinstance(name, str)
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_chess_club_exists(self, client):
        """Test that Chess Club is in the activities."""
        # Arrange - no setup needed

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert "Chess Club" in activities

    def test_participants_are_emails(self, client):
        """Test that participants are stored as email strings."""
        # Arrange - no setup needed

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for name, details in activities.items():
            for participant in details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client):
        """Test successful signup for an activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity."""
        # Arrange
        email = "testjoin@mergington.edu"
        activity = "Programming Class"

        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email in activities[activity]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404."""
        # Arrange
        email = "test@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self, client):
        """Test that a student cannot sign up twice for the same activity."""
        # Arrange
        email = "duplicate@mergington.edu"
        activity = "Art Studio"

        # Act
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        response2 = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple students can sign up for the same activity."""
        # Arrange
        email1 = "user1@mergington.edu"
        email2 = "user2@mergington.edu"
        activity = "Drama Club"

        # Act
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_signup_same_student_different_activities(self, client):
        """Test that a student can sign up for multiple different activities."""
        # Arrange
        email = "multi@mergington.edu"
        activity1 = "Debate Team"
        activity2 = "Science Club"

        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""

    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity."""
        # Arrange
        email = "unreg@mergington.edu"
        activity = "Basketball Team"
        client.post(f"/activities/{activity}/signup?email={email}")

        # Act
        response = client.delete(f"/activities/{activity}/participants?email={email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregistering actually removes the participant."""
        # Arrange
        email = "removetest@mergington.edu"
        activity = "Tennis Club"
        client.post(f"/activities/{activity}/signup?email={email}")

        # Act
        client.delete(f"/activities/{activity}/participants?email={email}")
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email not in activities[activity]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404."""
        # Arrange
        email = "test@mergington.edu"
        activity = "Fake Activity"

        # Act
        response = client.delete(f"/activities/{activity}/participants?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_participant_not_found(self, client):
        """Test unregister for participant not in activity returns 404."""
        # Arrange
        email = "notpresent@mergington.edu"
        activity = "Gym Class"

        # Act
        response = client.delete(f"/activities/{activity}/participants?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_unregister_twice_fails(self, client):
        """Test that unregistering twice fails on the second attempt."""
        # Arrange
        email = "twicetemp@mergington.edu"
        activity = "Art Studio"
        client.post(f"/activities/{activity}/signup?email={email}")

        # Act
        response1 = client.delete(f"/activities/{activity}/participants?email={email}")
        response2 = client.delete(f"/activities/{activity}/participants?email={email}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 404
