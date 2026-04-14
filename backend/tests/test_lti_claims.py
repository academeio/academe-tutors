"""Tests for LTI claim extraction and role mapping."""
import pytest

from app.lti.claims import extract_lti_claims, map_lti_role


class TestMapLtiRole:
    def test_instructor_maps_to_faculty(self):
        roles = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"]
        assert map_lti_role(roles) == "faculty"

    def test_learner_maps_to_student(self):
        roles = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"]
        assert map_lti_role(roles) == "student"

    def test_admin_maps_to_admin(self):
        roles = [
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
        ]
        assert map_lti_role(roles) == "admin"

    def test_multiple_roles_highest_wins(self):
        roles = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
        ]
        assert map_lti_role(roles) == "faculty"

    def test_unknown_role_defaults_to_student(self):
        roles = ["http://purl.imsglobal.org/vocab/lis/v2/membership#ContentDeveloper"]
        assert map_lti_role(roles) == "student"

    def test_empty_roles_defaults_to_student(self):
        assert map_lti_role([]) == "student"


class TestExtractLtiClaims:
    def test_extracts_standard_claims(self):
        token_payload = {
            "sub": "user-123",
            "name": "Test Student",
            "email": "test@mgmcri.ac.in",
            "https://purl.imsglobal.org/spec/lti/claim/roles": [
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
            ],
            "https://purl.imsglobal.org/spec/lti/claim/context": {
                "id": "834",
                "label": "AN-MBBS1",
                "title": "Anatomy MBBS Phase 1",
            },
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
                "id": "link-456",
                "title": "Academe Tutor",
            },
        }
        claims = extract_lti_claims(token_payload)
        assert claims.lti_user_id == "user-123"
        assert claims.user_name == "Test Student"
        assert claims.user_email == "test@mgmcri.ac.in"
        assert claims.role == "student"
        assert claims.course_id == "834"
        assert claims.course_title == "Anatomy MBBS Phase 1"
        assert claims.resource_link_id == "link-456"

    def test_handles_missing_optional_claims(self):
        token_payload = {
            "sub": "user-789",
            "https://purl.imsglobal.org/spec/lti/claim/roles": [],
        }
        claims = extract_lti_claims(token_payload)
        assert claims.lti_user_id == "user-789"
        assert claims.user_name is None
        assert claims.user_email is None
        assert claims.role == "student"
        assert claims.course_id is None
