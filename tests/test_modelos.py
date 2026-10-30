import pytest

from mangavid import images, modelos


def test_plan_has_everything_once():
    steps = modelos.plan([images.DEFAULT_MODEL, modelos.WAI_MODEL, images.DEFAULT_MODEL])
    repos = [r for _, r in steps]
    assert repos == [images.DEFAULT_MODEL, modelos.WAI_MODEL, images.FP16_VAE, images.IP_ADAPTER, "deepghs"]


def test_download_runs_every_step_and_reports_failures(monkeypatch, capsys):
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    calls = []

    def runner(action):
        calls.append(action)
        if len(calls) == 2:
            raise RuntimeError("sin red")

    results = modelos.download([images.DEFAULT_MODEL], runner=runner)
    assert len(calls) == 4
    assert [s for _, _, s in results] == ["ok", "falló: sin red", "ok", "ok"]
    assert "1 descargas fallaron" in capsys.readouterr().out


def test_download_refuses_offline(monkeypatch):
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    with pytest.raises(SystemExit, match="HF_HUB_OFFLINE"):
        modelos.download([images.DEFAULT_MODEL], runner=lambda f: None)
