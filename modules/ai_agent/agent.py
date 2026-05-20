"""
Цикл AI-агента: модель → tool calls → исполнение → ответ.
"""
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from models import User, AIChatSession, AIChatMessage
from config import DEFAULT_AI_MODEL
from modules.ai_agent.client import get_ai_client
from modules.ai_agent.tools import TOOLS_SCHEMA, execute_tool


SYSTEM_PROMPT = """Ты — дружелюбный AI-консультант маркетплейса.
Помогаешь пользователю находить товары, отвечаешь на вопросы по каталогу,
можешь добавить товары в корзину и в избранное (если пользователь авторизован).

Правила:
- Используй инструменты для поиска и работы с товарами.
- Если пользователь просит "добавить в корзину" но не авторизован — вежливо сообщи об этом.
- Отвечай на русском языке, кратко и по делу.
- Не выдумывай товары — используй только данные из инструментов.
"""

MAX_TOOL_ITERATIONS = 5


def _load_history(db: Session, session: AIChatSession) -> List[Dict[str, Any]]:
    """Восстановить историю сообщений сессии в формате OpenAI."""
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in session.messages:
        msg: Dict[str, Any] = {"role": m.role}
        if m.content is not None:
            msg["content"] = m.content
        if m.tool_calls:
            msg["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        messages.append(msg)
    return messages


def _save_message(
    db: Session,
    session: AIChatSession,
    role: str,
    content: Optional[str] = None,
    tool_calls: Optional[list] = None,
    tool_call_id: Optional[str] = None,
):
    msg = AIChatMessage(
        session_id=session.id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_or_create_session(
    db: Session, session_id: Optional[int], user: Optional[User]
) -> AIChatSession:
    if session_id:
        session = db.query(AIChatSession).filter(AIChatSession.id == session_id).first()
        if session:
            return session
    session = AIChatSession(user_id=user.id if user else None)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def run_agent(
    db: Session,
    user: Optional[User],
    session: AIChatSession,
    user_message: str,
) -> Dict[str, Any]:
    """
    Запустить цикл агента: добавить сообщение пользователя, получить ответ,
    обработать tool calls и вернуть финальный ответ ассистента.
    """
    client = get_ai_client()

    # сохраняем сообщение пользователя
    _save_message(db, session, role="user", content=user_message)

    messages = _load_history(db, session)

    final_response: Optional[str] = None
    tool_logs: List[Dict[str, Any]] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        completion = client.chat.completions.create(
            model=DEFAULT_AI_MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )

        msg = completion.choices[0].message
        tool_calls = msg.tool_calls or []

        # сериализуем tool_calls для сохранения и для следующего запроса
        serialized_tool_calls = None
        if tool_calls:
            serialized_tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]

        # сохраняем сообщение ассистента (даже если оно с tool_calls, content может быть пустым)
        _save_message(
            db,
            session,
            role="assistant",
            content=msg.content,
            tool_calls=serialized_tool_calls,
        )

        # добавляем в local messages
        assistant_msg: Dict[str, Any] = {"role": "assistant", "content": msg.content}
        if serialized_tool_calls:
            assistant_msg["tool_calls"] = serialized_tool_calls
        messages.append(assistant_msg)

        # если модель не запросила инструмент — это финальный ответ
        if not tool_calls:
            final_response = msg.content or ""
            break

        # выполняем все tool calls
        for tc in tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            result = execute_tool(tool_name, tool_args, db=db, user=user)
            result_str = json.dumps(result, ensure_ascii=False, default=str)

            tool_logs.append({"name": tool_name, "args": tool_args, "result": result})

            _save_message(
                db,
                session,
                role="tool",
                content=result_str,
                tool_call_id=tc.id,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                }
            )

        # цикл продолжается: модель увидит результаты инструментов и сформирует ответ

    if final_response is None:
        final_response = (
            "Извините, не получилось завершить запрос. Попробуйте ещё раз."
        )

    return {
        "session_id": session.id,
        "reply": final_response,
        "tool_calls": tool_logs,
    }
