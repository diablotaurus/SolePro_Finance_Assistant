"""
Тесты для точек входа и desktop application bootstrap.
"""
import importlib.machinery
import importlib.util
from pathlib import Path

from solepro.presentation.desktop import application as desktop_app_module


def _load_run_desktop_module():
    project_root = Path(__file__).resolve().parents[2]
    module_path = project_root / "RunDesktopApp.pyw"
    loader = importlib.machinery.SourceFileLoader("run_desktop_app_pyw", str(module_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _build_fake_container_and_sentinels():
    sentinels = {
        "add_tx": object(),
        "upd_tx": object(),
        "del_tx": object(),
        "get_tx": object(),
        "list_tx": object(),
        "search_tx": object(),
        "stats_tx": object(),
        "add_cp": object(),
        "upd_cp": object(),
        "del_cp": object(),
        "list_cp": object(),
        "search_cp": object(),
        "stats_cp": object(),
    }
    fake_container = _SentinelContainerStub(sentinels=sentinels)
    return fake_container, sentinels


def _build_app_with_empty_container():
    return desktop_app_module.DesktopApplication(di_container=_EmptyContainerStub())


class _SessionManagerStub:
    def __init__(self, database_url=None):
        self.database_url = database_url
        self.created = False
        self.closed = False

    def create_tables(self):
        self.created = True

    def close(self):
        self.closed = True


class _SessionContainerStub:
    def __init__(self, session_manager):
        self._session_manager = session_manager

    def session_manager(self):
        return self._session_manager


class _EmptyContainerStub:
    def session_manager(self):
        return _SessionManagerStub()


class _SentinelContainerStub:
    def __init__(self, sentinels):
        self._sentinels = sentinels

    def session_manager(self):
        return _SessionManagerStub()

    def add_transaction_use_case(self):
        return self._sentinels["add_tx"]

    def update_transaction_use_case(self):
        return self._sentinels["upd_tx"]

    def delete_transaction_use_case(self):
        return self._sentinels["del_tx"]

    def get_transaction_use_case(self):
        return self._sentinels["get_tx"]

    def list_transactions_use_case(self):
        return self._sentinels["list_tx"]

    def search_transactions_use_case(self):
        return self._sentinels["search_tx"]

    def get_transaction_statistics_use_case(self):
        return self._sentinels["stats_tx"]

    def add_counterparty_use_case(self):
        return self._sentinels["add_cp"]

    def update_counterparty_use_case(self):
        return self._sentinels["upd_cp"]

    def delete_counterparty_use_case(self):
        return self._sentinels["del_cp"]

    def list_counterparties_use_case(self):
        return self._sentinels["list_cp"]

    def search_counterparties_use_case(self):
        return self._sentinels["search_cp"]

    def get_counterparty_statistics_use_case(self):
        return self._sentinels["stats_cp"]


class _QtAppSpy:
    def __init__(self, exec_result=0):
        self.exec_result = exec_result
        self.app_name = None
        self.org_name = None
        self.org_domain = None
        self.icon = None

    def setApplicationName(self, value):
        self.app_name = value

    def setOrganizationName(self, value):
        self.org_name = value

    def setOrganizationDomain(self, value):
        self.org_domain = value

    def setWindowIcon(self, icon):
        self.icon = icon

    def exec(self):
        return self.exec_result


class _MainWindowSpy:
    def __init__(self):
        self.shown = False
        self.refreshed = False

    def show(self):
        self.shown = True

    def refresh_data(self):
        self.refreshed = True


class _Counter:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1


class _TimerSpy:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class _DbConfigStub:
    def __init__(self, use_migrations):
        self.use_migrations = use_migrations


class _ResolvedPathStub:
    def __init__(self, project_root):
        self.parents = {4: project_root}


def test_rundesktop_main_success(monkeypatch):
    module = _load_run_desktop_module()
    calls = {"prepare": 0, "run": 0}

    monkeypatch.setattr(module, "_prepare_paths", lambda: calls.__setitem__("prepare", calls["prepare"] + 1))
    monkeypatch.setattr(
        module.runpy,
        "run_module",
        lambda *args, **kwargs: calls.__setitem__("run", calls["run"] + 1),
    )

    module.main()

    assert calls["prepare"] == 1
    assert calls["run"] == 1


def test_rundesktop_main_error_shows_dialog(monkeypatch):
    module = _load_run_desktop_module()
    shown = {"message": None}

    monkeypatch.setattr(module, "_prepare_paths", lambda: None)

    def _raise(*args, **kwargs):
        raise RuntimeError("boot-failed")

    monkeypatch.setattr(module.runpy, "run_module", _raise)
    monkeypatch.setattr(module, "_show_error", lambda message: shown.__setitem__("message", message))

    module.main()
    assert shown["message"] is not None
    assert "Не удалось запустить приложение" in shown["message"]
    assert "boot-failed" in shown["message"]


def test_desktop_application_setup_database(monkeypatch):
    session_manager = _SessionManagerStub()
    fake_container = _SessionContainerStub(session_manager)
    app = desktop_app_module.DesktopApplication(di_container=fake_container)

    app.setup_database()

    assert app.session_manager is session_manager
    assert session_manager.created is True


def test_desktop_application_setup_database_migrations_success(monkeypatch):
    session_manager = _SessionManagerStub(database_url="sqlite:///tmp.db")
    fake_container = _SessionContainerStub(session_manager)
    app = desktop_app_module.DesktopApplication(di_container=fake_container)
    calls = {"migrated": 0}

    monkeypatch.setattr(
        desktop_app_module, "get_database_config", lambda: _DbConfigStub(use_migrations=True)
    )
    monkeypatch.setattr(
        desktop_app_module,
        "upgrade_database_to_head",
        lambda database_url: calls.__setitem__("migrated", calls["migrated"] + 1) or True,
    )

    app.setup_database()

    assert calls["migrated"] == 1
    assert session_manager.created is False


def test_desktop_application_setup_database_migrations_fallback(monkeypatch):
    session_manager = _SessionManagerStub(database_url="sqlite:///tmp.db")
    fake_container = _SessionContainerStub(session_manager)
    app = desktop_app_module.DesktopApplication(di_container=fake_container)
    calls = {"migrated": 0}

    monkeypatch.setattr(
        desktop_app_module, "get_database_config", lambda: _DbConfigStub(use_migrations=True)
    )
    monkeypatch.setattr(
        desktop_app_module,
        "upgrade_database_to_head",
        lambda database_url: calls.__setitem__("migrated", calls["migrated"] + 1) or False,
    )

    app.setup_database()

    assert calls["migrated"] == 1
    assert session_manager.created is True


def test_try_run_migrations_skips_when_disabled(monkeypatch):
    app = _build_app_with_empty_container()
    calls = {"migrated": 0}

    monkeypatch.setattr(
        desktop_app_module,
        "upgrade_database_to_head",
        lambda database_url: calls.__setitem__("migrated", calls["migrated"] + 1) or True,
    )

    migrated = app._try_run_migrations(use_migrations=False, database_url="sqlite:///tmp.db")

    assert migrated is False
    assert calls["migrated"] == 0


def test_try_run_migrations_skips_when_no_database_url(monkeypatch):
    app = _build_app_with_empty_container()
    calls = {"migrated": 0}

    monkeypatch.setattr(
        desktop_app_module,
        "upgrade_database_to_head",
        lambda database_url: calls.__setitem__("migrated", calls["migrated"] + 1) or True,
    )

    migrated = app._try_run_migrations(use_migrations=True, database_url=None)

    assert migrated is False
    assert calls["migrated"] == 0


def test_desktop_application_run_success(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    shown = {"value": False}

    def _setup_application():
        window = _MainWindowSpy()
        app.main_window = window
        app.app = _QtAppSpy(exec_result=desktop_app_module.DesktopApplication.EXIT_SUCCESS)
        window.show = lambda: shown.__setitem__("value", True)

    monkeypatch.setattr(app, "setup_database", lambda: None)
    monkeypatch.setattr(app, "setup_application", _setup_application)

    assert app.run() == desktop_app_module.DesktopApplication.EXIT_SUCCESS
    assert shown["value"] is True


def test_desktop_application_setup_application_uses_builders(monkeypatch):
    app = _build_app_with_empty_container()
    fake_qapp = _QtAppSpy()
    fake_qapp.setApplicationName = lambda value: setattr(app, "_app_name", value)
    fake_qapp.setOrganizationName = lambda value: setattr(app, "_org_name", value)
    fake_qapp.setOrganizationDomain = lambda value: setattr(app, "_org_domain", value)
    fake_controller = object()
    fake_window = object()

    monkeypatch.setattr(app, "_build_qt_application", lambda: fake_qapp)
    monkeypatch.setattr(app, "_apply_app_icon", lambda: setattr(app, "_icon_applied", True))
    monkeypatch.setattr(app, "create_controller", lambda: fake_controller)
    monkeypatch.setattr(app, "_build_main_window", lambda controller: fake_window)
    monkeypatch.setattr(desktop_app_module, "apply_style", lambda qapp: setattr(app, "_styled", qapp))

    app.setup_application()

    assert app.app is fake_qapp
    assert app.controller is fake_controller
    assert app.main_window is fake_window
    assert app._styled is fake_qapp
    assert app._app_name == desktop_app_module.DesktopApplication.APP_NAME
    assert app._org_name == desktop_app_module.DesktopApplication.ORG_NAME
    assert app._org_domain == desktop_app_module.DesktopApplication.ORG_DOMAIN
    assert app._icon_applied is True


def test_desktop_application_setup_application_calls_metadata_configurer(monkeypatch):
    app = _build_app_with_empty_container()
    fake_qapp = _QtAppSpy()
    fake_controller = object()
    fake_window = object()
    calls = {"configured": 0}

    monkeypatch.setattr(app, "_build_qt_application", lambda: fake_qapp)
    monkeypatch.setattr(
        app,
        "_configure_application_metadata",
        lambda qapp: calls.__setitem__("configured", calls["configured"] + 1),
    )
    monkeypatch.setattr(app, "_apply_app_icon", lambda: None)
    monkeypatch.setattr(app, "create_controller", lambda: fake_controller)
    monkeypatch.setattr(app, "_build_main_window", lambda controller: fake_window)
    monkeypatch.setattr(desktop_app_module, "apply_style", lambda qapp: None)

    app.setup_application()

    assert calls["configured"] == 1


def test_desktop_application_run_error(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    monkeypatch.setattr(app, "setup_database", lambda: (_ for _ in ()).throw(RuntimeError("db-down")))

    assert app.run() == desktop_app_module.DesktopApplication.EXIT_FAILURE


def test_desktop_application_run_error_uses_handler(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    captured = {"error": None}

    monkeypatch.setattr(app, "setup_database", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(
        app,
        "_handle_run_error",
        lambda error: captured.__setitem__("error", error) or 77,
    )

    result = app.run()

    assert result == 77
    assert isinstance(captured["error"], RuntimeError)
    assert str(captured["error"]) == "boom"


def test_desktop_application_handle_run_error_logs_and_returns_code(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    captured = {"message": None}

    monkeypatch.setattr(app, "_log", lambda message: captured.__setitem__("message", message))

    code = app._handle_run_error(RuntimeError("x"))

    assert code == desktop_app_module.DesktopApplication.EXIT_FAILURE
    assert captured["message"] == f"{desktop_app_module.DesktopApplication.RUN_ERROR_PREFIX}: x"


def test_desktop_application_uses_injected_log_writer():
    captured = {"message": None}
    app = desktop_app_module.DesktopApplication(
        di_container=_EmptyContainerStub(),
        log_writer=lambda message: captured.__setitem__("message", message),
    )

    app._log("hello")

    assert captured["message"] == "hello"


def test_desktop_application_handle_run_error_calls_traceback_printer(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    calls = {"traceback": 0}

    monkeypatch.setattr(app, "_log", lambda message: None)
    monkeypatch.setattr(
        app,
        "_print_traceback",
        lambda: calls.__setitem__("traceback", calls["traceback"] + 1),
    )

    code = app._handle_run_error(RuntimeError("oops"))

    assert code == desktop_app_module.DesktopApplication.EXIT_FAILURE
    assert calls["traceback"] == 1


def test_desktop_application_create_controller_uses_builders(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    tx_coordinator = object()
    cp_coordinator = object()
    export_service = object()

    monkeypatch.setattr(app, "_build_transaction_coordinator", lambda: tx_coordinator)
    monkeypatch.setattr(app, "_build_counterparty_coordinator", lambda: cp_coordinator)
    monkeypatch.setattr(app, "_build_transaction_export_service", lambda: export_service)

    controller = app.create_controller()

    assert controller.transaction_coordinator is tx_coordinator
    assert controller.counterparty_coordinator is cp_coordinator
    assert controller.transaction_export_service is export_service


def test_desktop_application_builders_use_injected_container():
    fake_container, sentinels = _build_fake_container_and_sentinels()
    app = desktop_app_module.DesktopApplication(di_container=fake_container)

    tx_coordinator = app._build_transaction_coordinator()
    cp_coordinator = app._build_counterparty_coordinator()

    assert tx_coordinator.add_transaction_use_case is sentinels["add_tx"]
    assert tx_coordinator.search_transactions_use_case is sentinels["search_tx"]
    assert cp_coordinator.add_counterparty_use_case is sentinels["add_cp"]
    assert cp_coordinator.get_counterparty_statistics_use_case is sentinels["stats_cp"]


def test_desktop_application_create_controller_uses_injected_container():
    fake_container, sentinels = _build_fake_container_and_sentinels()
    app = desktop_app_module.DesktopApplication(di_container=fake_container)

    controller = app.create_controller()

    assert controller.transaction_coordinator.add_transaction_use_case is sentinels["add_tx"]
    assert controller.transaction_coordinator.get_transaction_statistics_use_case is sentinels["stats_tx"]
    assert controller.counterparty_coordinator.add_counterparty_use_case is sentinels["add_cp"]
    assert controller.counterparty_coordinator.get_counterparty_statistics_use_case is sentinels["stats_cp"]
    assert hasattr(controller.transaction_export_service, "export_to_excel")


def test_apply_app_icon_uses_first_existing_candidate(monkeypatch, tmp_path):
    app = desktop_app_module.DesktopApplication()
    first = tmp_path / "solepro.ico"
    second = tmp_path / "solepro.png"
    second.write_text("x", encoding="utf-8")
    captured = {"icon": None}
    qapp = _QtAppSpy()
    qapp.setWindowIcon = lambda icon: captured.__setitem__("icon", icon)
    app.app = qapp

    monkeypatch.setattr(app, "_iter_icon_candidates", lambda: [first, second])
    monkeypatch.setattr(desktop_app_module, "QIcon", lambda path: ("icon", path))

    app._apply_app_icon()

    assert captured["icon"] == ("icon", str(second))


def test_apply_app_icon_skips_when_no_candidates_exist(monkeypatch, tmp_path):
    app = desktop_app_module.DesktopApplication()
    missing = tmp_path / "missing.ico"
    calls = _Counter()
    qapp = _QtAppSpy()
    qapp.setWindowIcon = lambda icon: calls.inc()
    app.app = qapp

    monkeypatch.setattr(app, "_iter_icon_candidates", lambda: [missing])
    monkeypatch.setattr(desktop_app_module, "QIcon", lambda path: ("icon", path))

    app._apply_app_icon()

    assert calls.value == 0


def test_iter_icon_candidates_uses_declared_order(monkeypatch):
    app = desktop_app_module.DesktopApplication()
    project_root = Path("C:/tmp/project")

    monkeypatch.setattr(
        desktop_app_module.Path,
        "resolve",
        lambda self: _ResolvedPathStub(project_root),
    )

    candidates = app._iter_icon_candidates()

    assert [path.name for path in candidates] == list(desktop_app_module.DesktopApplication.ICON_FILENAMES)
    assert all(str(path).startswith(str(project_root / "icons")) for path in candidates)


def test_desktop_application_cleanup_and_refresh():
    app = desktop_app_module.DesktopApplication()
    session_manager = _SessionManagerStub()
    timer = _TimerSpy()
    window = _MainWindowSpy()
    app.session_manager = session_manager
    app.refresh_timer = timer
    app.main_window = window

    app.refresh_data()
    assert window.refreshed is True

    app.cleanup()
    assert session_manager.closed is True
    assert timer.stopped is True
