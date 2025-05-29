from unittest.mock import MagicMock, patch, ANY

from app.tests_pre_start import init, logger


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    # Create a mock session that works as a context manager
    session_mock = MagicMock()
    session_mock.__enter__ = MagicMock(return_value=session_mock)
    session_mock.__exit__ = MagicMock(return_value=None)
    session_mock.exec = MagicMock(return_value=True)

    with (
        patch("app.tests_pre_start.Session", return_value=session_mock),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        # Call init and verify no exception is raised
        init(engine_mock)

        # Verify the session was created with the engine
        session_mock.__enter__.assert_called_once()
        
        # Verify the exec method was called once (select(1) creates different instances)
        session_mock.exec.assert_called_once()
