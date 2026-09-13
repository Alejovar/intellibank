import json
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import auth as auth_module
from app.llm import mcp_client
from app.llm.orchestrator import reset_history, run_turn
from app.llm.tools import TOOL_REGISTRY
from app.models import Account, ConversationTurn, CreditAccount, SessionState, User
from app.routers.actions import execute_action
from app.schemas.chat import ActionExecuteRequest


def _tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _response(*tool_calls, content=None):
    message = SimpleNamespace(content=content, tool_calls=list(tool_calls))
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: next(self._responses))
        )


class BackendHardeningTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.user = User(
            clave_bancaria="test",
            password_hash="hash",
            full_name="Usuario Prueba",
        )
        self.db.add(self.user)
        self.db.flush()
        self.user_id = self.user.id
        self.db.add(Account(
            user_id=self.user_id,
            label="Cuenta principal",
            masked_number="**** 0000",
            balance=12345.67,
        ))
        self.credit = CreditAccount(
            user_id=self.user_id,
            balance=10000,
            credit_limit=20000,
            current_cat=40,
        )
        self.db.add(self.credit)
        self.db.commit()
        self.domain_tool_patcher = patch(
            "app.llm.orchestrator.mcp_client.call_domain_tool",
            side_effect=lambda name, user_id, arguments: TOOL_REGISTRY[name](
                db=self.db,
                user_id=user_id,
                **arguments,
            ),
        )
        self.domain_tool_patcher.start()

    def tearDown(self):
        self.domain_tool_patcher.stop()
        self.db.close()
        self.engine.dispose()
        os.unlink(self.db_path)

    def test_persisted_flow_confirmation_gate_and_restart(self):
        balance_screen = {
            "id": "saldo",
            "title": "Tu saldo",
            "stage_kind": "generated",
            "stage_label": "Saldo",
            "components": [{"id": "balance", "component": "BalanceCard"}],
        }
        balance_client = _FakeClient([
            _response(_tool_call("data-1", "get_balance", {})),
            _response(_tool_call("ui-1", "emit_screen", balance_screen)),
        ])
        with patch("app.llm.orchestrator.get_client", return_value=balance_client):
            result = run_turn(
                self.db, self.user.id, self.user.full_name, [], "cual es mi saldo"
            )
        self.assertEqual(result.payload.id, "saldo")
        state = self.db.get(SessionState, self.user.id)
        self.assertEqual(state.current_stage, "generated")
        self.assertEqual(state.last_screen_payload["id"], "saldo")

        action_args = {
            "credit_account_id": self.credit.id,
            "term_months": 12,
            "cat": 25.0,
            "monthly_payment": 950.0,
        }
        confirmation_screen = {
            "id": "confirmar-plan",
            "title": "Confirma tu plan",
            "stage_kind": "confirmation",
            "stage_label": "Confirmacion",
            "components": [
                {
                    "id": "summary",
                    "component": "ConfirmationSummary",
                    "actions": [
                        {
                            "tool": "functions.apply_credit_plan",
                            "args": action_args,
                            "requires_biometric": True,
                        }
                    ],
                }
            ],
        }
        with patch(
            "app.llm.orchestrator.get_client",
            return_value=_FakeClient([
                _response(_tool_call("ui-2", "emit_screen", confirmation_screen))
            ]),
        ):
            run_turn(self.db, self.user.id, self.user.full_name, [], "continuar")
        self.db.refresh(state)
        self.assertEqual(
            state.pending_action,
            {"screen_id": "confirmar-plan", "tools": ["apply_credit_plan"]},
        )

        result_screen = {
            "id": "plan-aplicado",
            "title": "Plan aplicado",
            "stage_kind": "result",
            "stage_label": "Resultado",
            "components": [{"id": "success", "component": "SuccessScreen"}],
        }
        request = ActionExecuteRequest(
            tool="functions.apply_credit_plan",
            args=action_args,
            screen_id="confirmar-plan",
        )
        with patch(
            "app.llm.orchestrator.get_client",
            return_value=_FakeClient([
                _response(_tool_call("ui-3", "emit_screen", result_screen))
            ]),
        ):
            response = execute_action(request, self.db, self.user)
        self.assertEqual(response.response.payload.id, "plan-aplicado")
        self.db.refresh(self.credit)
        self.assertEqual(self.credit.plan_term_months, 12)
        self.db.refresh(state)
        self.assertEqual(state.current_stage, "result")
        self.assertIsNone(state.pending_action)

        history_count = self.db.query(ConversationTurn).count()
        self.assertGreater(history_count, 0)
        self.db.close()
        self.engine.dispose()
        check_code = """
import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import ConversationTurn, SessionState
db = sessionmaker(bind=create_engine(f'sqlite:///{sys.argv[1]}'))()
state = db.get(SessionState, int(sys.argv[2]))
print(json.dumps({'stage': state.current_stage, 'turns': db.query(ConversationTurn).count()}))
db.close()
"""
        restarted = subprocess.run(
            [sys.executable, "-c", check_code, self.db_path, str(self.user_id)],
            check=True,
            capture_output=True,
            text=True,
        )
        persisted = json.loads(restarted.stdout)
        self.assertEqual(persisted, {"stage": "result", "turns": history_count})
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.db = sessionmaker(bind=self.engine)()

    def test_sensitive_action_without_active_confirmation_is_rejected(self):
        request = ActionExecuteRequest(
            tool="apply_credit_plan",
            args={},
            screen_id="inventada",
        )
        with self.assertRaises(HTTPException) as raised:
            execute_action(request, self.db, self.user)
        self.assertEqual(raised.exception.status_code, 409)

    def test_action_rejects_stale_unoffered_and_unconfirmed_requests(self):
        self.db.add(SessionState(
            user_id=self.user_id,
            current_stage="generated",
            last_screen_id="actual",
            last_screen_payload={
                "id": "actual",
                "stage_kind": "confirmation",
                "components": [{
                    "actions": [{"tool": "functions.apply_credit_plan"}],
                }],
                "footer_actions": [],
            },
        ))
        self.db.commit()

        with self.assertRaises(HTTPException) as stale:
            execute_action(
                ActionExecuteRequest(tool="apply_credit_plan", screen_id="anterior"),
                self.db,
                self.user,
            )
        self.assertEqual(stale.exception.status_code, 409)

        with self.assertRaises(HTTPException) as unoffered:
            execute_action(
                ActionExecuteRequest(tool="confirm_investment", screen_id="actual"),
                self.db,
                self.user,
            )
        self.assertEqual(unoffered.exception.status_code, 403)

        for tool in ("functions.apply_credit_plan", "apply_credit_plan"):
            with self.subTest(tool=tool), self.assertRaises(HTTPException) as unconfirmed:
                execute_action(
                    ActionExecuteRequest(tool=tool, screen_id="actual"),
                    self.db,
                    self.user,
                )
            self.assertEqual(unconfirmed.exception.status_code, 403)

    def test_illegal_llm_stage_transition_returns_fallback(self):
        # "intent" (pedir aclaracion) es un destino valido desde cualquier
        # estado -- lo que la maquina de estados SI bloquea es saltar
        # directo a "confirmation" sin haber pasado antes por una pantalla
        # con datos reales (generated/interaction).
        self.db.add(SessionState(
            user_id=self.user_id,
            current_stage="idle",
            last_screen_id="vigente",
            last_screen_payload={"id": "vigente", "components": []},
        ))
        self.db.commit()
        confirmation_screen = {
            "id": "confirmacion-invalida",
            "title": "Confirma",
            "stage_kind": "confirmation",
            "stage_label": "Confirmacion",
            "components": [{"id": "summary", "component": "ConfirmationSummary"}],
        }
        with patch(
            "app.llm.orchestrator.get_client",
            return_value=_FakeClient([
                _response(_tool_call("ui-invalid", "emit_screen", confirmation_screen))
            ]),
        ):
            response = run_turn(
                self.db, self.user_id, self.user.full_name, [], "otra solicitud"
            )
        self.assertEqual(response.payload.id, "fallback-clarify")
        state = self.db.get(SessionState, self.user_id)
        # El SessionState debe reflejar la pantalla de fallback que SI se le
        # mostro al usuario (evita que quede atascado comparando contra el
        # estado previo a la transicion rechazada).
        self.assertEqual(state.current_stage, "intent")
        self.assertEqual(state.last_screen_id, "fallback-clarify")
        self.assertIsNone(state.pending_action)

    def test_reset_removes_history_and_fsm_state(self):
        self.db.add(ConversationTurn(
            user_id=self.user.id,
            role="user",
            content=json.dumps({"role": "user", "content": "hola"}),
        ))
        self.db.add(SessionState(user_id=self.user.id, current_stage="generated"))
        self.db.commit()
        reset_history(self.db, self.user.id)
        self.assertEqual(self.db.query(ConversationTurn).count(), 0)
        self.assertIsNone(self.db.get(SessionState, self.user.id))

    def test_phone_is_a_unique_login_identifier(self):
        self.user.phone = "5512345678"
        self.user.password_hash = auth_module.hash_pw("password123")
        self.db.commit()

        _, logged_in = auth_module.login("55 1234 5678", "password123", self.db)
        self.assertEqual(logged_in.id, self.user.id)

        with self.assertRaises(HTTPException) as duplicate:
            auth_module.register(
                full_name="Otra Persona",
                email="otra@example.com",
                phone="5512345678",
                password="password123",
                clave_bancaria="123456789012345678",
                card_number=None,
                db=self.db,
            )
        self.assertEqual(duplicate.exception.status_code, 409)


class MCPTransportTest(unittest.TestCase):
    def test_in_memory_transport_executes_domain_tool(self):
        try:
            result = mcp_client.call_domain_tool("get_portfolio", 999999, {})
        finally:
            mcp_client.shutdown()

        self.assertNotIn("error", result)
        self.assertEqual(result["totalValue"], 0)
        self.assertEqual(result["positions"], [])


if __name__ == "__main__":
    unittest.main()
