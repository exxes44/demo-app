import importlib
import json
import sqlite3
from unittest.mock import Mock

import pytest
import yaml


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "test-only-placeholder")
    return importlib.import_module("insecure_demo")


def test_sql_injection_is_treated_as_a_literal_username(demo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    attack = "' OR 1=1 --"
    conn = sqlite3.connect("app.db")
    try:
        conn.execute("CREATE TABLE users (name TEXT PRIMARY KEY)")
        conn.executemany("INSERT INTO users VALUES (?)", [("alice",), (attack,)])
        conn.commit()
    finally:
        conn.close()
    assert demo.get_user(attack) == [(attack,)]
    assert demo.get_user("alice") == [("alice",)]


@pytest.mark.parametrize("host", ["127.0.0.1; id", "-c", "host\nwhoami", "", "a..b", "::1%bad", None])
def test_ping_rejects_invalid_host_without_starting_a_process(demo, monkeypatch, host):
    run = Mock()
    monkeypatch.setattr(demo.subprocess, "run", run)
    with pytest.raises(ValueError):
        demo.ping(host)
    run.assert_not_called()


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "example.org", "host-name.example."])
def test_ping_passes_valid_host_as_one_argument_without_a_shell(demo, monkeypatch, host):
    run = Mock()
    monkeypatch.setattr(demo.subprocess, "run", run)
    assert demo.ping(host) is run.return_value
    args, kwargs = run.call_args
    assert isinstance(args[0], list)
    assert args[0][-1] == host
    assert kwargs.get("shell", False) is False
    assert 0 < kwargs["timeout"] <= 10


def test_password_hashes_use_unique_salts_and_can_be_reproduced(demo):
    salt, digest = demo.hash_password("correct horse battery staple")
    other_salt, other_digest = demo.hash_password("correct horse battery staple")
    assert len(salt) >= 16
    assert salt != other_salt
    assert digest != other_digest
    assert demo.hash_password("correct horse battery staple", salt) == (salt, digest)
    assert demo.hash_password("a different password", salt)[1] != digest


def test_reset_token_uses_cryptographic_generator(demo, monkeypatch):
    secure_generator = Mock(return_value="opaque-token")
    monkeypatch.setattr(demo.secrets, "token_urlsafe", secure_generator)
    assert demo.make_reset_token() == "opaque-token"
    secure_generator.assert_called_once_with(32)


def test_yaml_rejects_python_object_construction(demo, tmp_path):
    marker = tmp_path / "yaml-created"
    payload = f"!!python/object/apply:pathlib.Path.touch [!!python/object/apply:pathlib.Path ['{marker.as_posix()}']]"
    with pytest.raises(yaml.constructor.ConstructorError):
        demo.load_config(payload)
    assert not marker.exists()
    assert demo.load_config("enabled: true\nretries: 3") == {"enabled": True, "retries": 3}


def test_sessions_accept_json_but_reject_pickle_opcodes(demo):
    assert demo.load_session('{"user": "alice", "roles": ["reader"]}') == {
        "user": "alice", "roles": ["reader"]
    }
    with pytest.raises((json.JSONDecodeError, UnicodeDecodeError)):
        demo.load_session(b"\x80\x04N.")


def test_fetch_keeps_certificate_verification_and_has_a_timeout(demo, monkeypatch):
    get = Mock()
    monkeypatch.setattr(demo.requests, "get", get)
    assert demo.fetch("https://example.org") is get.return_value
    args, kwargs = get.call_args
    assert args == ("https://example.org",)
    assert kwargs.get("verify", True) is True
    assert 0 < kwargs["timeout"] <= 10
