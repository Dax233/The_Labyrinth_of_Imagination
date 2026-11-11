"""config.ini 读写往返测试。"""

from __future__ import annotations

import configparser

from labyrinth.config import (
    CONFIG_KEYS,
    CONFIG_SECTION,
    DEFAULT_CONFIG_FILENAME,
    GameConfig,
)


def test_defaults_are_all_off():
    config = GameConfig()
    assert (config.show_position, config.show_direction, config.show_head) == (
        False,
        False,
        False,
    )


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "config.ini"
    original = GameConfig(show_position=True, show_direction=False, show_head=True)
    original.save(path)
    assert path.exists()
    assert GameConfig.load(path) == original


def test_saved_file_keeps_legacy_section_and_keys(tmp_path):
    path = tmp_path / "config.ini"
    GameConfig(show_position=True, show_direction=True, show_head=False).save(path)

    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    assert parser.has_section(CONFIG_SECTION)
    for key in CONFIG_KEYS:
        assert parser.has_option(CONFIG_SECTION, key)
    assert parser.getboolean(CONFIG_SECTION, "show_position") is True
    assert parser.getboolean(CONFIG_SECTION, "show_head") is False


def test_load_accepts_legacy_file(tmp_path):
    """旧版用 configparser 写出来的文件（无 encoding 参数）应该能直接读。"""
    path = tmp_path / "config.ini"
    parser = configparser.ConfigParser()
    parser.add_section("Game Settings")
    parser.set("Game Settings", "show_position", "False")
    parser.set("Game Settings", "show_direction", "True")
    parser.set("Game Settings", "show_head", "False")
    with open(path, "w") as config_file:
        parser.write(config_file)

    assert GameConfig.load(path) == GameConfig(
        show_position=False, show_direction=True, show_head=False
    )


def test_missing_file_returns_defaults(tmp_path):
    path = tmp_path / "not-there.ini"
    assert GameConfig.load(path) == GameConfig()
    assert not path.exists()


def test_load_or_create_writes_default_file(tmp_path):
    path = tmp_path / "config.ini"
    config = GameConfig.load_or_create(path)
    assert config == GameConfig()
    assert path.exists()
    # 第二次读取不会覆盖用户改过的值
    GameConfig(show_position=True).save(path)
    assert GameConfig.load_or_create(path).show_position is True


def test_load_tolerates_missing_keys_and_sections(tmp_path):
    path = tmp_path / "config.ini"
    path.write_text("[Game Settings]\nshow_position = True\n", encoding="utf-8")
    config = GameConfig.load(path)
    assert config.show_position is True
    assert config.show_direction is False
    assert config.show_head is False

    path.write_text("[Other]\nfoo = bar\n", encoding="utf-8")
    assert GameConfig.load(path) == GameConfig()


def test_default_filename_is_config_ini():
    assert DEFAULT_CONFIG_FILENAME == "config.ini"
