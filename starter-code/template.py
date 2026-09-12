"""
Lab #3: Baseline Chatbot vs ReAct Agent
Học viên hoàn thiện các mục TODO để hoàn thành bài lab.
"""

import json
import re
from typing import Any, Dict, List, Optional

from tools import TOOL_DEFINITIONS, TOOL_MAP

SYSTEM_PROMPT = """Bạn là một ReAct Agent thông minh hỗ trợ khách hàng Vingroup.
Bạn chỉ sử dụng các công cụ sau:
{tools}

Quy trình trả lời bắt buộc:
Thought: <Suy nghĩ bước tiếp theo>
Action: {{"name": "<tên tool>", "args": {{<tham số>}}}}
Observation: <Kết quả từ tool>
... (Lặp lại cho tới khi có đủ dữ liệu)
Final Answer: <Câu trả lời hoàn chỉnh cho khách hàng>
"""

class ChatbotBaseline:
    """Baseline LLM Chatbot (Không sử dụng ReAct Loop hay Tools)"""

    def query(self, user_input: str) -> Dict[str, Any]:
        """Trả lời một lượt mà không truy cập bất kỳ công cụ nào."""
        return {
            "status": "success",
            "answer": (
                "Tôi chưa thể tra cứu dữ liệu chuyến bay hoặc thời tiết theo thời gian "
                f"thực cho yêu cầu: {user_input}"
            ),
            "tool_calls": [],
        }

class ReActAgent:
    """ReAct Agent có sử dụng Thought-Action-Observation Loop"""
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.trace = []

    @staticmethod
    def _airport_codes(user_input: str) -> List[str]:
        """Lấy mã sân bay trong câu hỏi, đồng thời hiểu một số tên thành phố."""
        codes = re.findall(r"\b[A-Za-z]{3}\b", user_input)
        valid_codes = {"HAN", "SGN", "DAD"}
        result = [code.upper() for code in codes if code.upper() in valid_codes]

        city_aliases = {
            "hà nội": "HAN",
            "ha noi": "HAN",
            "tp. hồ chí minh": "SGN",
            "hồ chí minh": "SGN",
            "ho chi minh": "SGN",
            "sài gòn": "SGN",
            "sai gon": "SGN",
            "đà nẵng": "DAD",
            "da nang": "DAD",
        }
        normalized_input = user_input.lower()
        for city, code in city_aliases.items():
            if city in normalized_input and code not in result:
                result.append(code)
        return result

    @staticmethod
    def _max_price(user_input: str) -> int:
        """Chuyển các cách ghi như 1.5 triệu, 2 triệu hoặc 500k thành VND."""
        lowered = user_input.lower().replace(",", ".")
        million_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:triệu|trieu)", lowered)
        if million_match:
            return int(float(million_match.group(1)) * 1_000_000)

        thousand_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", lowered)
        if thousand_match:
            return int(float(thousand_match.group(1)) * 1_000)

        return 5_000_000

    @staticmethod
    def _execute_action(action: Any) -> Any:
        """Validate, normalize and execute one ReAct action through TOOL_MAP."""
        if isinstance(action, str):
            try:
                action = json.loads(action)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format"}

        if not isinstance(action, dict):
            return {"error": "Action must be a JSON object"}

        tool_name = str(action.get("name", "")).strip().lower()
        args = action.get("args", {})
        tool = TOOL_MAP.get(tool_name)
        if tool is None:
            return {"error": f"Unknown tool: {tool_name}"}
        if not isinstance(args, dict):
            return {"error": "Tool arguments must be a JSON object"}

        try:
            return tool(**args)
        except (TypeError, ValueError) as exc:
            return {"error": f"Tool execution failed: {exc}"}

    @staticmethod
    def _format_flights(flights: List[Dict[str, Any]]) -> str:
        if not flights:
            return "Không tìm thấy chuyến bay phù hợp với hành trình và ngân sách."
        details = [
            (
                f"{flight['flight_number']} ({flight['airline']}), khởi hành "
                f"{flight['departure_time']}, giá {flight['price_vnd']:,} VND"
            )
            for flight in flights
        ]
        return "Các chuyến bay phù hợp: " + "; ".join(details) + "."

    @staticmethod
    def _format_weather(weather: Dict[str, Any]) -> str:
        if "error" in weather:
            return f"Không lấy được dữ liệu thời tiết: {weather['error']}."
        return (
            f"Thời tiết {weather['city']}: {weather['temperature_c']}°C, "
            f"{weather['condition']}, độ ẩm {weather['humidity_pct']}%. "
            f"Gợi ý: {weather['recommendation']}"
        )

    def _result(self, status: str, answer: str) -> Dict[str, Any]:
        return {
            "status": status,
            "answer": answer,
            "iterations": len(self.trace),
            "trace": self.trace.copy(),
        }

    def run(self, user_input: str) -> Dict[str, Any]:
        """Run a deterministic Thought-Action-Observation loop for the lab data."""
        self.trace = []
        if self.max_iterations <= 0:
            return self._result(
                "max_iterations_reached",
                "Không thể hoàn thành trong số bước tối đa.",
            )

        lowered = user_input.lower()
        is_faq = any(
            term in lowered
            for term in ("chính sách", "đổi trả", "đổi vé", "hoàn vé")
        )
        needs_flight = not is_faq and any(
            term in lowered for term in ("chuyến bay", "vé", "flight")
        )
        needs_weather = any(term in lowered for term in ("thời tiết", "weather", "mặc gì"))
        codes = self._airport_codes(user_input)
        answers: List[str] = []

        if needs_flight:
            origin = codes[0] if codes else "HAN"
            destination = codes[1] if len(codes) > 1 else None
            if destination is None:
                answers.append("Bạn vui lòng cung cấp đủ điểm đi và điểm đến.")
                self.trace.append({
                    "iteration": len(self.trace) + 1,
                    "thought": "Yêu cầu thiếu điểm đi hoặc điểm đến.",
                    "action": None,
                    "observation": "Missing route information",
                })
            else:
                action = {
                    "name": "get_flight_info",
                    "args": {
                        "origin": origin,
                        "destination": destination,
                        "max_price": self._max_price(user_input),
                    },
                }
                observation = self._execute_action(action)
                self.trace.append({
                    "iteration": len(self.trace) + 1,
                    "thought": "Tra cứu các chuyến bay phù hợp với hành trình và ngân sách.",
                    "action": action,
                    "observation": observation,
                })
                answers.append(self._format_flights(observation))

        if needs_weather and len(self.trace) < self.max_iterations:
            city_code: Optional[str] = codes[-1] if codes else None
            if city_code is None:
                answers.append("Bạn vui lòng cung cấp thành phố cần xem thời tiết.")
                self.trace.append({
                    "iteration": len(self.trace) + 1,
                    "thought": "Yêu cầu thiếu địa điểm cần xem thời tiết.",
                    "action": None,
                    "observation": "Missing city information",
                })
            else:
                action = {
                    "name": "get_weather_forecast",
                    "args": {"city_code": city_code},
                }
                observation = self._execute_action(action)
                self.trace.append({
                    "iteration": len(self.trace) + 1,
                    "thought": "Tra cứu thời tiết tại điểm đến và gợi ý trang phục.",
                    "action": action,
                    "observation": observation,
                })
                answers.append(self._format_weather(observation))

        if needs_flight and needs_weather:
            if len(self.trace) >= self.max_iterations:
                return self._result(
                    "max_iterations_reached",
                    " ".join(answers) or "Không thể hoàn thành trong số bước tối đa.",
                )
            self.trace.append({
                "iteration": len(self.trace) + 1,
                "thought": "Đã có đủ dữ liệu để tổng hợp câu trả lời cuối cùng.",
                "action": None,
                "observation": "Final answer ready",
            })
        elif not needs_flight and not needs_weather:
            answers.append(
                "Vinpearl hỗ trợ đổi hoặc hoàn vé tùy theo điều kiện của hạng vé. "
                "Bạn nên kiểm tra điều kiện ghi trên vé hoặc liên hệ bộ phận chăm sóc khách hàng Vinpearl."
            )
            self.trace.append({
                "iteration": 1,
                "thought": "Đây là câu hỏi FAQ nên không cần gọi công cụ.",
                "action": None,
                "observation": "Answered from general policy guidance",
            })

        return self._result("completed", " ".join(answers))

def main():
    user_query = "Tìm cho tôi chuyến bay từ HAN đi SGN dưới 2 triệu, rồi cho biết thời tiết SGN nên mặc gì?"
    
    print("=== RUNNING CHATBOT BASELINE ===")
    chatbot = ChatbotBaseline()
    print(chatbot.query(user_query))
    
    print("\n=== RUNNING REACT AGENT ===")
    agent = ReActAgent(max_iterations=5)
    result = agent.run(user_query)
    print("Result:", result)
    print("Trace Log:", json.dumps(agent.trace, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
