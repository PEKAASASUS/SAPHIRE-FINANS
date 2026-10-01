import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.session import Session
from app.models.user import User
from app.security.lock_manager import LockManager


def _fake_user() -> User:
    return User(
        id=1, name="Teste",
        password_hash="x", password_salt="x",
        password_algorithm="pbkdf2_sha256",
        password_iterations=1000,
        created_at="2025-01-01", updated_at="2025-01-01",
    )


class TestSession(unittest.TestCase):
    def test_new_session_is_unauthenticated(self):
        s = Session()
        self.assertFalse(s.is_authenticated)

    def test_login_sets_authenticated(self):
        s = Session()
        s.login(_fake_user())
        self.assertTrue(s.is_authenticated)
        self.assertFalse(s.is_locked)

    def test_logout_clears_user(self):
        s = Session()
        s.login(_fake_user())
        s.logout()
        self.assertFalse(s.is_authenticated)
        self.assertIsNone(s.user)

    def test_lock_sets_locked_when_authenticated(self):
        s = Session()
        s.login(_fake_user())
        s.lock()
        self.assertTrue(s.is_locked)
        self.assertTrue(s.is_authenticated)  # Usuário continua logado

    def test_lock_has_no_effect_when_not_authenticated(self):
        s = Session()
        s.lock()
        self.assertFalse(s.is_locked)

    def test_unlock_clears_locked(self):
        s = Session()
        s.login(_fake_user())
        s.lock()
        s.unlock()
        self.assertFalse(s.is_locked)

    def test_touch_resets_activity_timer(self):
        s = Session()
        s.login(_fake_user())
        time.sleep(0.01)
        before = s.seconds_since_last_activity()
        s.touch()
        after = s.seconds_since_last_activity()
        self.assertGreater(before, after)


class TestLockManager(unittest.TestCase):
    def test_does_not_lock_when_unauthenticated(self):
        s = Session()
        lm = LockManager(s, timeout_seconds=1)
        self.assertFalse(lm.should_lock())

    def test_does_not_lock_within_timeout(self):
        s = Session()
        s.login(_fake_user())
        lm = LockManager(s, timeout_seconds=60)
        self.assertFalse(lm.should_lock())

    def test_should_lock_after_timeout_expires(self):
        s = Session()
        s.login(_fake_user())
        lm = LockManager(s, timeout_seconds=1)
        # Simula inatividade: _last_activity foi há muito tempo
        with patch.object(s, "seconds_since_last_activity", return_value=2.0):
            self.assertTrue(lm.should_lock())

    def test_check_and_apply_locks_session(self):
        s = Session()
        s.login(_fake_user())
        lm = LockManager(s, timeout_seconds=1)
        with patch.object(s, "seconds_since_last_activity", return_value=2.0):
            locked = lm.check_and_apply()
        self.assertTrue(locked)
        self.assertTrue(s.is_locked)

    def test_check_and_apply_does_not_relock_already_locked(self):
        s = Session()
        s.login(_fake_user())
        s.lock()
        lm = LockManager(s, timeout_seconds=1)
        with patch.object(s, "seconds_since_last_activity", return_value=999.0):
            locked_again = lm.check_and_apply()
        self.assertFalse(locked_again)  # Já estava bloqueado; não relança.

    def test_set_timeout_updates_threshold(self):
        s = Session()
        s.login(_fake_user())
        lm = LockManager(s, timeout_seconds=60)
        self.assertFalse(lm.should_lock())
        lm.set_timeout(0)  # Timeout zero — bloqueia imediatamente
        self.assertTrue(lm.should_lock())


if __name__ == "__main__":
    unittest.main()
